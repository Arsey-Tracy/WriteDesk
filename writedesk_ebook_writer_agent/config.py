from dataclasses import dataclass


@dataclass
class WriteDeskConfig:
    """
    Configuration for research-relate models and parameters.
    
    Attributes:
    smart_model (str): The model to use for smart tasks (i.e brainstorming book ideas and generating content if required).
    regular_model (str): The model to use for regular tasks.
    max_search_interations (int): The maximum number of search iterations.
    """
    smart_model: str = "gemini-2.5-pro"
    regular_model: str = "gemini-2.5-flash"
    max_search_interations: int = 3


config = WriteDeskConfig()