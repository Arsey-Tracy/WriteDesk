import os
from datetime import datetime
from textstat import textstat


def count_words(text: str) -> str:
    words = len(text.split())
    return f"Word count: {words}"

def reading_time(text: str) -> str:
    words = len(text.split())
    minutes = max(1, round(words / 200))
    return f"Estimated reaing time: {minutes} min (for {words} words)"

def readability(text: str) -> str:
    ease = textstat.flesch_reading_ease(text)
    grade = textstat.flesch_kincaid_grade(text)
    return (
        f"Flesch Reading Ease: {ease:.1f} (higher = easier, 60-70 is good for general audience)\n"
        f"Flesch-Kincaid Grade Level: {grade:.1f} (aim for grade 7-8 for broad audiences)"
    )

def save_draft(content: str, filename: str = "draft") -> str:
    """
    Save a Markdown draft to the drafts/ folder.
    Provide a suggested filename (without extension) as the second argument.
    """
    os.makedirs("drafts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{filename}_{timestamp}.md"
    path = os.path.join("drafts", safe_name)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Draft saved to {path}"
