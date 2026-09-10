import os
import sys
from pathlib import Path
import shutil

def check_dotenv():
    """
    Checks if a .env file exists in the project root.
    Returns True if it exists, False otherwise.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    return env_path.exists()

def setup_env_file():
    """
    Creates a default .env.example file if .env does not exist.
    This file serves as a template for API keys and data paths.
    """
    root_dir = Path(__file__).resolve().parent.parent
    env_path = root_dir / ".env"
    env_example_path = root_dir / ".env.example"

    if env_path.exists():
        print("Environment file (.env) already exists.")
        return

    # Define default template content
    template = """
# Environment Configuration for PROJ-531
# Copy this file to .env and fill in the values.
# Do not commit .env to version control.

# Data Paths
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed
DATA_RESULTS_DIR=data/results

# API Keys (if external services are used)
# OPENML_API_KEY=
# HUGGINGFACE_TOKEN=

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/project.log
"""

    env_example_path.write_text(template.strip())
    print(f"Created .env.example template at {env_example_path}")
    print("Please copy .env.example to .env and configure your variables.")

def ensure_directories():
    """
    Ensures that standard project directories exist based on config or defaults.
    """
    root_dir = Path(__file__).resolve().parent.parent
    dirs = [
        root_dir / "data" / "raw",
        root_dir / "data" / "processed",
        root_dir / "data" / "results",
        root_dir / "logs",
        root_dir / "figures",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main entry point for environment setup.
    """
    ensure_directories()
    setup_env_file()
    if check_dotenv():
        print("Environment ready.")
    else:
        print("Setup complete. Please configure .env before running analysis.")

if __name__ == "__main__":
    main()