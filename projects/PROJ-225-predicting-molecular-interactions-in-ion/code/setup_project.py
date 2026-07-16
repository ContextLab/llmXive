"""
Project initialization script for llmXive automated science pipeline.
Creates the required directory structure for the molecular interactions project.
"""
import os
import sys

def main():
    """Create the project directory structure."""
    # Define all required directories relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/validation",
        "models",
        "contracts",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "specs/001-predicting-molecular-interactions-in-ion"
    ]

    created_count = 0
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())