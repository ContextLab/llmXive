import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as specified in the implementation plan.
    This includes code subdirectories, data subdirectories, and state directories.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define all required directories relative to the project root
    directories = [
        "code/data_prep",
        "code/analysis",
        "code/utils",
        "code/tests",
        "data/defects4j",
        "data/summaries",
        "data/interaction_logs",
        "data/analysis_results",
        "data/consent",
        "state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """
    Entry point for the script.
    """
    try:
        success = create_directories()
        if success:
            print("SUCCESS: Project structure created successfully.")
            sys.exit(0)
        else:
            print("ERROR: Failed to create project structure.")
            sys.exit(1)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
