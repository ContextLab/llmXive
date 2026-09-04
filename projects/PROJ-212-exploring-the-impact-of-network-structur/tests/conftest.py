import pytest
import os
import sys
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

@pytest.fixture
def sample_graph():
    """Provide a sample graph for testing."""
    return {
        "id": "test_graph",
        "nodes": 10,
        "edges": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]
    }
