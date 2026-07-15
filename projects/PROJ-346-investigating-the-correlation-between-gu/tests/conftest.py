"""
Root conftest.py for test discovery and shared fixtures.
This file ensures the code directory is on the Python path for imports.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root and code directory to sys.path
# This allows tests to import modules like `from 01_ingest import ...`
# without needing to run from the code directory specifically.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.fixture
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture
def code_dir(project_root):
    return project_root / "code"
