from google.adk.agents import Agent
from google.adk.tools import google_search

fact_checking_agent = Agent(
    name="ebook_fact_checker",
    description="An agent that checks facts for the ebook content.",
    instruction="""
    You are a fact-checking assistant for an ebook about the user topic.
    Your task is to verify the accuracy of statements and information related to the user content.
    """,
    tools=[google_search]
)
fact_checker = fact_checking_agent