"""
Tests for T013d: Fetch Recipe1M Embeddings.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.embeddings import load_unique_ingredients, fetch_embeddings_streaming, save_output, ensure_directories, LOG_FILE, OUTPUT_FILE, INPUT_FILE

@pytest.fixture
def mock_unique_ingredients(tmp_path):
    """Create a mock unique_ingredients.parquet file."""
    input_path = tmp_path / "unique_ingredients.parquet"
    df = pd.DataFrame({
        "ingredient_id": ["salt", "sugar", "flour", "butter", "egg"],
        "count": [100, 90, 80, 70, 60]
    })
    df.to_parquet(input_path)
    # Temporarily override INPUT_FILE for testing
    original_path = INPUT_FILE
    # We cannot easily override the global in the module without importlib reload
    # So we will test the logic by passing data directly or mocking the file system
    return input_path, df

def test_ensure_directories(tmp_path):
    """Test that ensure_directories creates the folder."""
    test_dir = tmp_path / "test_output"
    # Patch the OUTPUT_DIR constant in the module
    import code.data.embeddings as emb_module
    original_output_dir = emb_module.OUTPUT_DIR
    emb_module.OUTPUT_DIR = test_dir
    
    try:
        emb_module.ensure_directories()
        assert test_dir.exists()
    finally:
        emb_module.OUTPUT_DIR = original_output_dir

def test_load_unique_ingredients_missing_file():
    """Test that load_unique_ingredients raises if file missing."""
    # Ensure the file doesn't exist
    if INPUT_FILE.exists():
        INPUT_FILE.unlink()
    
    with pytest.raises(FileNotFoundError):
        load_unique_ingredients()

# Note: Actual streaming test requires a real dataset or a mock of the dataset iterator
# We test the structure of the expected output if we had a mock
def test_fetch_embeddings_streaming_structure():
    """
    Test the logic of fetch_embeddings_streaming with a mock dataset iterator.
    This avoids hitting the network during unit tests.
    """
    # Mock ingredients
    ingredients = ["salt", "sugar"]
    
    # Mock dataset iterator
    class MockDataset:
        def __iter__(self):
            return iter([
                {"ingredient": "salt", "embedding": [0.1, 0.2, 0.3]},
                {"ingredient": "sugar", "embedding": [0.4, 0.5, 0.6]},
                {"ingredient": "flour", "embedding": [0.7, 0.8, 0.9]}, # Not in list
            ])
    
    # We need to patch load_dataset
    import code.data.embeddings as emb_module
    original_load = emb_module.load_dataset
    
    def mock_load(*args, **kwargs):
        return MockDataset()
    
    emb_module.load_dataset = mock_load
    
    try:
        df = fetch_embeddings_streaming(ingredients)
        assert len(df) == 2
        assert "salt" in df["ingredient_id"].values
        assert "sugar" in df["ingredient_id"].values
        assert "embedding" in df.columns
        assert isinstance(df.iloc[0]["embedding"], list)
    finally:
        emb_module.load_dataset = original_load

def test_save_output(tmp_path):
    """Test saving output to parquet."""
    test_dir = tmp_path / "test_save"
    test_dir.mkdir()
    test_file = test_dir / "test_embeddings.parquet"
    
    import code.data.embeddings as emb_module
    original_output_dir = emb_module.OUTPUT_DIR
    original_output_file = emb_module.OUTPUT_FILE
    emb_module.OUTPUT_DIR = test_dir
    emb_module.OUTPUT_FILE = test_file
    
    try:
        df = pd.DataFrame({
            "ingredient_id": ["test"],
            "embedding": [[1.0, 2.0]],
            "source": "mock"
        })
        save_output(df)
        assert test_file.exists()
        loaded = pd.read_parquet(test_file)
        assert len(loaded) == 1
    finally:
        emb_module.OUTPUT_DIR = original_output_dir
        emb_module.OUTPUT_FILE = original_output_file

def test_log_results(tmp_path):
    """Test logging results."""
    import code.data.embeddings as emb_module
    original_log_file = emb_module.LOG_FILE
    emb_module.LOG_FILE = tmp_path / "test_log.json"
    
    try:
        emb_module.log_results(100, 50, "SUCCESS")
        assert emb_module.LOG_FILE.exists()
        with open(emb_module.LOG_FILE, 'r') as f:
            data = json.load(f)
        assert data["status"] == "SUCCESS"
        assert data["coverage_rate"] == 0.5
    finally:
        emb_module.LOG_FILE = original_log_file
