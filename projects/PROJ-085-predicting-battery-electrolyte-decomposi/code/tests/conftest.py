import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, List, Dict, Any
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def output_dir() -> Path:
    """Return the path to the output directory."""
    return project_root / "data" / "processed"

@pytest.fixture
def sample_dataset(tmp_path: Path) -> Path:
    """Create a temporary sample dataset file."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("id,value\n1,10.0\n2,20.0\n3,30.0\n")
    return csv_path

@pytest.fixture
def schema_validator() -> Dict[str, Any]:
    """Return a sample schema validator configuration."""
    return {
        "type": "object",
        "properties": {
            "molecule_id": {"type": "string"},
            "potential_v": {"type": "integer"},
            "decomp_energy": {"type": "number"}
        },
        "required": ["molecule_id", "potential_v"]
    }

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "contract: marks tests as contract validation tests"
    )
