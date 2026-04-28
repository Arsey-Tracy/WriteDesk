
"""
WritDesk – Flask web application.
Provides a REST API consumed by the single-page HTML/JS frontend.
AI calls are proxied through this server so the API key is never
exposed to the browser and there are no CORS issues.
"""
import os
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template
from agent import root_agent
import asyncio
from tools import count_words, reading_time, readability, save_draft, save_docx



app = Flask(__name__)
DRAFTS_DIR = Path("drafts")
DRAFTS_DIR.mkdir(exist_ok=True)



# ── helpers ──────────────────────────────────────────────────────────────────

def _stats(text: str) -> dict:
    words     = len(text.split())
    chars     = len(text)
    sentences = max(1, len(re.split(r'[.!?]+', text.strip())))
    minutes   = max(1, round(words / 200))
    return {"words": words, "chars": chars, "sentences": sentences, "reading_minutes": minutes}

async def run_agent(full_prompt: str) -> str:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name="write_desk",
        session_id="session",
        user_id="user"
    )

    runner = Runner(
        agent=root_agent,
        app_name="write_desk",
        session_service=session_service,
    )

    final_text = ""

    async for event in runner.run_async(
        user_id="user",
        session_id="session",
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=full_prompt)]
        )
    ):
        print("EVENT:", event)
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text

    return final_text or "No response from agent"

# ── routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats", methods=["POST"])
def api_stats():
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"words": 0, "chars": 0, "sentences": 0, "reading_minutes": 0})
    return jsonify(_stats(text))


@app.route("/api/readability", methods=["POST"])
def api_readability():
    data   = request.get_json(force=True)
    text   = data.get("text", "")
    result = readability(text)
    return jsonify({"result": result})


@app.route("/api/save/draft", methods=["POST"])
def api_save_draft():
    data     = request.get_json(force=True)
    content  = data.get("content", "")
    filename = data.get("filename", "draft")
    if not content.strip():
        return jsonify({"error": "No content provided"}), 400
    result = save_draft(content, filename)
    return jsonify({"message": result})


@app.route("/api/save/docx", methods=["POST"])
def api_save_docx():
    data     = request.get_json(force=True)
    content  = data.get("content", "")
    filename = data.get("filename", "document")
    title    = data.get("title", "Document")
    if not content.strip():
        return jsonify({"error": "No content provided"}), 400
    result = save_docx(content, filename, title)
    if "DOCX saved to" in result:
        path = result.replace("DOCX saved to ", "").strip()
        return jsonify({"message": result, "path": path, "filename": Path(path).name})
    return jsonify({"error": result}), 500


@app.route("/api/download/<filename>")
def api_download(filename):
    """Serve a file from the drafts/ folder as a download."""
    safe_path = DRAFTS_DIR / filename
    if not safe_path.exists() or not safe_path.is_file():
        return jsonify({"error": "File not found"}), 404
    return send_file(str(safe_path), as_attachment=True, download_name=filename)


@app.route("/api/drafts", methods=["GET"])
def api_list_drafts():
    files = []
    for f in sorted(DRAFTS_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if f.suffix in (".md", ".docx"):
            files.append({
                "name":     f.name,
                "ext":      f.suffix.lstrip("."),
                "size":     f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%b %d, %Y %H:%M"),
            })
    return jsonify(files)


@app.route("/api/ai", methods=["POST"])
def api_ai():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    context = data.get("context", "").strip()

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    full_prompt = f"{prompt}\n\nContext:\n{context}" if context else prompt

    try:
        result_text = asyncio.run(run_agent(full_prompt))
        return jsonify({"result": result_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Load .env if python-dotenv is available
    import shutil
    if not shutil.which("node"):
        raise RuntimeError("Node.js is required for DOCX Export but not found. Please install Node.js and try again.")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    app.run(debug=True, port=5000)