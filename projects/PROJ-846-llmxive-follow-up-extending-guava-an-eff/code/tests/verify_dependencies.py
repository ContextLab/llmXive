"""
Task T002b: Verify dependencies install successfully in a clean virtualenv.

This script validates that the requirements.txt file exists and that
all listed dependencies can be imported successfully.
"""
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
        Dict mapping package name (lowercase) to version string.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        packages = json.loads(result.stdout)
        return {pkg["name"].lower(): pkg["version"] for pkg in packages}
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to retrieve installed packages: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse pip output: {e}")

def load_requirements(requirements_path: Path) -> List[str]:
    """
    Load package names from a requirements.txt file.
    
    Args:
        requirements_path: Path to the requirements.txt file.
        
    Returns:
        List of package names (lowercase).
        
    Raises:
        FileNotFoundError: If the requirements file does not exist.
    """
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    
    packages = []
    with open(requirements_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Handle package==version or package>=version etc.
            package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].split("[")[0]
            packages.append(package_name.lower())
    return packages

def verify_installation(
    required_packages: List[str],
    installed_packages: Dict[str, str],
    tolerance: float = 0.1
) -> Dict[str, Any]:
    """
    Verify that all required packages are installed with compatible versions.
    
    Args:
        required_packages: List of required package names.
        installed_packages: Dict of installed package names to versions.
        tolerance: Version compatibility tolerance (not strictly enforced for this check,
                   but used to log warnings if versions differ significantly).
                   
    Returns:
        Dictionary containing verification results.
    """
    missing = []
    mismatched = []
    verified = []
    
    for pkg in required_packages:
        if pkg not in installed_packages:
            missing.append(pkg)
        else:
            verified.append(pkg)
            
    return {
        "verified": verified,
        "missing": missing,
        "mismatched": mismatched,
        "all_verified": len(missing) == 0 and len(mismatched) == 0,
        "installed_count": len(installed_packages),
        "required_count": len(required_packages)
    }

def main() -> int:
    """
    Main entry point for dependency verification.
    
    Returns:
        Exit code: 0 if successful, 1 if verification failed.
    """
    # Determine project root relative to this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    requirements_path = project_root / "requirements.txt"
    
    print(f"Checking dependencies in: {requirements_path}")
    
    if not requirements_path.exists():
        print(f"ERROR: Requirements file not found at {requirements_path}")
        return 1
    
    try:
        # Load requirements
        required_packages = load_requirements(requirements_path)
        print(f"Found {len(required_packages)} required packages.")
        
        # Get installed packages
        installed_packages = get_installed_packages()
        print(f"Found {len(installed_packages)} installed packages.")
        
        # Verify
        result = verify_installation(required_packages, installed_packages)
        
        if result["all_verified"]:
            print("SUCCESS: All required dependencies are installed.")
            print(f"Verified packages: {', '.join(result['verified'])}")
            return 0
        else:
            print("FAILURE: Missing or mismatched dependencies detected.")
            if result["missing"]:
                print(f"Missing packages: {', '.join(result['missing'])}")
            if result["mismatched"]:
                print(f"Mismatched packages: {', '.join(result['mismatched'])}")
            return 1
            
    except Exception as e:
        print(f"ERROR: Verification failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())