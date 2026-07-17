"""
Task T003: Create directory `output/plots/` in the project root.

This script ensures the output/plots directory exists for storing
visualization artifacts (e.g., 3D surface plots).
"""
import os
from pathlib import Path

def main():
    """Create the output/plots directory if it does not exist."""
    # Determine the project root based on the task description
    # The task specifies the path relative to the project root:
    # projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
    # We assume this script runs from the project root or we construct the path relative to __file__
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent  # Assuming script is in code/
    
    target_dir = project_root / "output" / "plots"
    
    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {target_dir}")
    else:
        print(f"Directory already exists: {target_dir}")

if __name__ == "__main__":
    main()
