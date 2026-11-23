"""
Script to create empty project files (requirements.txt, pytest.ini, etc.).
This implements T001b and T001c logic, but T001a specifically asks for directories.
This file ensures the structure is fully set up.
"""
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_directories() -> None:
    """Create required directories."""
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala"
    ]
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")

def create_empty_files() -> None:
    """Create empty project configuration files."""
    files = {
        "code/requirements.txt": "# Dependencies\nnumpy\npandas\nscikit-learn\nrequests\ntorch\ndatasets\n",
        ".gitignore": "data/raw/\ndata/processed/\nresults/\nfigures/\n__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.Python\nenv/\nvenv/\n*.egg-info/\n",
        "pytest.ini": "[pytest]\npython_files = test_*.py\naddopts = -v --tb=short\n",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/requirements.txt": "# Project specific deps\n",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/.gitignore": "data/\nresults/\n",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/pytest.ini": "[pytest]\npython_files = test_*.py\naddopts = -v\n"
    }

    for file_path, content in files.items():
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content)
            logger.info(f"Created file: {path}")
        else:
            logger.info(f"File already exists: {path}")

def main() -> None:
    setup_directories()
    create_empty_files()
    logger.info("Project setup complete.")

if __name__ == "__main__":
    main()