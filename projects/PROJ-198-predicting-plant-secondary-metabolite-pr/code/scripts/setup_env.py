import os
import sys
from pathlib import Path

def main():
    """
    Setup script for environment configuration.
    Creates .env file template and ensures required directories exist.
    """
    print("Setting up environment configuration...")

    # Create .env file template if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        template_content = """# Environment Configuration for Plant Secondary Metabolite Prediction Project
# Copy this file to .env and fill in your values

# API Keys (Optional - only required if using specific services)
# NCBI_API_KEY=your_ncbi_api_key_here
# PHYTOZOME_API_KEY=your_phytozome_api_key_here
# METABOLIGHTS_API_KEY=your_metabolights_api_key_here
# PMDB_API_KEY=your_pmdb_api_key_here

# Local Paths (Optional - defaults to project root subdirectories)
# DATA_ROOT=data
# CODE_ROOT=code
# LOGS_DIR=logs
# FIGURES_DIR=figures
# STATE_DIR=state

# Optional: Custom paths for external tools
# ANTIMASH_PATH=/path/to/antismash
# HMMER_PATH=/path/to/hmmer
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(template_content)
        print(f"Created .env file template at {env_file}")
        print("Please edit .env and add your API keys if needed.")
    else:
        print(f".env file already exists at {env_file}")

    # Ensure directories exist
    directories = [
        "data",
        "data/raw",
        "data/processed",
        "data/interim",
        "code",
        "logs",
        "figures",
        "state",
        "state/projects"
    ]

    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

    print("Environment setup complete.")
    print("Next steps:")
    print("1. Edit .env file to add your API keys (if needed)")
    print("2. Run the pipeline with 'python -m code.cli.main'")

if __name__ == "__main__":
    main()