import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for llmXive Follow-up:
    Reward Fidelity vs. Error Recovery Density.
    
    Creates directories under the project root:
    - data/raw
    - data/processed
    - code
    - code/utils
    - code/tests
    - results
    - artifacts
    - specs/001-reward-fidelity-error-recovery/contracts
    """
    # Determine project root relative to this script's location
    # Assuming this script is at code/setup_project_structure.py
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define the directories to create relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "code/tests",
        "results",
        "artifacts",
        "specs/001-reward-fidelity-error-recovery/contracts",
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created: {full_path}")
        else:
            print(f"Exists:  {full_path}")
    
    print(f"\nTotal directories created/verified: {len(created_dirs)}")
    print("\nDirectory structure verification (ls):")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.is_dir():
            print(f"[OK] {dir_path}")
        else:
            print(f"[FAIL] {dir_path} - not found")
            return 1
    
    print("\nAll required directories verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())