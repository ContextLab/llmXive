import pytest
from pathlib import Path
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.fixture
def test_data_dir(project_root):
    data_dir = project_root / "data" / "integration_tests"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
