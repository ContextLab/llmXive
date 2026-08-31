import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for llmXive.
    Ensures all required directories exist under the project root.
    """
    # Define the directory structure relative to the project root
    # Based on tasks.md: code/, data/raw/, data/processed/, data/analysis/, models/, analysis/, tests/, docs/
    # Note: The task description lists 'models/' and 'analysis/' at root level, 
    # but the existing API surface shows code/models/ and code/analysis/.
    # We will create the structure consistent with the existing API surface (code/) 
    # and the data directories as specified.
    
    directories = [
        "code",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/data/analysis",
        "code/models",
        "code/analysis",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "models",
        "analysis",
        "logs"
    ]

    # Determine project root (current working directory for this script)
    # In the context of the pipeline, this script runs from the repo root.
    project_root = Path(".")

    created_count = 0
    existing_count = 0

    print(f"Creating project structure in: {project_root.absolute()}")

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optional: print existing if needed for debugging, but keep output clean
            # print(f"Directory already exists: {dir_path}")

    print(f"Project structure setup complete. Created: {created_count}, Already existed: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())