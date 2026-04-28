from google.adk.agents import Agent

image_generator = Agent(
    name="image_generator",
    description="Image generation agent for ebook content.",
    instruction="""
    You are an image generation assistant for an ebook about the user's topic.
    Your task is to create relevant and high-quality images to accompany the content.
    """
)