"""
Environment configuration management for the project.

This module handles the creation and validation of .env files,
specifically managing the HF_TOKEN for HuggingFace access.
"""
import os
import sys
from pathlib import Path
from utils.env_config import create_env_template, ensure_env_file_exists, validate_env_config, EnvConfigError

def main():
    """
    Main entry point for environment setup.
    
    Creates .env.example template and ensures .env exists for local development.
    """
    project_root = Path(__file__).resolve().parent.parent
    env_example_path = project_root / ".env.example"
    env_path = project_root / ".env"
    
    print(f"Setting up environment configuration in: {project_root}")
    
    # Create the .env.example template
    print("Creating .env.example template...")
    create_env_template(env_example_path)
    
    # Ensure .env exists (copy from example if not present)
    print("Ensuring .env file exists...")
    ensure_env_file_exists(env_path, env_example_path)
    
    # Validate the configuration
    try:
        validate_env_config(env_path)
        print("Environment configuration validated successfully.")
    except EnvConfigError as e:
        print(f"Warning: Environment configuration issue detected: {e}")
        print("Please ensure HF_TOKEN is set for HuggingFace access.")
    
    print("Environment setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())