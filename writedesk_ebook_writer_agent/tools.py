import os
import re
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from textstat import textstat
except ImportError:
    textstat = None

# Base directory: wherever tools.py lives — works on any machine
BASE_DIR = Path(__file__).parent.resolve()
DRAFTS_DIR = BASE_DIR / "drafts"


def count_words(text: str) -> str:
    """Count words in the given text."""
    words = len(text.split())
    chars = len(text)
    sentences = max(1, len(re.split(r'[.!?]+', text)))
    return json.dumps({
        "words": words,
        "characters": chars,
        "sentences": sentences,
        "message": f"Word count: {words} | Characters: {chars} | Sentences: {sentences}"
    })


def reading_time(text: str) -> str:
    """Estimate reading time for the given text."""
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"Estimated reading time: {minutes} min (for {words} words at 200 wpm)"


def readability(text: str) -> str:
    """Calculate readability scores for the given text."""
    if textstat is None:
        return "Readability analysis unavailable (textstat not installed)"
    ease = textstat.flesch_reading_ease(text)
    grade = textstat.flesch_kincaid_grade(text)
    return (
        f"Flesch Reading Ease: {ease:.1f} (higher = easier; 60–70 is good for general audience)\n"
        f"Flesch-Kincaid Grade Level: {grade:.1f} (aim for grade 7–8 for broad audiences)"
    )


def save_draft(content: str, filename: str = "draft") -> str:
    """
    Save a Markdown draft to the drafts/ folder.
    Args:
        content: The text content to save (Markdown format preferred).
        filename: Suggested filename (without extension).
    Returns:
        Path to the saved draft.
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{filename}_{timestamp}.md"
    path = DRAFTS_DIR / safe_name
    path.write_text(content, encoding="utf-8")
    return f"Draft saved to {path}"


def save_docx(content: str, filename: str = "document", title: str = "Document") -> str:
    """
    Convert Markdown content to a well-formatted .docx file.
    Parses headings, paragraphs, bullet lists, and numbered lists.
    Args:
        content: Markdown-formatted text.
        filename: Output filename (without extension).
        title: Document title shown as the first H1 if not present.
    Returns:
        Path to the saved .docx file, or error message.
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{filename}_{timestamp}.docx"
    # Use absolute path so Node writes to the right place regardless of cwd
    out_path = str((DRAFTS_DIR / safe_name).resolve())

    node_script = _build_node_script(content, title, out_path)
    script_path = os.path.join(tempfile.gettempdir(), f"gen_docx_{timestamp}.js")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(node_script)

    # Determine NODE_PATH so `require('docx')` resolves whether the package is
    # installed locally (next to this file) or globally.
    local_node_modules = str(BASE_DIR / "node_modules")
    # Try to find the global node_modules via `npm root -g`
    try:
        global_node_modules = subprocess.check_output(
            ["npm", "root", "-g"], text=True, timeout=10
        ).strip()
    except Exception:
        global_node_modules = ""

    node_path_parts = [p for p in [local_node_modules, global_node_modules] if p]
    node_path_env = os.pathsep.join(node_path_parts)

    env = os.environ.copy()
    if node_path_env:
        existing = env.get("NODE_PATH", "")
        env["NODE_PATH"] = (node_path_env + os.pathsep + existing).rstrip(os.pathsep)

    try:
        result = subprocess.run(
            ["node", script_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(BASE_DIR),   # run from the project root (portable)
            env=env,
        )
        if result.returncode == 0:
            return f"DOCX saved to {out_path}"
        else:
          return f"DOCX generation failed: {result.stderr}"
    except Exception as e:
        return f"DOCX generation error: {str(e)}"
    finally:
        if os.path.exists(script_path):
            os.remove(script_path)


def _build_node_script(content: str, title: str, out_path: str) -> str:
    """Build a Node.js script that generates the DOCX using the docx library."""
    content_escaped = json.dumps(content)
    title_escaped = json.dumps(title)
    out_path_escaped = json.dumps(out_path)

    return f"""
const fs = require('fs');
const {{ Document, Packer, Paragraph, TextRun, HeadingLevel,
         AlignmentType, LevelFormat, PageNumber, Footer, Header,
         BorderStyle }} = require('docx');

const content = {content_escaped};
const title = {title_escaped};
const outPath = {out_path_escaped};

// Parse markdown into document children
function parseMarkdown(md) {{
  const lines = md.split('\\n');
  const children = [];
  let bulletItems = [];
  let numberedItems = [];
  let bulletCounter = 0;
  let numberedCounter = 0;

  function flushBullets() {{
    if (bulletItems.length > 0) {{
      bulletCounter++;
      for (const item of bulletItems) {{
        children.push(new Paragraph({{
          numbering: {{ reference: `bullets-${{bulletCounter}}`, level: 0 }},
          children: [new TextRun({{ text: item, size: 24, font: 'Georgia' }})]
        }}));
      }}
      bulletItems = [];
    }}
  }}

  function flushNumbered() {{
    if (numberedItems.length > 0) {{
      numberedCounter++;
      for (const item of numberedItems) {{
        children.push(new Paragraph({{
          numbering: {{ reference: `numbers-${{numberedCounter}}`, level: 0 }},
          children: [new TextRun({{ text: item, size: 24, font: 'Georgia' }})]
        }}));
      }}
      numberedItems = [];
    }}
  }}

  for (let i = 0; i < lines.length; i++) {{
    const line = lines[i];

    if (/^# /.test(line)) {{
      flushBullets(); flushNumbered();
      children.push(new Paragraph({{
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun({{ text: line.slice(2).trim(), bold: true, font: 'Playfair Display', size: 40 }})]
      }}));
    }} else if (/^## /.test(line)) {{
      flushBullets(); flushNumbered();
      children.push(new Paragraph({{
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({{ text: line.slice(3).trim(), bold: true, font: 'Playfair Display', size: 32 }})]
      }}));
    }} else if (/^### /.test(line)) {{
      flushBullets(); flushNumbered();
      children.push(new Paragraph({{
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun({{ text: line.slice(4).trim(), bold: true, font: 'Georgia', size: 28 }})]
      }}));
    }} else if (/^(\\*|-) /.test(line)) {{
      flushNumbered();
      bulletItems.push(line.replace(/^[*\\-] /, '').trim());
    }} else if (/^\\d+\\. /.test(line)) {{
      flushBullets();
      numberedItems.push(line.replace(/^\\d+\\.\\s*/, '').trim());
    }} else if (line.trim() === '') {{
      flushBullets(); flushNumbered();
      children.push(new Paragraph({{ children: [new TextRun('')] }}));
    }} else {{
      flushBullets(); flushNumbered();
      const parts = line.split(/(\\*\\*[^*]+\\*\\*|\\*[^*]+\\*)/);
      const runs = parts.map(part => {{
        if (/^\\*\\*/.test(part)) {{
          return new TextRun({{ text: part.replace(/\\*\\*/g, ''), bold: true, size: 24, font: 'Georgia' }});
        }} else if (/^\\*/.test(part)) {{
          return new TextRun({{ text: part.replace(/\\*/g, ''), italics: true, size: 24, font: 'Georgia' }});
        }}
        return new TextRun({{ text: part, size: 24, font: 'Georgia' }});
      }});
      children.push(new Paragraph({{ children: runs, spacing: {{ after: 120 }} }}));
    }}
  }}

  flushBullets();
  flushNumbered();
  return {{ children, bulletCount: bulletCounter, numberedCount: numberedCounter }};
}}

const {{ children, bulletCount, numberedCount }} = parseMarkdown(content);

const numberingConfig = [];
for (let i = 1; i <= bulletCount; i++) {{
  numberingConfig.push({{
    reference: `bullets-${{i}}`,
    levels: [{{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
      style: {{ paragraph: {{ indent: {{ left: 720, hanging: 360 }}, spacing: {{ after: 80 }} }},
               run: {{ font: 'Georgia', size: 24 }} }} }}]
  }});
}}
for (let i = 1; i <= numberedCount; i++) {{
  numberingConfig.push({{
    reference: `numbers-${{i}}`,
    levels: [{{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
      style: {{ paragraph: {{ indent: {{ left: 720, hanging: 360 }}, spacing: {{ after: 80 }} }},
               run: {{ font: 'Georgia', size: 24 }} }} }}]
  }});
}}

const doc = new Document({{
  numbering: {{ config: numberingConfig }},
  styles: {{
    default: {{ document: {{ run: {{ font: 'Georgia', size: 24 }} }} }},
    paragraphStyles: [
      {{ id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: {{ size: 40, bold: true, font: 'Playfair Display', color: '1a1a2e' }},
        paragraph: {{ spacing: {{ before: 360, after: 240 }}, outlineLevel: 0,
          border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 4, color: '4a90d9', space: 6 }} }} }} }},
      {{ id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: {{ size: 32, bold: true, font: 'Playfair Display', color: '2c3e6b' }},
        paragraph: {{ spacing: {{ before: 280, after: 160 }}, outlineLevel: 1 }} }},
      {{ id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: {{ size: 28, bold: true, font: 'Georgia', color: '34495e' }},
        paragraph: {{ spacing: {{ before: 200, after: 120 }}, outlineLevel: 2 }} }},
    ]
  }},
  sections: [{{
    properties: {{
      page: {{
        size: {{ width: 12240, height: 15840 }},
        margin: {{ top: 1440, right: 1440, bottom: 1440, left: 1440 }}
      }}
    }},
    headers: {{
      default: new Header({{
        children: [new Paragraph({{
          children: [new TextRun({{ text: title, font: 'Georgia', size: 18, color: '888888', italics: true }})],
          border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 2, color: 'cccccc', space: 4 }} }}
        }})]
      }})
    }},
    footers: {{
      default: new Footer({{
        children: [new Paragraph({{
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({{ text: 'Page ', font: 'Georgia', size: 18, color: '888888' }}),
            new TextRun({{ children: [PageNumber.CURRENT], font: 'Georgia', size: 18, color: '888888' }}),
            new TextRun({{ text: ' of ', font: 'Georgia', size: 18, color: '888888' }}),
            new TextRun({{ children: [PageNumber.TOTAL_PAGES], font: 'Georgia', size: 18, color: '888888' }}),
          ],
          border: {{ top: {{ style: BorderStyle.SINGLE, size: 2, color: 'cccccc', space: 4 }} }}
        }})]
      }})
    }},
    children
  }}]
}});

Packer.toBuffer(doc).then(buf => {{
  fs.writeFileSync(outPath, buf);
  console.log('OK: ' + outPath);
}}).catch(e => {{ console.error(e); process.exit(1); }});
"""