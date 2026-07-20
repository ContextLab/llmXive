"""
Script to initialize the project directory structure for the
llmXive research pipeline: The Impact of Simulated Social Feedback.

This script creates the necessary directories for code, tests, data,
and logs as defined in the implementation plan.
"""
import os
from pathlib import Path

def create_directories():
    """Create the project directory structure."""
    base_path = Path(".")
    
    # Define the directories to create
    directories = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/raw/lexicons",
        "data/processed",
        "data/results",
        "data/results/diagnostics",
        "figures",
        "logs",
        "specs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    print("Project structure initialized successfully.")

if __name__ == "__main__":
    create_directories()