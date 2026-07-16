"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the code/src directory to the path so imports work
# This ensures that 'from src.config import ...' works in tests
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up test environment variables if needed."""
    # Ensure we're not using production data paths
    os.environ.setdefault("PROJECT_ROOT", str(current_dir.parent))
    yield
    # Cleanup if needed
    pass

@pytest.fixture
def sample_waveform_data():
    """Provide sample waveform data for testing."""
    import numpy as np
    # Create a simple sine wave as sample data
    fs = 4096
    t = np.linspace(0, 1, fs)
    signal = np.sin(2 * np.pi * 100 * t)  # 100 Hz sine wave
    return {"signal": signal, "fs": fs, "duration": 1.0}

@pytest.fixture
def sample_injection_metadata():
    """Provide sample injection metadata."""
    return {
        "injection_id": "test_001",
        "resolution": 4096,
        "snr": 12.5,
        "mass1": 30.0,
        "mass2": 20.0,
        "distance": 200.0
    }

@pytest.fixture
def mock_schema_content():
    """Provide a mock JSON schema for testing."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["id", "name"]
    }