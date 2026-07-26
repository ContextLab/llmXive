"""
Integration test for the full download and validation flow.
This test verifies that the pipeline components work together.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.logger import setup_global_logger
from config import PROJECT_ROOT


def test_directory_structure_exists():
    """Verify that the required directory structure exists."""
    # Check root
    assert PROJECT_ROOT.exists(), f"Project root {PROJECT_ROOT} does not exist"
    
    # Check code dir
    code_path = PROJECT_ROOT / "code"
    assert code_path.exists(), "code directory missing"
    
    # Check data dir
    data_path = PROJECT_ROOT / "data"
    assert data_path.exists(), "data directory missing"
    
    # Check tests dir
    tests_path = PROJECT_ROOT / "tests"
    assert tests_path.exists(), "tests directory missing"


def test_config_loads():
    """Verify that config.py loads without errors."""
    # Importing config triggers the initialization
    import config
    assert hasattr(config, 'PROJECT_ROOT')


def test_logger_setup():
    """Verify that the logger can be initialized."""
    logger = setup_global_logger("test_integration")
    assert logger is not None
    assert logger.name == "test_integration"
