import os
from pathlib import Path

def create_project_structure(base_path: str) -> None:
    """
    Creates the project directory structure for PROJ-951-llmxive-follow-up-extending-physisforcin.
    
    Structure:
    code/
      data/
        raw/
        curated/
        eval/
      src/
        generation/
        filtering/
        training/
        evaluation/
        utils/
      tests/
        unit/
        integration/
    
    Args:
        base_path: The root directory where the project structure will be created.
    """
    # Define the relative paths based on the task description
    relative_paths = [
        "data/raw",
        "data/curated",
        "data/eval",
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/utils",
        "tests/unit",
        "tests/integration"
    ]
    
    base = Path(base_path)
    base.mkdir(parents=True, exist_ok=True)
    
    created_count = 0
    for rel_path in relative_paths:
        full_path = base / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure creation complete. {created_count} new directories created.")
    print(f"Base path: {base.resolve()}")

if __name__ == "__main__":
    # Default execution creates the structure in the current directory under 'code/'
    # or allows an override via argument.
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "."
    
    create_project_structure(target)