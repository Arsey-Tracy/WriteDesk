from google.adk.agents import Agent

ebook_planning_agent = Agent(
    name="ebook_planner",
    description="Planning agent for ebook content.",
    instruction="""
    You are a planning assistant for an ebook about the user topic or idea.
    Your task is to organize and structure the content for the ebook.
    """,
)
ebook_planner = ebook_planning_agent