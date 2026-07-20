"""
Script to initialize the data directory structure for the Socratic Transformers project.
Creates raw, processed, and results directories with .gitkeep files.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root relative to this script
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    data_dir = project_root / "data"

    subdirs = ["raw", "processed", "results"]
    created = []

    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = subdir_path / ".gitkeep"
        
        # Write a descriptive .gitkeep file
        description = {
            "raw": "This directory stores raw, unprocessed datasets (e.g., GSM8K, MATH).\nFiles here are downloaded directly from source and must not be modified.",
            "processed": "This directory stores processed datasets derived from raw data.\nIncludes static QA tuples, dialogue tuples, and ablation datasets.",
            "results": "This directory stores experiment results, metrics, and analysis outputs.\nIncludes training logs, evaluation metrics, and statistical analysis JSONs."
        }
        
        with open(gitkeep_path, "w", encoding="utf-8") as f:
            f.write(f"# {description[subdir_name]}\n")
        
        created.append(str(gitkeep_path))
        print(f"Created: {gitkeep_path}")

    print(f"\nData directory structure initialized at: {data_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())