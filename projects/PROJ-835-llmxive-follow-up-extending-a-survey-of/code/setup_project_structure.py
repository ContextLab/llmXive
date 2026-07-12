import os
import shutil
from pathlib import Path

def create_structure(base_path: str) -> None:
    """
    Creates the full project directory structure for the LlmXive follow-up study.
    
    Args:
        base_path: The root directory where the project structure will be created.
    """
    root = Path(base_path)
    
    # Define the directory tree to create
    dirs = [
        "code",
        "code/utils",
        "code/models",
        "code/data",
        "code/scripts",
        "data",
        "data/raw",
        "data/processed",
        "data/embeddings",
        "data/cache",
        "results",
        "results/metrics",
        "results/figures",
        "results/methodology_notes",
        "tests",
        "tests/unit",
        "tests/integration",
        "specs",
        "specs/001-llmxive-follow-up-extending-a-survey-of",
        "contracts",
        "figures",
        "logs"
    ]
    
    # Create directories
    for dir_path in dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep file to ensure empty directories are tracked by git
        (full_path / ".gitkeep").touch()
    
    # Create README.md
    readme_content = """# LlmXive Follow-up: Extending a Survey of Latent-Space Jailbreak Detection

This project implements the follow-up research to extend the survey on latent-space jailbreak detection.
It focuses on CPU-only embedding extraction, lightweight binary classification, and statistical validation.

## Project Structure

- `code/`: Source code for the pipeline
  - `utils/`: Utility functions (memory monitoring, logging, verification)
  - `models/`: Model training and evaluation scripts
  - `data/`: Data processing scripts (download, preprocess, extract)
  - `scripts/`: Entry point scripts for pipeline execution
- `data/`: Data storage
  - `raw/`: Original downloaded datasets
  - `processed/`: Cleaned and preprocessed data
  - `embeddings/`: Extracted feature embeddings
- `results/`: Output artifacts
  - `metrics/`: JSON metrics files
  - `figures/`: Generated plots and charts
  - `methodology_notes/`: Documentation of statistical deviations
- `tests/`: Unit and integration tests
- `specs/`: Research specifications and design documents
- `contracts/`: Data schemas and API contracts
- `figures/`: High-level project figures
- `logs/`: Execution logs

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run setup: `python code/setup_data_structure.py`
3. Execute pipeline: `python code/scripts/run_pipeline.py`

## Constraints

- CPU-only execution (no GPU)
- Memory limit: ~6.5 GB peak RAM
- Runtime limit: < 6 hours
- Real data only (no synthetic fabrication)
"""
    (root / "README.md").write_text(readme_content)
    
    # Create requirements.txt
    requirements_content = """transformers>=4.35.0
torch-cpu>=2.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
librosa>=0.10.0
datasets>=2.14.0
psutil>=5.9.0
pyyaml>=6.0.0
ruff>=0.1.0
black>=23.0.0
pytest>=7.4.0
"""
    (root / "requirements.txt").write_text(requirements_content)
    
    # Create .ruff.toml
    ruff_content = """[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "F401"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
    (root / ".ruff.toml").write_text(ruff_content)
    
    # Create pyproject.toml for Black and tool config
    pyproject_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-follow-up"
version = "0.1.0"
description = "LlmXive Follow-up: Latent-Space Jailbreak Detection"
requires-python = ">=3.9"

[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
"""
    (root / "pyproject.toml").write_text(pyproject_content)
    
    print(f"Project structure created successfully at: {root}")