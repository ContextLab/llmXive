import os
import sys
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir

@pytest.fixture
def sample_data():
    """Provide sample data for testing."""
    import pandas as pd
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'value': [10, 20, 30, 40, 50],
        'category': ['A', 'B', 'A', 'B', 'A']
    })

@pytest.fixture
def mock_api_response():
    """Provide a mock API response for testing."""
    return {
        'status': 'success',
        'data': [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
    }
