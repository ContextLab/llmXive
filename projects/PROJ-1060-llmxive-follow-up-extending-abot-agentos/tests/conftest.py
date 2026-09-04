"""
Pytest configuration and shared fixtures for llmXive project.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Ensure code/ is in path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add code/ to sys.path for all tests."""
    root = Path(__file__).parent.parent
    code_path = root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def sample_alfworld_trace() -> Dict[str, Any]:
    """
    Provide a minimal, realistic ALFWorld trace structure.
    Matches the schema expected by code/data_loader.py and code/graph_builder.py.
    """
    return {
        "task_id": "test_task_001",
        "episode_id": 1,
        "observations": [
            {
                "observation": "You are in the living room. There is a key on the table.",
                "image": None, # Images handled by VLM in tokenizer
                "action": "go to table"
            },
            {
                "observation": "You arrive at the table. There is a key on the table.",
                "image": None,
                "action": "pickup key"
            },
            {
                "observation": "You pick up the key from the table.",
                "image": None,
                "action": "go to drawer"
            },
            {
                "observation": "You arrive at the drawer. The drawer is closed.",
                "image": None,
                "action": "open drawer"
            }
        ],
        "goal": "put the key in the drawer",
        "success": True
    }

@pytest.fixture
def sample_graph_data() -> Dict[str, Any]:
    """
    Provide a sample graph structure for contract testing.
    """
    return {
        "nodes": [
            {"id": "n1", "token": "table", "type": "object"},
            {"id": "n2", "token": "key", "type": "object"},
            {"id": "n3", "token": "drawer", "type": "object"}
        ],
        "edges": [
            {"source": "n1", "target": "n2", "predicate": "contains"},
            {"source": "n2", "target": "n3", "predicate": "before"}
        ]
    }

@pytest.fixture
def ground_truth_schema() -> Dict[str, Any]:
    """
    Load or provide the ground truth schema for validation tests.
    If the file exists in data/schemas, use it; otherwise provide a minimal default.
    """
    root = Path(__file__).parent.parent
    schema_path = root / "data" / "schemas" / "ground_truth_mapping.json"
    
    if schema_path.exists():
        with open(schema_path, "r") as f:
            return json.load(f)
    
    return {
        "nodes": ["table", "key", "drawer", "sofa", "lamp"],
        "edges": [
            {"source": "table", "target": "key", "predicate": "on_top_of"},
            {"source": "drawer", "target": "key", "predicate": "inside"}
        ],
        "predicates": ["on_top_of", "near", "before", "inside", "next_to"]
    }
