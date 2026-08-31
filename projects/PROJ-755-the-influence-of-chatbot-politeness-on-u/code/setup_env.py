"""
Environment Setup Utility for PROJ-755.

This script ensures the existence of the .env file and validates the configuration.
It is intended to be run during the initial setup phase or as a helper for developers.
"""
import os
import sys
from pathlib import Path
from utils.env_config import create_env_template, ensure_env_file_exists, validate_env_config, EnvConfigError

def main():
    """
    Main entry point for environment setup.
    
    1. Checks if .env exists. If not, copies .env.example to .env.
    2. Validates that HF_TOKEN is set if the .env file is present.
    """
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    env_example_path = project_root / ".env.example"

    print(f"Checking environment configuration at: {env_path}")

    if not env_path.exists():
        if env_example_path.exists():
            print(".env file not found. Creating from .env.example...")
            # Copy contents manually to ensure it's a new file, not a link
            with open(env_example_path, 'r') as f_src:
                content = f_src.read()
            with open(env_path, 'w') as f_dst:
                f_dst.write(content)
            print(f"Created {env_path}. Please edit this file to add your HF_TOKEN.")
        else:
            print("ERROR: .env.example not found. Cannot create .env.")
            sys.exit(1)
    else:
        print(".env file exists.")

    # Validate configuration
    try:
        validate_env_config(env_path)
        print("Environment configuration is valid.")
    except EnvConfigError as e:
        print(f"WARNING: {e}")
        print("Note: HF_TOKEN is required for downloading datasets. "
              "If running in CI, ensure HF_TOKEN is set as an environment variable.")
        # We do not exit here, as the pipeline might run in a mode that doesn't require the token immediately
        # or might fail later with a clearer error if the token is actually needed.

if __name__ == "__main__":
    main()
