"""
Project Structure Initialization Script.
Creates the required directory hierarchy for the llmXive research pipeline.
"""
import os
from pathlib import Path


def create_directories():
    """
    Creates the full project directory structure as per implementation plan.
    
    Required directories:
    - src/ (source code)
    - tests/ (test suites)
    - data/ (data storage)
    - data/logs/ (resource logs)
    - data/results/ (evaluation results)
    - data/reports/ (analysis reports)
    - specs/001-evaluate-prompting-strategies/contracts/ (JSON schemas)
    - state/projects/ (project state tracking)
    """
    # Define the base project root relative to this script's location
    # Assuming this script is at code/setup_project.py, root is parent of code/
    base_path = Path(__file__).parent.parent
    
    # Define all required directories relative to root
    directories = [
        "src",
        "tests",
        "data",
        "data/logs",
        "data/results",
        "data/reports",
        "specs/001-evaluate-prompting-strategies/contracts",
        "state/projects"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        
        if full_path.exists():
            print(f"[SKIP] Directory already exists: {full_path}")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] Directory created: {full_path}")
            created_count += 1
    
    print(f"\n{'='*60}")
    print(f"Project structure initialization complete.")
    print(f"Created: {created_count} new directories.")
    print(f"Skipped: {existing_count} existing directories.")
    print(f"{'='*60}")
    
    return True


if __name__ == "__main__":
    create_directories()