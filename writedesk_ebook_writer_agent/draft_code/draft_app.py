import asyncio
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from google.adk.runners import Runner
from agent import root_agent


async def main():
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name="app",
        session_id="session", 
        user_id="user"
    )
    runner = Runner(
            agent=root_agent,
            app_name="app",
            session_service=session_service, 
        )
    query = "Can you help me outline an ebook about the history of AI?"
    async for event in runner.run_async(
        user_id="user",
        session_id="session",
        new_message=genai_types.Content(
            role="user", parts=[genai_types.Part.from_text(text=query)]
        )
    ):
        if (event.is_final_response() and event.content and event.content.parts):
            print("Agent response:", event.content.parts[0].text)
if __name__ == "__main__":
    asyncio.run(main())