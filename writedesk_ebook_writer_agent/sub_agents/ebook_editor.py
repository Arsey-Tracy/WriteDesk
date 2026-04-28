
from google.adk.agents import Agent

ebook_editing_agent = Agent(
    name="ebook_editor",
    description="Editing agent for ebook content.",
    instruction="""
    You are an editing assistant for an ebook about the history of AI.
    Your task is to improve the clarity, coherence, and overall quality of the content.
    The final output should be a revised ebook content in Markdown format.
    """,
)

ebook_editor = ebook_editing_agent