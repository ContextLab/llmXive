import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure and necessary placeholder files
    as per the implementation plan.
    
    Structure:
    - data/raw/ (with .gitkeep)
    - data/processed/ (with .gitkeep)
    - code/
    - tests/
    - docs/
    """
    root = Path(__file__).parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs"
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path.relative_to(root)}")
    
    # Create .gitkeep files in data directories to ensure they are tracked
    # even when empty
    data_raw_keep = root / "data" / "raw" / ".gitkeep"
    data_processed_keep = root / "data" / "processed" / ".gitkeep"
    
    for keep_file in [data_raw_keep, data_processed_keep]:
        if not keep_file.exists():
            keep_file.touch()
            print(f"Created placeholder: {keep_file.relative_to(root)}")
    
    # Create README placeholders
    docs_readme = root / "docs" / "README.md"
    if not docs_readme.exists():
        docs_readme.write_text("# Documentation\n\nDocumentation for the project goes here.\n")
        print(f"Created placeholder: {docs_readme.relative_to(root)}")
    
    print("\nProject structure created successfully.")
    return True

if __name__ == "__main__":
    create_structure()
