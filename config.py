import os
import logging
from google.api_core import retry
from google.genai import types

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class Config:
    # --- CONFIGURATION ---
    # Ensure GOOGLE_API_KEY is set in your environment variables
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    LOCATION = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    # Using a model capable of complex reasoning
    MODEL_NAME = "gemini-1.5-pro-002" 
    
    # --- RETRY POLICY ---
    # Robustness for long generation tasks
    RETRY_POLICY = retry.Retry(
        initial=1.0,
        maximum=60.0,
        multiplier=2.0,
        deadline=120.0,
        predicate=retry.if_exception_type(Exception)
    )

    @staticmethod
    def get_model_config(response_mime_type: str = "text/plain"):
        """Returns standard generation config."""
        return types.GenerateContentConfig(
            temperature=0.7, # Higher creativity for storytelling
            max_output_tokens=8192,
            response_mime_type=response_mime_type
        )

def setup_config():
    """Helper to validate environment."""
    if not os.getenv("GOOGLE_API_KEY"):
        logger.warning("⚠️ GOOGLE_API_KEY not set. Agents may fail to authenticate.")
    return Config()