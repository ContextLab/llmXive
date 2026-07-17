"""Pytest configuration and fixtures for llmXive tests"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_project_root(monkeypatch):
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    yield
    sys.path.remove(str(project_root))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure"""
    raw = tmp_path / "data" / "raw"
    derived = tmp_path / "data" / "derived"
    validation = tmp_path / "data" / "validation"
    raw.mkdir(parents=True)
    derived.mkdir()
    validation.mkdir()
    return tmp_path
