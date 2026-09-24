"""
Project Structure Setup Script for llmXive - Submarine Hydrothermal Vent Research
Creates the required directory structure and placeholder files as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure and initial placeholder files."""
    # Define the project root (current directory)
    project_root = Path(".")

    # Define required directories based on tasks.md
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "state",
        "results/figures",
        "specs",
        "contracts",
        "docs"
    ]

    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create placeholder files to ensure structure is recognized
    placeholder_files = [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "code/.gitkeep",
        "tests/.gitkeep",
        "state/.gitkeep",
        "results/figures/.gitkeep",
        "specs/README.md",
        "contracts/README.md",
        "docs/README.md"
    ]

    for file_path in placeholder_files:
        full_path = project_root / file_path
        # Ensure parent directory exists before creating file
        if not full_path.parent.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write a small placeholder comment if file doesn't exist or is empty
        if not full_path.exists() or full_path.stat().st_size == 0:
            with open(full_path, "w") as f:
                if file_path.endswith(".gitkeep"):
                    f.write("# Placeholder to keep directory in version control\n")
                else:
                    f.write(f"# Placeholder for {file_path}\n")
            print(f"Created placeholder file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

    print("\nProject structure setup complete.")
    print("Directories created: data/raw/, data/processed/, code/, tests/, state/, results/figures/")

if __name__ == "__main__":
    main()
