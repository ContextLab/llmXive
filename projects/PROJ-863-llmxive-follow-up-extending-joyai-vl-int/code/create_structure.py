"""
Script to create the project directory structure for llmXive.
This script ensures all required directories exist as per the implementation plan.
"""
import os
from pathlib import Path

def main():
    # Define the base directory (current working directory or specified root)
    base_dir = Path(__file__).resolve().parent
    
    # Define the required directories relative to the project root
    # Note: The task description mentions 'src/', but the API surface provided 
    # indicates the code lives in 'code/'. We will create the structure 
    # under 'code/' to align with the existing API surface provided in the prompt.
    # If the project root is the parent of 'code', we adjust accordingly.
    # Based on 'code/src/data_synthesis/models.py' existing, we create under code/src.
    
    structure = [
        "src/data_synthesis",
        "src/feature_extraction",
        "src/baseline",
        "src/scheduler",
        "tests",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/features",
        "data/baseline",
        "data/evaluation",
        "models",
        "figures",
        "logs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in structure:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            skipped_count += 1
    
    print(f"\nProject structure ready.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {skipped_count}")

if __name__ == "__main__":
    main()