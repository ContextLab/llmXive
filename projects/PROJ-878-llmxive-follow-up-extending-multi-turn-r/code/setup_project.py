import os
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in plan.md.
    Directories: data/raw/, data/processed/, code/, code/utils/, tests/, results/paper_figures/
    """
    project_root = Path(".")
    
    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "results/paper_figures"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()