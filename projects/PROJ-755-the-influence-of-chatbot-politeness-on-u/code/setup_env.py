"""
Setup environment configuration management.

This script ensures the .env template exists and provides utilities
for managing environment variables required for the project.
"""
import os
import sys
from pathlib import Path
from utils.env_config import create_env_template, ensure_env_file_exists, validate_env_config, EnvConfigError

def main():
    """
    Main entry point for environment setup.
    
    1. Ensures the .env.example template exists in the project root.
    2. Validates the current environment configuration if .env exists.
    3. Prints instructions for local vs CI configuration.
    """
    project_root = Path(__file__).resolve().parent.parent
    env_example_path = project_root / ".env.example"
    env_path = project_root / ".env"

    print(f"Setting up environment configuration in {project_root}...")

    # Ensure template exists
    if not env_example_path.exists():
        print("Creating .env.example template...")
        create_env_template(project_root)
        print(f"Created: {env_example_path}")
    else:
        print(f"Template already exists: {env_example_path}")

    # Validate current env if it exists
    if env_path.exists():
        print("Validating existing .env configuration...")
        try:
            validate_env_config(project_root)
            print("Configuration valid.")
        except EnvConfigError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
    else:
        print("No .env file found. Creating a copy of the template for local development...")
        ensure_env_file_exists(project_root)
        print(f"Created: {env_path} (copy of .env.example)")

    print("\n--- Configuration Instructions ---")
    print("Local Development: Edit the .env file with your HF_TOKEN.")
    print("CI/CD (GitHub Actions): Inject HF_TOKEN via repository secrets.")
    print("----------------------------------")

if __name__ == "__main__":
    main()