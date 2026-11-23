import os
import sys
import configparser
import toml
import logging
from datetime import datetime
from utils import setup_logging, get_logger, set_task_id, get_unique_id

def check_file_exists(path: str) -> bool:
    """Check if a file exists."""
    return os.path.isfile(path)

def validate_flake8_config():
    """Create .flake8 config if missing."""
    config_path = ".flake8"
    if not check_file_exists(config_path):
        with open(config_path, "w") as f:
            f.write("[flake8]\n")
            f.write("max-line-length = 88\n")
            f.write("ignore = E203, W503\n")
        logging.info(f"Created {config_path}")
    else:
        logging.info(f"{config_path} already exists")

def validate_pyproject_config():
    """Create pyproject.toml with black config if missing."""
    config_path = "pyproject.toml"
    if not check_file_exists(config_path):
        with open(config_path, "w") as f:
            f.write("[tool.black]\n")
            f.write("line-length = 88\n")
            f.write("target-version = ['py38']\n")
        logging.info(f"Created {config_path}")
    else:
        logging.info(f"{config_path} already exists")

def update_requirements():
    """Ensure requirements.txt exists (T002)."""
    req_path = "code/requirements.txt"
    if not check_file_exists(req_path):
        os.makedirs(os.path.dirname(req_path), exist_ok=True)
        with open(req_path, "w") as f:
            f.write("# Dependencies\n")
            f.write("datasets>=2.0.0\n")
            f.write("pandas>=1.5.0\n")
            f.write("pyarrow>=10.0.0\n")
            f.write("matplotlib>=3.5.0\n")
            f.write("scipy>=1.9.0\n")
            f.write("statsmodels>=0.13.0\n")
            f.write("radon>=6.0.0\n")
            f.write("transformers>=4.25.0\n")
            f.write("torch>=1.13.0\n")
            f.write("accelerate>=0.15.0\n")
        logging.info(f"Created {req_path}")
    else:
        logging.info(f"{req_path} already exists")

def main():
    """T003: Configure linting (flake8/black)."""
    logger = setup_logging(task_id="T003")
    logger.info("Setting up linting configuration...")
    
    validate_flake8_config()
    validate_pyproject_config()
    update_requirements()
    
    logger.info("Linting configuration complete.")

if __name__ == "__main__":
    main()
