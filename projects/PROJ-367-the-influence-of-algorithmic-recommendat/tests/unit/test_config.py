"""
Tests for configuration and project structure.
"""
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import (
    PROJECT_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    FIGURES_DIR,
    SIMILARITY_THRESHOLD_DEFAULT,
    REQUIRED_COLUMNS,
    MIN_SAMPLE_SIZE_FOR_PSW
)

def test_project_root_exists():
    assert PROJECT_ROOT.exists(), "Project root directory must exist."

def test_directories_exist():
    assert DATA_DIR.exists(), "Data directory must exist."
    assert PROCESSED_DIR.exists(), "Processed directory must exist."
    assert FIGURES_DIR.exists(), "Figures directory must exist."

def test_constants_defined():
    assert SIMILARITY_THRESHOLD_DEFAULT > 0
    assert len(REQUIRED_COLUMNS) > 0
    assert MIN_SAMPLE_SIZE_FOR_PSW > 0