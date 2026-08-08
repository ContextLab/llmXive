"""
Script to setup the data directory structure for the Socratic Transformers project.
Creates raw, processed, and results directories with .gitkeep files.
"""
import os
import sys
from pathlib import Path

def create_gitkeep(directory: Path) -> None:
    """Create a .gitkeep file in the specified directory to ensure it is tracked by git."""
    gitkeep_path = directory / ".gitkeep"
    if not gitkeep_path.exists():
        # Create a minimal comment explaining the directory's purpose
        purpose = {
            "raw": "Raw datasets from external sources (e.g., GSM8K, MATH).",
            "processed": "Processed datasets ready for training.",
            "results": "Evaluation results, metrics, and analysis reports."
        }
        dir_name = directory.name
        comment = purpose.get(dir_name, "Data directory.")
        content = f"# {comment}\n"
        gitkeep_path.write_text(content, encoding="utf-8")
        print(f"Created: {gitkeep_path}")
    else:
        print(f"Exists: {gitkeep_path}")

def main() -> None:
    """Main function to create data directory structure."""
    # Determine project root based on script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_root = project_root / "data"

    # Define required subdirectories
    subdirs = ["raw", "processed", "results"]

    print(f"Setting up data directories in: {data_root}")
    
    for subdir in subdirs:
        dir_path = data_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        create_gitkeep(dir_path)

    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()