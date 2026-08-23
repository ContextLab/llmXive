"""
Environment setup script for the llmXive pipeline.

Initializes the .env file if missing and validates required environment variables.
"""
import sys
from pathlib import Path
from utils.env_config import (
    EnvConfigError,
    load_env_config,
    get_hf_token,
    validate_env_config,
    ensure_env_file_exists
)


def main():
    """Main entry point for environment setup."""
    print("Setting up environment configuration...")
    
    try:
        # Ensure .env file exists (creates from template if missing)
        env_path = ensure_env_file_exists()
        print(f"Environment file ensured at: {env_path}")
        
        # Load configuration
        load_env_config()
        
        # Validate required variables
        # Currently only HF_TOKEN is required for dataset downloads
        required = ["HF_TOKEN"]
        
        # We validate but allow missing if we are just setting up
        # The actual error will be raised when the dataset loader runs
        try:
            validate_env_config(required)
            print("✓ All required environment variables are set.")
        except EnvConfigError as e:
            print(f"⚠ Warning: {e}")
            print("  Please update your .env file with the missing values.")
            print("  See .env.example for instructions.")
            
        # If HF_TOKEN is present, verify it's not the placeholder
        token = get_hf_token()
        if token and token == "YOUR_HF_TOKEN_HERE":
            print("⚠ Warning: HF_TOKEN is still set to the placeholder value.")
            print("  Please replace it with your actual token from huggingface.co.")
            return 1
            
        print("Environment setup complete.")
        return 0
        
    except EnvConfigError as e:
        print(f"Error during environment setup: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())