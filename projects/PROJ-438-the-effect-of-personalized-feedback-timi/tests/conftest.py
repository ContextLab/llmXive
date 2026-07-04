"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the code directory to sys.path for tests."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    
    yield
    
    # Cleanup if necessary (though usually not needed for path insertion)

import pytest

@pytest.fixture
def sample_dataframe():
    """Provide a simple dataframe for testing."""
    import pandas as pd
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "course_id": ["A", "A", "B", "B", "C"],
        "timestamp": pd.date_range("2023-01-01", periods=5),
        "grade": [85.5, 90.0, 70.0, 65.5, 95.0],
        "completed": [True, True, False, True, True]
    })