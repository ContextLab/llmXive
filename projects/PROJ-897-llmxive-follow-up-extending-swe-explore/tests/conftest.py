"""
Pytest configuration and fixtures for the llmXive pipeline.
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

import pytest

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.fixture
def data_raw(project_root):
    return project_root / "data" / "raw"

@pytest.fixture
def data_curated(project_root):
    return project_root / "data" / "curated"

@pytest.fixture
def data_results(project_root):
    return project_root / "data" / "results"