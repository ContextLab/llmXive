"""
Pytest configuration and fixtures for the Gut Microbiome and Cognitive Flexibility project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path so imports work without PYTHONPATH setup
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Ensure the 'code' directory is importable as a package
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

def pytest_configure(config):
    """Configure pytest markers and environment."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_data: marks tests that require pre-existing data files"
    )

def pytest_collection_modifyitems(config, items):
    """Skip tests marked with requires_data if data is not present."""
    for item in items:
        if "requires_data" in item.keywords:
            data_path = Path(__file__).parent.parent / "data" / "processed"
            if not data_path.exists() or not any(data_path.iterdir()):
                item.add_marker(pytest.mark.skip(reason="No processed data found in data/processed/"))
