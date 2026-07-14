"""
Project Structure Initialization Script.

Creates the required directory hierarchy and initializes the project state YAML file
for PROJ-672-the-impact-of-bounded-confidence-on-opin.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to where this script runs
    # Assuming this script is in code/
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/contract",
        "state/projects",
        "docs",
        "specs",
        "figures",
        "code/utils",
        "code/contracts",
        "code/explorers",
        "code/visualizations",
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Initialize project state YAML
    project_id = "PROJ-672-the-impact-of-bounded-confidence-on-opin"
    state_file = project_root / "state" / "projects" / f"{project_id}.yaml"
    
    if not state_file.exists():
        content = f"""project_id: {project_id}
title: The Impact of Bounded Confidence on Opinion Polarization Speed
status: active
created_at: 2026-06-10T00:00:00Z
updated_at: 2026-06-10T00:00:00Z
phase: setup
completed_tasks: []
current_tasks:
  - T001
dependencies: []
artifacts:
  checksums: []
metadata:
  version: 0.1.0
  python_version: "3.11"
  author: llmXive
  description: >
    Investigating how bounded confidence thresholds (epsilon) influence the speed
    and stability of opinion polarization in complex networks using the
    Hegselmann-Krause model.
"""
        state_file.write_text(content)
        print(f"Initialized project state file: {state_file}")
    else:
        print(f"Project state file already exists: {state_file}")
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()