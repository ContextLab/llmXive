import os
from pathlib import Path
from typing import Optional
import sys
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file if it exists."""
# Find the project root (assuming code/ is the root for this script or parent)
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try current directory if running from root
        load_dotenv()

def get_fred_api_key() -> str:
    """Retrieve FRED API key from environment."""
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise ValueError(
            "FRED_API_KEY not found in environment. "
            "Please set it in your .env file or export it."
        )
    return key

def get_hf_token() -> Optional[str]:
    """Retrieve HuggingFace token from environment."""
    return os.getenv("HF_TOKEN")

def get_gdelt_api_key() -> Optional[str]:
    """Retrieve GDELT API key from environment."""
    return os.getenv("GDELT_API_KEY")

def validate_environment():
    """Validate that required environment variables are set."""
    # FRED is required for T016
    if not os.getenv("FRED_API_KEY"):
        raise RuntimeError("FRED_API_KEY is required but not set.")

def main():
    """Test environment loading."""
    load_environment()
    try:
        key = get_fred_api_key()
        print("FRED API Key loaded successfully.")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()