"""
Script to initialize the environment configuration.
Creates .env file from .env.example if it doesn't exist.
Validates that required directories and configuration are in place.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parents[1]
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"

    # Create .env from .env.example if it doesn't exist
    if not env_file.exists():
        if env_example.exists():
            print(f"Creating .env from .env.example...")
            with open(env_example, "r") as src:
                content = src.read()
            with open(env_file, "w") as dst:
                dst.write(content)
            print(f"Created: {env_file}")
            print("Please edit .env to set your API keys and paths if needed.")
        else:
            print(f"Warning: .env.example not found at {env_example}")
            print("Creating empty .env file...")
            env_file.touch()
    else:
        print(f".env already exists at {env_file}")

    # Load configuration and ensure directories exist
    from utils.config import get_config
    config = get_config(env_file)
    
    print("Ensuring required directories exist...")
    config.ensure_dirs()
    
    # Validate configuration
    print("\nConfiguration Summary:")
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        if key != "api_keys_valid":
            print(f"  {key}: {value}")
    
    # Check API keys (optional for synthetic-only mode)
    api_status = config_dict.get("api_keys_valid", {})
    print("\nAPI Key Status:")
    for key, is_valid in api_status.items():
        status = "✓" if is_valid else "○"
        print(f"  {status} {key}: {'Set' if is_valid else 'Not set (OK for synthetic mode)'}")

    print("\nEnvironment setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())