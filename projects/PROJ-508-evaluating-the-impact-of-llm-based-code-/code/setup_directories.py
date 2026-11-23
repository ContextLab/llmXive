import os
from pathlib import Path

def create_directories():
    """
    Creates all required directories for the project structure.
    This function ensures that the docs/output directory exists for report generation.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "projects" / "PROJ-508-evaluating-the-impact-of-llm-based-code-" / "data" / "raw",
        project_root / "projects" / "PROJ-508-evaluating-the-impact-of-llm-based-code-" / "data" / "derived",
        project_root / "projects" / "PROJ-508-evaluating-the-impact-of-llm-based-code-" / "docs" / "output",
        project_root / "code",
        project_root / "code" / "utils",
        project_root / "tests",
        project_root / "docs",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

if __name__ == "__main__":
    create_directories()
    print("Directory setup complete.")