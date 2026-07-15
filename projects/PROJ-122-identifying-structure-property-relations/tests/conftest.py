"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
import sys

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code')
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    if code_dir in sys.path:
        sys.path.remove(code_dir)

@pytest.fixture
def sample_smiles():
    return "CCO"

@pytest.fixture
def sample_weight_fractions():
    return [0.5, 0.5]
