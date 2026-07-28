import os
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the llmXive pipeline.
    Ensures all necessary folders for code, tests, data (raw/processed), and logs exist.
    """
    # Define the project root relative to this script's location or current working dir
    # Assuming this script runs from the project root or code/
    project_root = Path.cwd()
    
    # Define relative paths as per task requirements
    directories = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/results/diagnostics",
        "figures",
        "logs",
        "specs"
    ]

    created = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")

    # Ensure data/raw/lexicons exists for T008 (Rosenberg lexicon)
    lexicon_path = project_root / "data" / "raw" / "lexicons"
    if not lexicon_path.exists():
        lexicon_path.mkdir(parents=True, exist_ok=True)
        print(f"Created lexicon directory: {lexicon_path}")

    return True

if __name__ == "__main__":
    create_directories()
