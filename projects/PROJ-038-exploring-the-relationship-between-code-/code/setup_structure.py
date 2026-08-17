import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for the llmXive research pipeline.
    
    Creates the following directories relative to the project root:
    - code/
    - code/src/
    - code/tests/
    - code/data/raw/
    - code/data/processed/
    - code/data/results/
    - specs/001-code-complexity-bug-prediction/
    """
    base_dir = Path(__file__).parent.parent
    project_root = base_dir / "code"
    
    directories = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "specs/001-code-complexity-bug-prediction",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()