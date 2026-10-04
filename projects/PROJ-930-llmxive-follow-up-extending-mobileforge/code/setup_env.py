"""
Setup script for environment configuration.
Creates .env file from .env.example if it doesn't exist.
"""
import os
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"
    env_example_path = project_root / ".env.example"

    if env_path.exists():
        print(".env file already exists. Skipping creation.")
        return 0

    if not env_example_path.exists():
        print("Error: .env.example not found.")
        return 1

    # Copy .env.example to .env
    with open(env_example_path, 'r') as src:
        content = src.read()

    with open(env_path, 'w') as dst:
        dst.write(content)

    print(f"Created .env file from .env.example at: {env_path}")
    print("Please edit .env and configure the required environment variables.")
    return 0


if __name__ == "__main__":
    exit(main())
