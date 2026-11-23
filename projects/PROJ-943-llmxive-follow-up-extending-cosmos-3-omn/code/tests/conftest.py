"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield
    # Optional: cleanup if needed, though path insertion is persistent for session

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure mimicking the project data layout."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        (base / "raw").mkdir()
        (base / "processed").mkdir()
        (base / "splits").mkdir()
        yield base

@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for model artifacts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        base.mkdir(parents=True, exist_ok=True)
        yield base

@pytest.fixture
def sample_schema():
    """Return a sample action schema dictionary for testing."""
    return {
        "norm_threshold": 0.5,
        "text_keywords": ["Safety Constraint"],
        "composite_operator": "AND",
        "vector_dimensions": 3
    }

@pytest.fixture
def sample_action_vector():
    """Return a sample action vector."""
    return [0.8, 0.6, 0.0, 0.1, 0.2]

@pytest.fixture
def sample_text_context():
    """Return a sample text context."""
    return "The robot is moving with a Safety Constraint applied."
