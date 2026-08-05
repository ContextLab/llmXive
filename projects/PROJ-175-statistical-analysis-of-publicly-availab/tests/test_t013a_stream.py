"""
Tests for T013a: Stream & Validate Recipe1M.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(project_root))

from data.stream_recipe1m import (
    ensure_directories,
    load_sample_size_requirement,
    flatten_recipe,
    stream_and_process_dataset
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_flatten_recipe_basic():
    """Test basic recipe flattening."""
    recipe = {
        "id": "123",
        "title": "Test Recipe",
        "ingredients": ["flour", "sugar", "eggs"],
        "instructions": ["Mix", "Bake"],
        "rating": 4.5
    }
    result = flatten_recipe(recipe)
    
    assert result['recipe_id'] == "123"
    assert result['title'] == "Test Recipe"
    assert result['ingredients'] == ["flour", "sugar", "eggs"]
    assert result['instructions'] == ["Mix", "Bake"]
    assert result['rating'] == 4.5

def test_flatten_recipe_nested_ingredients():
    """Test flattening with nested ingredient dicts."""
    recipe = {
        "id": "456",
        "ingredients": [
            {"ingredient": "flour", "quantity": "2 cups"},
            {"ingredient": "sugar", "quantity": "1 cup"}
        ],
        "instructions": [],
        "rating": None
    }
    result = flatten_recipe(recipe)
    
    assert result['ingredients'] == ["flour", "sugar"]

def test_ensure_directories(temp_dir):
    """Test directory creation."""
    # Mock project_root for this test
    import data.stream_recipe1m as module
    original_root = module.project_root
    module.project_root = temp_dir
    
    try:
        ensure_directories()
        assert (temp_dir / "data" / "raw").exists()
        assert (temp_dir / "data" / "logs").exists()
    finally:
        module.project_root = original_root

def test_load_sample_size_requirement_missing_file():
    """Test error when pilot stats file is missing."""
    with pytest.raises(FileNotFoundError):
        # Mock the path to a non-existent file
        with patch('data.stream_recipe1m.project_root') as mock_root:
            mock_root.__truediv__ = lambda self, other: Path("/nonexistent/pilot_stats.json")
            load_sample_size_requirement()

def test_load_sample_size_requirement_missing_key(temp_dir):
    """Test error when sample_size_required key is missing."""
    pilot_path = temp_dir / "pilot_stats.json"
    with open(pilot_path, "w") as f:
        json.dump({"other_key": 100}, f)
    
    with patch('data.stream_recipe1m.project_root') as mock_root:
        mock_root.__truediv__ = lambda self, other: pilot_path if other == "pilot_stats.json" else temp_dir
        with pytest.raises(KeyError):
            load_sample_size_requirement()

def test_load_sample_size_requirement_success(temp_dir):
    """Test successful loading of sample size."""
    pilot_path = temp_dir / "pilot_stats.json"
    with open(pilot_path, "w") as f:
        json.dump({"sample_size_required": 500}, f)
    
    with patch('data.stream_recipe1m.project_root') as mock_root:
        mock_root.__truediv__ = lambda self, other: pilot_path if other == "pilot_stats.json" else temp_dir
        result = load_sample_size_requirement()
        assert result == 500
