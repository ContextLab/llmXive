import os
import sys
from pathlib import Path

def create_state_directory():
    """
    Creates the 'state/' directory in the repository root.
    Verifies that the directory exists after creation.
    """
    repo_root = Path(__file__).resolve().parent.parent
    state_dir = repo_root / "state"
    
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created state directory: {state_dir}")
    else:
        print(f"State directory already exists: {state_dir}")
    
    # Verification
    if state_dir.is_dir():
        print("Verification passed: 'state/' directory exists.")
        return True
    else:
        print("Verification failed: 'state/' directory does not exist.")
        return False

def main():
    success = create_state_directory()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()