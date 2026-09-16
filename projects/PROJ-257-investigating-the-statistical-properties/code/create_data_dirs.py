import os
from pathlib import Path


def create_directories():
    """
    Creates the data/ and output/ directory structures required for the project.
    
    Structure:
    data/
        raw/
        processed/
    output/
        results/
        figures/
        
    Creates .gitkeep files in each subdirectory to ensure they are tracked by git.
    """
    base_path = Path("data")
    output_path = Path("output")

    # Define subdirectories
    data_dirs = [
        base_path / "raw",
        base_path / "processed",
    ]

    output_dirs = [
        output_path / "results",
        output_path / "figures",
    ]

    all_dirs = data_dirs + output_dirs

    # Create directories and .gitkeep files
    for dir_path in all_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        print(f"Created: {dir_path}")
        print(f"Created: {gitkeep_path}")

    print("Directory structure creation complete.")


def main():
    create_directories()


if __name__ == "__main__":
    main()