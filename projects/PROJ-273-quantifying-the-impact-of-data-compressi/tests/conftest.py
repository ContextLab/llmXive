import pytest
import sys
from pathlib import Path

# Add the project root to the path so imports work correctly
# This is crucial for running tests from the root directory
project_root = Path(__file__).parent.parent
src_path = project_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data artifacts."""
    return tmp_path_factory.mktemp("data")

@pytest.fixture
def sample_waveform():
    """Provide a simple sample waveform for testing compression/metrics."""
    import numpy as np
    t = np.linspace(0, 1, 1024)
    f = 50  # 50 Hz signal
    signal = np.sin(2 * np.pi * f * t)
    noise = np.random.normal(0, 0.01, len(t))
    return t, signal + noise
