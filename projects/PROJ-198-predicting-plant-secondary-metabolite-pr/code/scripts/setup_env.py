"""
Script to initialize the environment configuration for the project.
Creates the .env file from .env.example if it doesn't exist.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Main entry point for environment setup.
    """
    # Determine project root (assuming script is in code/scripts/)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    
    env_example_path = project_root / "code" / ".env.example"
    env_path = project_root / "code" / ".env"
    
    if not env_example_path.exists():
        print(f"Error: Template file not found at {env_example_path}")
        sys.exit(1)
    
    if env_path.exists():
        print(f".env file already exists at {env_path}. Skipping creation.")
        print("Please review and update the values in the existing .env file.")
        return
    
    # Copy .env.example to .env
    try:
        with open(env_example_path, 'r', encoding='utf-8') as f_src:
            content = f_src.read()
        
        with open(env_path, 'w', encoding='utf-8') as f_dst:
            f_dst.write(content)
        
        print(f"Successfully created .env file at {env_path}")
        print("Please update the values in the .env file before running the pipeline.")
    except Exception as e:
        print(f"Error creating .env file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()