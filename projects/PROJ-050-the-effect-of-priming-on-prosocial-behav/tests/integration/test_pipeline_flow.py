"""
Integration tests for pipeline flow.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import DATA_PROCESSED_DIR

def test_directories_created():
    """Verifies that the directory structure is created."""
    assert DATA_PROCESSED_DIR.exists()
    assert (DATA_PROCESSED_DIR / "anonymized.csv").parent.exists()

def test_requirements_exist():
    """Verifies requirements.txt exists."""
    req_path = Path(__file__).parent.parent.parent / "code" / "requirements.txt"
    assert req_path.exists()
