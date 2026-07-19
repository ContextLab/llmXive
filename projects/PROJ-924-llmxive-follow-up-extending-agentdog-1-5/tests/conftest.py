import pytest
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

@pytest.fixture
def sample_config():
    return {"seed": 42, "batch_size": 32}
