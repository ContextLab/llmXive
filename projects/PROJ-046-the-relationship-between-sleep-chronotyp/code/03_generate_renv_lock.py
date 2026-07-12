"""
Script to generate renv.lock file for the R project.
This script initializes renv and records the dependencies defined in the project.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find the project root (where code/ is a sibling)
    while current.parent != current:
        if (current / "code").exists() and (current / "data").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root directory")

def check_r_installed():
    """Check if R is installed and accessible."""
    try:
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_r_version():
    """Get the installed R version."""
    try:
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        # Parse version from output (first line usually contains version)
        for line in result.stdout.split('\n'):
            if 'R version' in line:
                return line.split()[2]
        return None
    except Exception:
        return None

def initialize_renv(project_root):
    """Initialize renv in the project directory."""
    packages = [
        "tidyverse",
        "lme4",
        "car",
        "effectsize",
        "pwr",
        "rmarkdown",
        "knitr",
        "data.table",
        "testthat",
        "lintr"
    ]

    print("Initializing renv...")
    try:
        # Run R script to initialize renv and install packages
        r_script = f"""
        if (!requireNamespace("renv", quietly = TRUE)) {{
            install.packages("renv", repos = "https://cloud.r-project.org")
        }}
        renv::init()
        packages <- c({', '.join([f"'{p}'" for p in packages])})
        renv::install(packages)
        renv::snapshot()
        """
        
        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=300
        )
        print("renv initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing renv: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("Timeout initializing renv")
        return False

def verify_renv_lock(project_root):
    """Verify that renv.lock was created."""
    lock_file = project_root / "renv.lock"
    if not lock_file.exists():
        return False
    
    try:
        with open(lock_file, 'r') as f:
            content = f.read()
            # Basic validation that it looks like a JSON lock file
            json.loads(content)
            return True
    except json.JSONDecodeError:
        return False

def main():
    """Main entry point."""
    print("Starting renv.lock generation...")
    
    if not check_r_installed():
        print("ERROR: R is not installed or not in PATH. Please install R 4.3+ and try again.")
        sys.exit(1)
    
    r_version = get_r_version()
    if not r_version:
        print("ERROR: Could not determine R version.")
        sys.exit(1)
    
    print(f"Detected R version: {r_version}")
    
    # Check if version is 4.3 or higher
    major, minor = map(int, r_version.split('.')[:2])
    if major < 4 or (major == 4 and minor < 3):
        print(f"ERROR: R version {r_version} is too old. Please upgrade to R 4.3+.")
        sys.exit(1)
    
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    if not initialize_renv(project_root):
        print("ERROR: Failed to initialize renv.")
        sys.exit(1)
    
    if not verify_renv_lock(project_root):
        print("ERROR: renv.lock was not created or is invalid.")
        sys.exit(1)
    
    print("SUCCESS: renv.lock generated successfully at", project_root / "renv.lock")
    sys.exit(0)

if __name__ == "__main__":
    main()
