"""
Utility functions for managing R environment and renv.
"""
import subprocess
import sys
import os
import json
from typing import List, Optional
from pathlib import Path

def check_r_version(min_version: str = "4.3.0") -> bool:
    """
    Check if R is installed and meets minimum version requirements.
    
    Args:
        min_version: Minimum required R version (default: 4.3.0)
    
    Returns:
        True if R meets version requirements, False otherwise
    """
    try:
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        # Parse version from output
        for line in result.stdout.split('\n'):
            if 'R version' in line:
                version = line.split()[2]
                major, minor, patch = map(int, version.split('.')[:3])
                min_major, min_minor, min_patch = map(int, min_version.split('.'))
                
                if major > min_major:
                    return True
                if major == min_major and minor > min_minor:
                    return True
                if major == min_major and minor == min_minor and patch >= min_patch:
                    return True
                return False
        
        return False
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False

def verify_packages(packages: List[str]) -> bool:
    """
    Verify that specified R packages are installed.
    
    Args:
        packages: List of package names to verify
    
    Returns:
        True if all packages are installed, False otherwise
    """
    r_script = f"""
    packages <- c({', '.join([f"'{p}'" for p in packages])})
    missing <- packages[!sapply(packages, requireNamespace, quietly = TRUE)]
    if (length(missing) > 0) {{
        quit(status = 1)
    }}
    """
    
    try:
        result = subprocess.run(
            ["Rscript", "-e", r_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

def initialize_renv(project_root: Path, packages: List[str]) -> bool:
    """
    Initialize renv in the project directory and install specified packages.
    
    Args:
        project_root: Path to the project root directory
        packages: List of packages to install
    
    Returns:
        True if initialization was successful, False otherwise
    """
    r_script = f"""
    if (!requireNamespace("renv", quietly = TRUE)) {{
        install.packages("renv", repos = "https://cloud.r-project.org")
    }}
    renv::init()
    packages <- c({', '.join([f"'{p}'" for p in packages])})
    renv::install(packages)
    renv::snapshot()
    """
    
    try:
        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
            timeout=300
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Error initializing renv: {e}")
        return False

def main():
    """Main entry point for command line usage."""
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
    
    if not check_r_version():
        print("ERROR: R 4.3+ is required but not found.")
        sys.exit(1)
    
    if not verify_packages(packages):
        print("Some packages are missing. Attempting to initialize renv...")
        
        # Find project root
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / "code").exists() and (current / "data").exists():
                project_root = current
                break
            current = current.parent
        else:
            print("ERROR: Could not find project root")
            sys.exit(1)
        
        if not initialize_renv(project_root, packages):
            print("ERROR: Failed to initialize renv.")
            sys.exit(1)
        
        if not verify_packages(packages):
            print("ERROR: Failed to install required packages.")
            sys.exit(1)
    
    print("SUCCESS: R environment verified and ready.")

if __name__ == "__main__":
    main()