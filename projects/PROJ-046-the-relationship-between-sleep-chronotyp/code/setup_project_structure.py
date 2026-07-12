import os
import json

def create_directories(base_path: str) -> None:
    """Create the required project directory structure."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "logs",
        "code",
        "tests",
        "reports",
        "figures",
        "docs",
        "specs",
    ]
    for d in dirs:
        full_path = os.path.join(base_path, d)
        os.makedirs(full_path, exist_ok=True)

def create_gitignore(base_path: str) -> None:
    """Create a .gitignore file with standard R and data science rules."""
    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# R
.Rhistory
.RData
.Rproj.user
renv/activate.R
renv/profiles/*/activate.R

# Data (Keep raw, ignore derived if large, keep logs)
data/raw/*
!data/raw/.gitkeep
data/processed/*.csv
data/derived/*.csv
data/derived/*.json
data/derived/*.log
logs/*.log
logs/*.flag

# Reports
reports/*.html
reports/*.pdf
reports/*.docx

# Figures
figures/*.png
figures/*.jpg
figures/*.pdf

# IDE
.vscode/
.idea/
*.swp
*.swo
"""
    file_path = os.path.join(base_path, ".gitignore")
    with open(file_path, "w") as f:
        f.write(content)

def create_readme(base_path: str) -> None:
    """Create a README.md with project context and the required data source flag."""
    content = """# PROJ-046: The Relationship Between Sleep Chronotype and Moral Judgement

## Overview
This project investigates the correlation between sleep chronotype (MEQ/MFQ) and moral judgment (MFQ subscales).

## Data Source Strategy
**CRITICAL FLAG**: The project specification assumes a Prolific integration for data collection.
However, the implementation plan (plan.md) specifies **user-provided data** ingestion.
This contradiction must be resolved before data ingestion tasks begin.
- Current Implementation Plan: User-provided CSVs in `data/raw/`
- Spec Assumption: Prolific API integration
- Action Required: Update plan.md to confirm data source strategy.

## Directory Structure
- `data/raw/`: Raw input files (user-provided or downloaded)
- `data/processed/`: Cleaned and validated data
- `data/derived/`: Analysis results and metrics
- `logs/`: Execution logs and exclusion records
- `code/`: R and Python scripts
- `reports/`: Final analysis reports
"""
    file_path = os.path.join(base_path, "README.md")
    with open(file_path, "w") as f:
        f.write(content)

def create_requirements_txt(base_path: str) -> None:
    """Create a requirements.txt for Python dependencies."""
    content = """# Data processing and analysis
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
statsmodels>=0.14.0
matplotlib>=3.7.0
seaborn>=0.12.0

# Utilities
tqdm>=4.65.0
"""
    file_path = os.path.join(base_path, "requirements.txt")
    with open(file_path, "w") as f:
        f.write(content)

def create_r_profile(base_path: str) -> None:
    """Create a basic .Rprofile for the project."""
    content = """# Project specific R configuration
options(stringsAsFactors = FALSE)
"""
    file_path = os.path.join(base_path, ".Rprofile")
    with open(file_path, "w") as f:
        f.write(content)

def main() -> None:
    """Entry point to initialize the project structure."""
    # Determine base path: if running from project root, assume current dir
    # If running from code/, go up one level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Check if we are in code/
    if os.path.basename(script_dir) == "code":
        base_path = os.path.dirname(script_dir)
    else:
        base_path = script_dir

    print(f"Initializing project structure at: {base_path}")
    create_directories(base_path)
    create_gitignore(base_path)
    create_readme(base_path)
    create_requirements_txt(base_path)
    create_r_profile(base_path)
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()
