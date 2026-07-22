import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in T001.
    This script ensures all required directories exist for the
    Robotic AI Sensory Fidelity Ablation Study.
    """
    # Define the root of the project relative to the script location
    # The script is located at code/scripts/, so root is two levels up
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # Define the directories to create relative to project_root
    # Based on T001: `mkdir -p code/src/{environment,data,agents,analysis,utils} code/scripts code/tests code/data code/results`
    directories = [
        "code/src/environment",
        "code/src/data",
        "code/src/agents",
        "code/src/analysis",
        "code/src/utils",
        "code/scripts",
        "code/tests",
        "code/data",
        "code/results"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Project Root: {project_root}")
    print("Creating project structure...")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optional: print if needed, but silent is often better for idempotency
            # print(f"  Exists:  {full_path}")
    
    print(f"Structure setup complete. Created {created_count} directories, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())