"""
Pytest configuration and fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the code directory to the path so imports work correctly
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add code/ to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    
    yield
    
    # Cleanup if needed
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def sample_p_value_inequality():
    """Provide a sample p-value inequality string."""
    return "p < 0.05"

@pytest.fixture
def sample_cohen_d_string():
    """Provide a sample Cohen's d string with confidence interval."""
    return "d = 0.5 [0.2, 0.8]"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir()
    return output_dir
