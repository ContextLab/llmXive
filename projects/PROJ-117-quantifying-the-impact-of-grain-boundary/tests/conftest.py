"""
Pytest configuration and shared fixtures for llmXive project.
"""
import os
import sys
from pathlib import Path
import pytest

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root))
    yield
    sys.path.remove(str(root))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data folders."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    models_dir = tmp_path / "models"
    artifacts_dir = tmp_path / "artifacts" / "reports"
    
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    models_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)
    
    return {
        "root": tmp_path,
        "raw": raw_dir,
        "processed": processed_dir,
        "models": models_dir,
        "reports": artifacts_dir,
    }
