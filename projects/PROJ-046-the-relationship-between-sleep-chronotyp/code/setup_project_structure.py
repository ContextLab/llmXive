import os
import json

# Define the project root relative to this file or use current working directory
# The task specifies the project root as `projects/PROJ-046-the-relationship-between-sleep-chronotyp/`
PROJECT_ROOT = "projects/PROJ-046-the-relationship-between-sleep-chronotyp"

def create_directories():
    """Create the required directory structure for the project."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/derived",
        "logs",
        "code",
        "tests",
        "reports",
        "specs",
        "figures"
    ]
    
    for d in dirs:
        path = os.path.join(PROJECT_ROOT, d)
        os.makedirs(path, exist_ok=True)
        print(f"Created directory: {path}")

def create_gitignore():
    """Create a .gitignore file tailored for R and data science projects."""
    gitignore_content = """# R specific
.Rhistory
.Rdata
.RData
.Rproj.user
.Rcheck
*.Rout
*.Rout.save

# Python specific
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Data specific (keeping raw data out of git)
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
data/derived/*
!data/derived/.gitkeep

# Logs
logs/*
!logs/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
    path = os.path.join(PROJECT_ROOT, ".gitignore")
    with open(path, "w") as f:
        f.write(gitignore_content)
    print(f"Created file: {path}")

def create_readme():
    """Create a README.md with project overview and setup instructions."""
    readme_content = """# The Relationship Between Sleep Chronotype and Moral Judgement

## Project Overview
This project investigates the relationship between sleep chronotype (MEQ, MFQ) and moral judgment, controlling for sleep quality (PSQI) and acute sleepiness.

## Directory Structure
- `data/raw/`: Raw input data (user-provided CSVs)
- `data/processed/`: Cleaned and preprocessed data
- `data/derived/`: Analysis results, metrics, and models
- `logs/`: Execution logs and exclusion records
- `code/`: R and Python scripts for analysis
- `tests/`: Unit and integration tests
- `reports/`: Final R-Markdown reports
- `figures/`: Generated plots and charts

## Prerequisites
- R 4.3+
- Python 3.9+
- `renv` (for R dependency management)

## Setup
1. Run the setup script to initialize directories:
   ```bash
   python code/setup_project_structure.py
   ```
2. Initialize R environment:
   ```bash
   Rscript -e "renv::init()"
   ```

## Data Source Strategy
**Note**: This project currently relies on user-provided merged datasets as per Plan.md. 
The spec assumption regarding Prolific integration is flagged for plan update.
Raw data must be placed in `data/raw/` before running analysis scripts.
"""
    path = os.path.join(PROJECT_ROOT, "README.md")
    with open(path, "w") as f:
        f.write(readme_content)
    print(f"Created file: {path}")

def create_requirements_txt():
    """Create a requirements.txt for Python dependencies."""
    requirements_content = """# Python dependencies for the analysis pipeline
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
pytest>=7.0.0
"""
    path = os.path.join(PROJECT_ROOT, "requirements.txt")
    with open(path, "w") as f:
        f.write(requirements_content)
    print(f"Created file: {path}")

def create_r_profile():
    """Create an .Rprofile to set up the R environment."""
    rprofile_content = """# R profile for PROJ-046
# Set working directory relative to project root if needed
# options(repos = c(CRAN = "https://cran.r-project.org"))

# Load renv if available
if (file.exists("renv/activate.R")) {
  source("renv/activate.R")
}

# Suppress specific warnings for cleaner logs
# options(warn = 1)
"""
    path = os.path.join(PROJECT_ROOT, ".Rprofile")
    with open(path, "w") as f:
        f.write(rprofile_content)
    print(f"Created file: {path}")

def main():
    """Main entry point to create the project structure."""
    print(f"Initializing project structure at: {PROJECT_ROOT}")
    if not os.path.exists(PROJECT_ROOT):
        os.makedirs(PROJECT_ROOT)
        print(f"Created root directory: {PROJECT_ROOT}")
    
    create_directories()
    create_gitignore()
    create_readme()
    create_requirements_txt()
    create_r_profile()
    
    # Create .gitkeep files to ensure empty directories are tracked by git
    keep_dirs = [
        "data/raw", "data/processed", "data/derived", 
        "logs", "figures", "reports"
    ]
    for d in keep_dirs:
        path = os.path.join(PROJECT_ROOT, d, ".gitkeep")
        with open(path, "w") as f:
            f.write("")
        print(f"Created keep file: {path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()