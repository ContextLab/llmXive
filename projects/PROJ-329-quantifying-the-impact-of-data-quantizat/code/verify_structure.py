import os
import sys
from pathlib import Path
from datetime import datetime

def check_structure(base_path: Path) -> dict:
    """
    Verify that the directory structure matches the expected plan.
    
    Expected structure based on T001a and general project layout:
    - code/
        - src/
        - tests/
        - data/
            - raw/
            - processed/
            - results/
    - logs/
    
    Returns a dict with 'valid' (bool) and 'missing' (list of paths).
    """
    expected_dirs = [
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "logs"
    ]
    
    missing = []
    for d in expected_dirs:
        full_path = base_path / d
        if not full_path.exists():
            missing.append(str(full_path.relative_to(base_path)))
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "checked_at": datetime.now().isoformat()
    }

def verify_structure(base_path: Path = None) -> bool:
    """
    Main entry point to verify the project structure.
    Prints the result to stdout and exits with code 0 if valid, 1 if not.
    
    Args:
        base_path: Path to the project root. Defaults to current working directory.
        
    Returns:
        bool: True if structure is valid, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
        
    # Handle case where base_path might be the project root or the 'code' folder
    # We look for the 'code' folder relative to base_path
    if (base_path / "code" / "src").exists():
        project_root = base_path
    elif (base_path / "src").exists():
        # If we are already inside the code folder (unlikely given task description)
        # but just in case, check if we are one level up
        project_root = base_path.parent
    else:
        print(f"ERROR: Could not determine project root from {base_path}")
        return False

    result = check_structure(project_root)
    
    if result["valid"]:
        print("SUCCESS: Directory structure matches the plan.")
        print(f"Checked at: {result['checked_at']}")
        return True
    else:
        print("FAILURE: Directory structure does not match the plan.")
        print(f"Checked at: {result['checked_at']}")
        print(f"Missing directories:")
        for m in result["missing"]:
            print(f"  - {m}")
        return False

if __name__ == "__main__":
    # Determine project root: usually the directory containing 'code' and 'logs'
    # The script is located in code/, so we go up one level to the project root
    current_file = Path(__file__).resolve()
    # Assuming script is at code/verify_structure.py
    project_root = current_file.parent.parent 
    
    success = verify_structure(project_root)
    sys.exit(0 if success else 1)