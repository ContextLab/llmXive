"""
Basic setup verification tests.
Ensures project structure and dependencies are correctly initialized.
"""
import pytest
import os
import sys
from pathlib import Path

def test_project_structure_exists():
    """Verify that key project directories exist."""
    project_root = Path(__file__).parent.parent
    assert (project_root / "code").exists(), "code/ directory missing"
    assert (project_root / "data").exists(), "data/ directory missing"
    assert (project_root / "tests").exists(), "tests/ directory missing"

def test_requirements_txt_exists():
    """Verify requirements.txt is present."""
    project_root = Path(__file__).parent.parent
    assert (project_root / "requirements.txt").exists(), "requirements.txt missing"

def test_pyproject_toml_exists():
    """Verify pyproject.toml is present."""
    project_root = Path(__file__).parent.parent
    assert (project_root / "pyproject.toml").exists(), "pyproject.toml missing"

def test_config_imports_successfully():
    """Verify code/config.py can be imported and has required attributes."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import code.config as config
    
    assert hasattr(config, "PROJECT_ROOT")
    assert hasattr(config, "DATA_DIR")
    assert hasattr(config, "SEED")
    assert hasattr(config, "OPENNEURO_DATASET_ID")
    assert config.OPENNEURO_DATASET_ID == "ds000234"

def test_dependencies_importable():
    """Verify core dependencies can be imported."""
    import numpy
    import pandas
    import nilearn
    import sklearn
    import torch
    import transformers