"""
Script to initialize R 4.3+ project with renv and required dependencies.

This script:
1. Checks for R 4.3+ installation
2. Initializes renv in the project directory
3. Installs all required packages
4. Generates renv.lock file
"""
import os
import sys
import subprocess
from utils_renv import check_r_version, initialize_renv

def main():
    """Main entry point for R environment setup."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_packages = [
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
    
    print("=" * 60)
    print("R Project Initialization Script")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print()
    
    # Check R version
    print("Step 1: Checking R version...")
    if not check_r_version("4.3.0"):
        print("ERROR: R version 4.3.0 or higher is required.")
        print("Please install R 4.3+ from https://cran.r-project.org/")
        sys.exit(1)
    print("✓ R version check passed")
    print()
    
    # Initialize renv and install packages
    print("Step 2: Initializing renv and installing packages...")
    print(f"Required packages: {', '.join(required_packages)}")
    
    if initialize_renv(project_root, required_packages):
        print("✓ R environment initialized successfully")
        print("✓ All required packages installed")
        print("✓ renv.lock file generated")
        print()
        print("Next steps:")
        print("  - Run R scripts with: Rscript <script>.R")
        print("  - Packages will be loaded from renv cache automatically")
        print("  - To restore environment on new machine: R -e 'renv::restore()'")
    else:
        print("ERROR: Failed to initialize R environment.")
        sys.exit(1)

if __name__ == "__main__":
    main()