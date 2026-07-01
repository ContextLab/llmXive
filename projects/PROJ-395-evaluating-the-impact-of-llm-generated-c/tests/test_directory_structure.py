import os
import pytest

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects", "PROJ-395-evaluating-the-impact-of-llm-generated-c")

def test_project_directory_structure_exists():
    """Verify that the main project directory and subdirectories exist."""
    assert os.path.isdir(PROJECT_ROOT), f"Project root {PROJECT_ROOT} does not exist"

    required_dirs = ["data", "code", "tests", "state"]
    for dir_name in required_dirs:
        dir_path = os.path.join(PROJECT_ROOT, dir_name)
        assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

def test_data_subdirectories_exist():
    """Verify that data/raw and data/processed directories exist."""
    data_raw = os.path.join(PROJECT_ROOT, "data", "raw")
    data_processed = os.path.join(PROJECT_ROOT, "data", "processed")

    assert os.path.isdir(data_raw), f"Directory {data_raw} does not exist"
    assert os.path.isdir(data_processed), f"Directory {data_processed} does not exist"

def test_requirements_txt_exists():
    """Verify that requirements.txt exists in the project root."""
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    assert os.path.isfile(req_path), f"File {req_path} does not exist"

def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists for linting/formatting config."""
    config_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    assert os.path.isfile(config_path), f"File {config_path} does not exist"