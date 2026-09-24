import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

def get_installed_packages() -> Dict[str, str]:
    """
    Retrieve the list of installed packages and their versions.
    
    Returns:
        Dict mapping package names to versions.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==', 1)
                packages[name.lower()] = version
        return packages
    except subprocess.CalledProcessError as e:
        print(f"Error running pip freeze: {e}")
        return {}

def load_requirements(req_path: Path) -> Dict[str, str]:
    """
    Load requirements from a requirements.txt file.
    
    Args:
        req_path: Path to the requirements file.
        
    Returns:
        Dict mapping package names to required versions.
    """
    packages = {}
    if not req_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")
    
    with open(req_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '==' in line:
                name, version = line.split('==', 1)
                packages[name.lower()] = version
    return packages

def verify_installation(
    required: Dict[str, str], 
    installed: Dict[str, str]
) -> List[str]:
    """
    Verify that all required packages are installed with correct versions.
    
    Args:
        required: Dict of required packages and versions.
        installed: Dict of installed packages and versions.
        
    Returns:
        List of missing or mismatched package names.
    """
    issues = []
    for name, version in required.items():
        if name not in installed:
            issues.append(f"MISSING: {name} (required {version})")
        elif installed[name] != version:
            issues.append(
                f"MISMATCH: {name} (required {version}, found {installed[name]})"
            )
    return issues

def main():
    """
    Main entry point for dependency verification.
    
    This script:
    1. Loads requirements from code/requirements.txt
    2. Retrieves currently installed packages
    3. Compares and reports any missing or mismatched packages
    4. Exits with code 1 if verification fails, 0 otherwise
    """
    # Determine project root (assume script is in code/tests/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    req_path = project_root / "code" / "requirements.txt"
    
    print(f"Verifying dependencies from: {req_path}")
    
    if not req_path.exists():
        print(f"ERROR: Requirements file not found at {req_path}")
        sys.exit(1)
    
    try:
        required = load_requirements(req_path)
        installed = get_installed_packages()
        
        print(f"\nFound {len(required)} required packages")
        print(f"Found {len(installed)} installed packages\n")
        
        issues = verify_installation(required, installed)
        
        if issues:
            print("VERIFICATION FAILED:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("VERIFICATION PASSED: All dependencies installed correctly.")
            print("\nInstalled versions:")
            for name, version in sorted(required.items()):
                print(f"  {name}=={version}")
            sys.exit(0)
            
    except Exception as e:
        print(f"ERROR during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()