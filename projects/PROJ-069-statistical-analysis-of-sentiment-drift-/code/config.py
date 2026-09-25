import os
from pathlib import Path
from typing import Optional
import sys
from dotenv import load_dotenv

# Ensure we load from the project root .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

def load_environment() -> bool:
    """
    Load environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env was found and loaded, False otherwise.
    """
    if ENV_FILE.exists():
        loaded = load_dotenv(dotenv_path=ENV_FILE)
        return loaded
    return False

def get_fred_api_key() -> Optional[str]:
    """
    Retrieve the FRED API key from environment variables.
    
    Returns:
        Optional[str]: The FRED API key if set, None otherwise.
    """
    return os.getenv("FRED_API_KEY")

def get_hf_token() -> Optional[str]:
    """
    Retrieve the HuggingFace token from environment variables.
    
    Returns:
        Optional[str]: The HuggingFace token if set, None otherwise.
    """
    return os.getenv("HF_TOKEN")

def get_gdelt_api_key() -> Optional[str]:
    """
    Retrieve the GDELT API key from environment variables.
    
    Note: GDELT typically doesn't require an API key for basic access,
    but this is provided for consistency with the project's config pattern.
    
    Returns:
        Optional[str]: The GDELT API key if set, None otherwise.
    """
    return os.getenv("GDELT_API_KEY")

def validate_environment() -> tuple[bool, list[str]]:
    """
    Validate that required environment variables are set.
    
    Required variables:
        - FRED_API_KEY: Required for economic data ingestion.
    
    Optional variables:
        - HF_TOKEN: Recommended for HuggingFace dataset access.
        - GDELT_API_KEY: Optional for GDELT data access.
    
    Returns:
        tuple[bool, list[str]]: (is_valid, list_of_missing_required_keys)
    """
    missing_required = []
    
    # Check required keys
    if not get_fred_api_key():
        missing_required.append("FRED_API_KEY")
    
    # Check optional but recommended keys
    missing_optional = []
    if not get_hf_token():
        missing_optional.append("HF_TOKEN (recommended)")
    if not get_gdelt_api_key():
        missing_optional.append("GDELT_API_KEY (optional)")
    
    is_valid = len(missing_required) == 0
    
    if not is_valid:
        print("ERROR: Required environment variables are missing:")
        for key in missing_required:
            print(f"  - {key}")
        print("\nPlease create a .env file in the project root with the following format:")
        print("  FRED_API_KEY=your_api_key_here")
        print("\nOptional variables:")
        for key in missing_optional:
            print(f"  {key}=<value>")
    elif missing_optional:
        print("WARNING: Optional environment variables are missing:")
        for key in missing_optional:
            print(f"  - {key}")
    
    return is_valid, missing_required

def main():
    """
    Main entry point for environment configuration validation.
    """
    print("Loading environment configuration...")
    loaded = load_environment()
    if loaded:
        print(f"✓ Loaded environment from {ENV_FILE}")
    else:
        print(f"⚠ No .env file found at {ENV_FILE}")
    
    is_valid, missing = validate_environment()
    
    if is_valid:
        print("✓ Environment validation passed")
        print(f"  FRED_API_KEY: {'*' * 10} (set)")
        if get_hf_token():
            print(f"  HF_TOKEN: {'*' * 10} (set)")
        else:
            print(f"  HF_TOKEN: not set (optional)")
        if get_gdelt_api_key():
            print(f"  GDELT_API_KEY: {'*' * 10} (set)")
        else:
            print(f"  GDELT_API_KEY: not set (optional)")
        sys.exit(0)
    else:
        print("✗ Environment validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
