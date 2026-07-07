import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Specifically ensures the docs/output directory exists for report artifacts.
    """
    base_path = Path("projects/PROJ-508-evaluating-the-impact-of-llm-based-code-")
    
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "docs" / "output",
        base_path / "code",
        base_path / "code" / "utils",
        base_path / "tests",
        base_path / "specs" / "001-evaluating-the-impact-of-llm-based-code",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    create_directories()
