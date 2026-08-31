"""
Project Initialization Script for PROJ-240
Creates the required directory structure and configuration files.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the current working directory
    # The task specifies the project is at projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/
    # We assume the script is run from the repository root or the project root.
    # We will create the structure relative to the current execution context.
    
    # Base directory for the project
    base_dir = Path("projects/PROJ-240-predicting-the-impact-of-cold-work-on-re")
    
    # 1. Create root directories: code, tests, data, artifacts
    root_dirs = ["code", "tests", "data", "artifacts"]
    for dir_name in root_dirs:
        dir_path = base_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # 2. Create data subdirectories: raw, processed, split
    data_subdirs = ["raw", "processed", "split"]
    data_base = base_dir / "data"
    for dir_name in data_subdirs:
        dir_path = data_base / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # 3. Create artifacts subdirectories: models, reports, figures
    artifact_subdirs = ["models", "reports", "figures"]
    artifact_base = base_dir / "artifacts"
    for dir_name in artifact_subdirs:
        dir_path = artifact_base / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # 4. Create pyproject.toml with ruff and black configuration
    pyproject_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "proj-240-cold-work-recrystallization"
version = "0.1.0"
description = "Predicting the impact of cold work on recrystallization kinetics in aluminum alloys"
requires-python = ">=3.9"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "scikit-learn>=1.3.0",
    "statsmodels>=0.14.0",
    "shap>=0.43.0",
    "pytest>=7.0.0",
]

[tool.setuptools.packages.find]
where = ["code"]

[tool.black]
line-length = 88
target-version = ['py39']

[tool.ruff]
line-length = 88
select = ["E", "W", "F"]
ignore = []
target-version = "py39"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
"""
    
    pyproject_path = base_dir / "pyproject.toml"
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(pyproject_content)
    print(f"Created configuration file: {pyproject_path}")

    # 5. Create .env file with N_PERMUTATIONS
    env_content = """# Environment Configuration for PROJ-240
# Statistical Test Parameters
N_PERMUTATIONS=1000

# Random Seed for Reproducibility
RANDOM_SEED=42

# Data Paths (relative to project root)
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed
DATA_SPLIT_DIR=data/split
ARTIFACTS_MODELS_DIR=artifacts/models
ARTIFACTS_REPORTS_DIR=artifacts/reports
ARTIFACTS_FIGURES_DIR=artifacts/figures
"""
    
    env_path = base_dir / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f"Created environment file: {env_path}")

    # 6. Create requirements.txt
    requirements_content = """pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
statsmodels>=0.14.0
shap>=0.43.0
pytest>=7.0.0
black>=23.0.0
ruff>=0.1.0
python-dotenv>=1.0.0
"""
    
    req_path = base_dir / "requirements.txt"
    with open(req_path, "w", encoding="utf-8") as f:
        f.write(requirements_content)
    print(f"Created requirements file: {req_path}")

    print("\nProject structure initialization complete.")
    print(f"Root directory: {base_dir}")

if __name__ == "__main__":
    main()