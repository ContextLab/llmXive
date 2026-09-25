import os
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure for the llmXive pipeline.
    
    Creates the following directories relative to the project root:
    - code/data
    - code/analysis
    - code/config
    - code/tests
    - data/raw
    - data/results
    - figures
    - specs
    """
    base_path = Path(__file__).parent.parent
    
    directories = [
        "code/data",
        "code/analysis",
        "code/config",
        "code/tests",
        "data/raw",
        "data/results",
        "figures",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the setup script."""
    print("Starting project structure creation...")
    create_directories()
    print("Done.")

if __name__ == "__main__":
    main()
