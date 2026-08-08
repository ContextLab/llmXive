"""
Script to initialize environment configuration for the project.
Creates .env file from template if it doesn't exist.
"""
import os
import sys
from pathlib import Path

def main():
    """Initialize environment configuration."""
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        print("✓ .env file already exists. Skipping creation.")
        print("  Edit .env to configure your API keys and paths.")
    else:
        print("Creating .env file from template...")
        if env_example.exists():
            content = env_example.read_text()
            env_file.write_text(content)
            print(f"✓ Created {env_file}")
            print("  Please edit .env and fill in your API keys.")
        else:
            print("Error: .env.example template not found.")
            sys.exit(1)

    # Ensure directories exist
    print("\nEnsuring directory structure...")
    from config_env import load_environment, ensure_directories
    config = load_environment()
    ensure_directories(config)
    print("✓ Directory structure ready.")

    print("\nEnvironment setup complete!")
    print("Next steps:")
    print("  1. Edit .env with your API keys (if needed)")
    print("  2. Run your pipeline scripts")

if __name__ == "__main__":
    main()
