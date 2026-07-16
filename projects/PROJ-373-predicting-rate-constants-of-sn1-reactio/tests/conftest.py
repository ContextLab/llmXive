import pytest
import os
import sys
from pathlib import Path

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture(scope="session")
def artifacts_dir(project_root):
    return project_root / "artifacts"

@pytest.fixture(scope="session")
def specs_dir(project_root):
    return project_root / "specs" / "001-predict-sn1-rate-constants"
