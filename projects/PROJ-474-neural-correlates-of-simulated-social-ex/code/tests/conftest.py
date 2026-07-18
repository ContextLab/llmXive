"""
Pytest configuration and fixtures.
"""
import os
import sys
import pytest
from pathlib import Path
import random
import numpy as np

# Add project root to path
@pytest.fixture(autouse=True)
def setup_environment():
    """Set up the environment for tests."""
    # Ensure reproducibility
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Add code directory to path
    code_dir = Path(__file__).parent.parent / "code"
    sys.path.insert(0, str(code_dir))

    # Create necessary directories if they don't exist
    (code_dir / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (code_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
    (code_dir / "data" / "results").mkdir(parents=True, exist_ok=True)
    (code_dir / "src").mkdir(parents=True, exist_ok=True)
    (code_dir / "tests").mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup if needed
    sys.path.remove(str(code_dir))

@pytest.fixture
def sample_events_content():
    """Provide sample events.tsv content with valid markers."""
    return (
        "onset\tduration\ttrial_type\tcondition\n"
        "10\t2\tInclusion\tInclusion\n"
        "20\t2\tExclusion\tExclusion\n"
        "30\t2\tInclusion\tInclusion\n"
    )

@pytest.fixture
def sample_events_content_invalid():
    """Provide sample events.tsv content with missing markers."""
    return (
        "onset\tduration\ttrial_type\tcondition\n"
        "10\t2\tNeutral\tNeutral\n"
    )