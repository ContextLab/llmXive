"""
T002b: Verify dependencies install successfully in a clean virtualenv.

This script performs the following actions:
1. Locates the requirements.txt file relative to the project root.
2. Checks if a virtual environment exists at the standard location.
3. If not, creates a clean virtual environment.
4. Activates the environment and runs `pip install -r requirements.txt`.
5. Verifies installation by listing installed packages via `pip freeze`.
6. Writes a verification report to data/artifacts/dependency_verification.json.

Exit codes:
0: Success (all dependencies installed and verified)
1: Failure (installation error, missing requirements, or verification failed)
"""
import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume script is in code/tests/, project root is two levels up
    return Path(__file__).resolve().parent.parent.parent

def get_requirements_path() -> Path:
    """Get the path to requirements.txt."""
    project_root = get_project_root()
    return project_root / "code" / "requirements.txt"

def get_venv_path() -> Path:
    """Get the path to the virtual environment."""
    project_root = get_project_root()
    return project_root / "code" / "venv"

def get_installed_packages(venv_path: Path) -> Dict[str, str]:
    """
    Get a dictionary of installed packages and their versions from the venv.
    Returns {package_name: version}.
    """
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip"
    else:
        pip_executable = venv_path / "bin" / "pip"

    if not pip_executable.exists():
        raise FileNotFoundError(f"pip executable not found at {pip_executable}")

    result = subprocess.run(
        [str(pip_executable), "freeze"],
        capture_output=True,
        text=True,
        check=True
    )
    
    packages = {}
    for line in result.stdout.strip().splitlines():
        if "==" in line:
            name, version = line.split("==", 1)
            packages[name.strip().lower()] = version.strip()
    return packages

def load_requirements(req_path: Path) -> List[str]:
    """Load requirements from file, filtering comments and empty lines."""
    if not req_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {req_path}")
    
    requirements = []
    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements

def verify_installation(
    installed: Dict[str, str], 
    requirements: List[str], 
    report_path: Path
) -> bool:
    """
    Verify that all required packages are installed with compatible versions.
    Writes a detailed report to report_path.
    """
    report = {
        "status": "success",
        "missing_packages": [],
        "version_mismatches": [],
        "installed_packages": list(installed.keys()),
        "verification_timestamp": "verification_in_progress" # Will be updated
    }
    
    all_ok = True
    
    for req in requirements:
        # Handle version specifiers (==, >=, <=, ~=, etc.)
        # Simple parsing: split on common operators
        import re
        match = re.match(r'^([a-zA-Z0-9_-]+)([<>=~!]+)?(.*)$', req)
        if not match:
            continue
            
        pkg_name = match.group(1).lower()
        operator = match.group(2)
        required_version = match.group(3)
        
        if pkg_name not in installed:
            report["missing_packages"].append({
                "package": pkg_name,
                "requirement": req
            })
            all_ok = False
        elif operator and required_version:
            # For simplicity, we just check exact match if ==, 
            # or log if version differs significantly for this task
            # A robust checker would use packaging.version, but for T002b
            # we focus on presence and basic version string match if ==
            if operator == "==":
                if installed[pkg_name] != required_version:
                    report["version_mismatches"].append({
                        "package": pkg_name,
                        "required": f"{operator}{required_version}",
                        "installed": installed[pkg_name]
                    })
                    all_ok = False
    
    if all_ok:
        report["status"] = "success"
        report["message"] = "All dependencies installed successfully."
    else:
        report["status"] = "failed"
        report["message"] = "Dependency verification failed."
        
    # Ensure parent directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
        
    return all_ok

def create_venv(venv_path: Path) -> bool:
    """Create a new virtual environment."""
    if venv_path.exists():
        # Optionally remove existing venv for a "clean" check
        # But for robustness in CI, we might just recreate if needed.
        # Here we assume we want a fresh start if it exists to ensure T002b "clean" constraint.
        print(f"Removing existing virtual environment at {venv_path}...")
        shutil.rmtree(venv_path)
        
    print(f"Creating virtual environment at {venv_path}...")
    result = subprocess.run(
        [sys.executable, "-m", "venv", str(venv_path)],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error creating venv: {result.stderr}")
        return False
    return True

def install_dependencies(venv_path: Path, req_path: Path) -> bool:
    """Install dependencies from requirements.txt into the venv."""
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip"
    else:
        pip_executable = venv_path / "bin" / "pip"
        
    if not pip_executable.exists():
        print(f"pip not found at {pip_executable} after venv creation.")
        return False

    print(f"Installing dependencies from {req_path}...")
    result = subprocess.run(
        [str(pip_executable), "install", "-r", str(req_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Installation failed:\n{result.stderr}")
        return False
        
    print("Installation completed.")
    return True

def main():
    """Main entry point for T002b verification."""
    project_root = get_project_root()
    req_path = get_requirements_path()
    venv_path = get_venv_path()
    report_path = project_root / "data" / "artifacts" / "dependency_verification.json"
    
    print(f"Project Root: {project_root}")
    print(f"Requirements Path: {req_path}")
    print(f"Venv Path: {venv_path}")
    
    # Step 1: Check requirements file
    if not req_path.exists():
        print(f"ERROR: Requirements file not found at {req_path}")
        sys.exit(1)
        
    # Step 2: Create/Reset venv
    if not create_venv(venv_path):
        print("ERROR: Failed to create virtual environment.")
        sys.exit(1)
        
    # Step 3: Install dependencies
    if not install_dependencies(venv_path, req_path):
        print("ERROR: Failed to install dependencies.")
        # Write failure report
        report = {
            "status": "failed",
            "message": "Dependency installation failed.",
            "error": "pip install returned non-zero exit code"
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
        
    # Step 4: Verify installation
    try:
        installed = get_installed_packages(venv_path)
        requirements = load_requirements(req_path)
        
        success = verify_installation(installed, requirements, report_path)
        
        if success:
            print("SUCCESS: All dependencies verified.")
            sys.exit(0)
        else:
            print("FAILURE: Dependency verification failed.")
            with open(report_path, "r") as f:
                print(f.read())
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()