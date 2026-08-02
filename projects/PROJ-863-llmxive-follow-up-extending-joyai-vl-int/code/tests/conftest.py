import pytest
import os
import sys
from pathlib import Path
import tempfile
import json
import resource

# Ensure project root is in path for imports
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

@pytest.fixture(scope="session", autouse=True)
def enforce_cpu_limits():
    """
    Enforce CPU resource limits for all tests to simulate the 6GB RAM / limited CPU constraint.
    This fixture runs once per session.
    """
    # Set soft/hard memory limit to 6GB (6 * 1024^3 bytes)
    # Note: resource limits are per-process. In CI, this might need adjustment.
    try:
        soft_limit = 6 * 1024 * 1024 * 1024  # 6GB
        hard_limit = 7 * 1024 * 1024 * 1024  # 7GB (buffer)
        resource.setrlimit(resource.RLIMIT_AS, (soft_limit, hard_limit))
    except (ValueError, resource.error) as e:
        # Ignore if running on Windows or non-Unix systems where RLIMIT_AS is not supported
        pytest.skip(f"Resource limits not supported on this platform: {e}")

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for data artifacts."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def temp_model_dir(tmp_path):
    """Create a temporary directory for model checkpoints."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    return model_dir

@pytest.fixture
def sample_manifest():
    """Provide a sample manifest structure for testing."""
    return {
        "version": "1.0",
        "total_frames": 100,
        "duration_seconds": 10.0,
        "chunks": [
            {"id": "chunk_0", "start_frame": 0, "end_frame": 50, "path": "data/chunk_0.jsonl"},
            {"id": "chunk_1", "start_frame": 50, "end_frame": 100, "path": "data/chunk_1.jsonl"}
        ]
    }

@pytest.fixture
def cpu_limit_marker():
    """
    Helper to verify a test is marked with cpu_limit.
    Usage: assert request.node.get_closest_marker("cpu_limit") is not None
    """
    return "cpu_limit"

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "cpu_limit: Marks tests that enforce CPU resource limits."
    )
    config.addinivalue_line(
        "markers", "slow: Marks tests that take longer than a threshold."
    )
    config.addinivalue_line(
        "markers", "unit: Marks unit tests."
    )
    config.addinivalue_line(
        "markers", "integration: Marks integration tests."
    )
    config.addinivalue_line(
        "markers", "data_gen: Marks data generation tests."
    )
    config.addinivalue_line(
        "markers", "baseline: Marks baseline detector tests."
    )
    config.addinivalue_line(
        "markers", "scheduler: Marks scheduler training/eval tests."
    )