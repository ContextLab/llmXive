import os
from pathlib import Path

def main():
    # Define the directory structure as required by T001
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "results",
        "paper",
        "tests",
    ]

    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Create an empty __init__.py in each directory as requested
        init_file = path / "__init__.py"
        init_file.touch()
        print(f"Created directory and __init__.py at: {dir_path}")

if __name__ == "__main__":
    main()
