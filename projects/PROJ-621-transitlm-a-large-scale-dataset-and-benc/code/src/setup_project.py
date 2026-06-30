"""
Project Setup Script for llmXive TransitLM Project.
Atomically generates the required directory structure.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to the script location or current working directory
# Assuming this script is run from the project root or installed in code/src
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define the directory structure to create
# Based on tasks.md and plan.md conventions:
# - src/: Source code
# - tests/: Unit and integration tests
# - specs/: Feature specifications and design docs
# - data/: Raw and processed data
# - data/raw/: Raw GTFS feeds
# - data/processed/: Processed sequences and splits
# - data/results/: Benchmark results and reports
# - figures/: Generated plots and visualizations
# - code/: Scripts and executables (if separate from src)
# Note: tasks.md mentions 'src/' and 'tests/' at root, but also 'code/' in constraints.
# We will create the standard 'src', 'tests', 'specs', 'data', 'figures' at root.
# We also create 'code' if the task implies scripts live there, but 'src' is the primary source.
# Given T001a created 'code/src/setup_project.py', we ensure the structure aligns.

DIRECTORIES = [
  "src",
  "src/lib",
  "src/models",
  "src/analysis",
  "src/cli",
  "src/contracts",
  "tests",
  "tests/unit",
  "tests/contract",
  "tests/integration",
  "specs",
  "specs/001-map-free-transit-route-generation",
  "data",
  "data/raw",
  "data/processed",
  "data/results",
  "figures",
  "code", # Ensuring code directory exists as per constraints
]

# Optional files to create as placeholders if they don't exist
# (Not strictly required by T001b, but good for initialization)
# T001b specifically asks to execute the script to create the structure.

def create_directories():
    """Creates all defined directories if they do not exist."""
    created_count = 0
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(PROJECT_ROOT)}")
            created_count += 1
        # else:
        #     print(f"Directory already exists: {full_path.relative_to(PROJECT_ROOT)}")
    
    if created_count == 0:
        print("All directories already exist.")
    else:
        print(f"Successfully created {created_count} directories.")

def main():
    print(f"Project Root: {PROJECT_ROOT}")
    create_directories()
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
