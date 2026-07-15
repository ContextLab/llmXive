"""
Pytest configuration and shared fixtures for llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project code directory is in the Python path
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the project's code directory to sys.path."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Optional: clean up if needed, though usually not necessary for path insertion

@pytest.fixture
def sample_graph_data():
    """Provide a minimal valid graph structure for testing."""
    return {
        "nodes": [
            {"id": "n1", "type": "entity", "content": "Alice"},
            {"id": "n2", "type": "entity", "content": "Bob"},
            {"id": "n3", "type": "relation", "content": "knows"}
        ],
        "edges": [
            {"source": "n1", "target": "n3", "weight": 1.0},
            {"source": "n3", "target": "n2", "weight": 1.0}
        ]
    }

@pytest.fixture
def sample_task_data():
    """Provide a minimal valid task structure for testing."""
    return {
        "task_id": "test_task_001",
        "question": "Who knows Bob?",
        "context": "Alice knows Bob.",
        "answer": "Alice"
    }
