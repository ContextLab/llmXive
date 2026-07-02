import os
import json

def create_directories(base_path):
    """Create the standard directory structure for the research project."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "logs",
        "code",
        "tests",
        "reports",
        "specs"
    ]
    for d in dirs:
        path = os.path.join(base_path, d)
        os.makedirs(path, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked in git
        with open(os.path.join(path, ".gitkeep"), "w") as f:
            f.write("")

def create_gitignore(base_path):
    """Create a .gitignore file for the project."""
    gitignore_content = """# R
.Rhistory
.Rdata
.RData
*.Rproj.user
.Rproj
renv/
renv.lock
# Logs
logs/
*.log
# Data
data/raw/*.csv
data/raw/*.tsv
data/raw/*.xlsx
# Generated files
data/processed/*.csv
data/derived/*.csv
data/derived/*.json
data/derived/*.rds
reports/*.html
reports/*.pdf
figures/
__pycache__/
*.pyc
*.pyo
.env
venv/
"""
    with open(os.path.join(base_path, ".gitignore"), "w") as f:
        f.write(gitignore_content)

def create_readme(base_path):
    """Create a README.md for the project."""
    readme_content = """# PROJ-046: The Relationship Between Sleep Chronotype and Moral Judgement

## Overview
This project investigates the relationship between sleep chronotype (measured by MEQ and MFQ) and moral judgment.

## Directory Structure
- `data/raw/`: Raw, unmodified input data (user-provided)
- `data/processed/`: Cleaned and preprocessed data
- `data/derived/`: Intermediate and final analysis results
- `code/`: R scripts for data processing and analysis
- `tests/`: Unit and integration tests
- `reports/`: Final R Markdown reports
- `specs/`: Feature specifications and design documents
- `logs/`: Pipeline execution logs

## Prerequisites
- R 4.3+
- renv

## Setup
1. Clone the repository.
2. Run `Rscript code/setup_project_structure.py` (if running from Python environment) or manually ensure directories exist.
3. Install R dependencies: `Rscript -e "renv::restore()"`

## Execution
Run the pipeline in order:
1. `Rscript code/01_ingest.R`
2. `Rscript code/02_classify.R`
3. `Rscript code/02.5_aggregate_exclusions.R`
4. `Rscript code/03_analysis.R`
5. `Rscript code/04_report.Rmd`
"""
    with open(os.path.join(base_path, "README.md"), "w") as f:
        f.write(readme_content)

def create_requirements_txt(base_path):
    """Create a requirements.txt for Python dependencies (if any)."""
    # Currently minimal, but good practice for mixed environments
    with open(os.path.join(base_path, "requirements.txt"), "w") as f:
        f.write("# No Python dependencies required for core pipeline\n")
        f.write("# R dependencies are managed via renv\n")

def create_r_profile(base_path):
    """Create a .Rprofile to set up the project environment."""
    r_profile_content = """# R Profile for PROJ-046
if (file.exists("renv.lock")) {
  renv::load()
}
"""
    with open(os.path.join(base_path, ".Rprofile"), "w") as f:
        f.write(r_profile_content)

def main():
    # Determine base path: if running from 'code/', go up one level
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Creating project structure in: {base_path}")
    
    create_directories(base_path)
    create_gitignore(base_path)
    create_readme(base_path)
    create_requirements_txt(base_path)
    create_r_profile(base_path)
    
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()