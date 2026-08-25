import os
from pathlib import Path
from typing import Optional
import sys
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # If .env is missing, we rely on system environment variables
    # This allows the script to run in CI/CD without a local .env file
    pass

def get_fred_api_key() -> str:
    """
    Retrieve the FRED API key from environment variables.
    
    Returns:
        str: The FRED API key.
    
    Raises:
        KeyError: If the FRED_API_KEY is not set in the environment.
    """
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise KeyError(
            "FRED_API_KEY environment variable is not set. "
            "Please set it in your .env file or system environment."
        )
    return key

def get_hf_token() -> Optional[str]:
    """
    Retrieve the HuggingFace token from environment variables.
    
    Returns:
        Optional[str]: The HuggingFace token if set, None otherwise.
        HF token is optional for this project (used for optional dataset fetching).
    """
    return os.getenv("HF_TOKEN")

def get_gdelt_api_key() -> Optional[str]:
    """
    Retrieve the GDELT API key from environment variables.
    
    Returns:
        Optional[str]: The GDELT API key if set, None otherwise.
        GDELT 2.0 API usually does not require a key for basic access,
        but this allows for future key-based access if needed.
    """
    return os.getenv("GDELT_API_KEY")

def validate_environment() -> bool:
    """
    Validate that all required environment variables are present.
    
    Returns:
        bool: True if all required variables are present, False otherwise.
    
    Side Effects:
        Prints warnings to stderr for missing optional keys.
        Raises KeyError for missing required keys (FRED_API_KEY).
    """
    # Required
    if not os.getenv("FRED_API_KEY"):
        raise KeyError(
            "FRED_API_KEY is required but not found in environment. "
            "Please add it to .env or set it in your shell."
        )
    
    # Optional but recommended
    if not os.getenv("HF_TOKEN"):
        print("Warning: HF_TOKEN is not set. Some HuggingFace features may be limited.", file=sys.stderr)
    
    return True

def load_environment() -> dict:
    """
    Load all relevant environment variables into a dictionary.
    
    Returns:
        dict: A dictionary containing the loaded environment variables.
    """
    return {
        "fred_api_key": os.getenv("FRED_API_KEY"),
        "hf_token": os.getenv("HF_TOKEN"),
        "gdelt_api_key": os.getenv("GDELT_API_KEY"),
    }

def main():
    """
    Main entry point for testing environment configuration.
    """
    print("Loading environment configuration...")
    try:
        validate_environment()
        print("Environment validation successful.")
        config = load_environment()
        print(f"Loaded config keys: {list(config.keys())}")
        # Mask sensitive values for display
        masked_config = {k: "***" if v else "None" for k, v in config.items()}
        print(f"Config values: {masked_config}")
        return 0
    except KeyError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
