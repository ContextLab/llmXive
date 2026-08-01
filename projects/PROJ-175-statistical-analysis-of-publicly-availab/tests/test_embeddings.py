"""
Tests for T014c: Embeddings fetching functionality.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.embeddings import (
    ensure_directories,
    load_ingredient_list,
    aggregate_embeddings,
    save_embeddings
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        processed_dir = tmp_path / "data" / "processed"
        raw_dir = tmp_path / "data" / "raw"
        processed_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        yield tmp_path
        # Cleanup handled by TemporaryDirectory

def test_ensure_directories(temp_dirs):
    """Test that ensure_directories creates the necessary folders."""
    # Change to temp dir context
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dirs)
        # Mock the PROJECT_ROOT behavior
        import code.data.embeddings as emb_module
        emb_module.PROCESSED_DIR = temp_dirs / "data" / "processed"
        emb_module.RAW_DIR = temp_dirs / "data" / "raw"
        
        emb_module.ensure_directories()
        
        assert emb_module.PROCESSED_DIR.exists()
        assert emb_module.RAW_DIR.exists()
    finally:
        os.chdir(original_cwd)

def test_aggregate_embeddings():
    """Test embedding aggregation logic."""
    # Create mock embedding data
    ingredient_embeddings = {
        'ingredient_a': [np.array([1.0, 2.0, 3.0]), np.array([2.0, 3.0, 4.0])],
        'ingredient_b': [np.array([0.5, 1.5, 2.5])]
    }
    ingredient_counts = {
        'ingredient_a': 2,
        'ingredient_b': 1
    }
    
    aggregated, stats = aggregate_embeddings(ingredient_embeddings, ingredient_counts)
    
    # Check aggregation results
    assert 'ingredient_a' in aggregated
    assert 'ingredient_b' in aggregated
    
    # Check mean calculation for ingredient_a
    expected_mean_a = np.mean([np.array([1.0, 2.0, 3.0]), np.array([2.0, 3.0, 4.0])], axis=0)
    actual_mean_a = np.array(aggregated['ingredient_a']['embedding'])
    np.testing.assert_array_almost_equal(actual_mean_a, expected_mean_a)
    
    # Check count
    assert aggregated['ingredient_a']['count'] == 2
    assert aggregated['ingredient_b']['count'] == 1

def test_save_embeddings(temp_dirs):
    """Test saving embeddings to parquet."""
    # Create mock aggregated data
    aggregated = {
        'ingredient_a': {
            'embedding': [1.0, 2.0, 3.0],
            'std': [0.1, 0.1, 0.1],
            'count': 10
        },
        'ingredient_b': {
            'embedding': [4.0, 5.0, 6.0],
            'std': [0.2, 0.2, 0.2],
            'count': 5
        }
    }
    stats = [
        {'ingredient_id': 'ingredient_a', 'embedding_count': 10, 'mean_norm': 3.74},
        {'ingredient_id': 'ingredient_b', 'embedding_count': 5, 'mean_norm': 8.77}
    ]
    
    # Set output path
    import code.data.embeddings as emb_module
    emb_module.PROCESSED_DIR = temp_dirs / "data" / "processed"
    emb_module.EMBEDDINGS_OUTPUT = emb_module.PROCESSED_DIR / "test_embeddings.parquet"
    
    df = save_embeddings(aggregated, stats)
    
    # Verify file exists
    assert emb_module.EMBEDDINGS_OUTPUT.exists()
    
    # Verify content
    df_loaded = pd.read_parquet(emb_module.EMBEDDINGS_OUTPUT)
    assert len(df_loaded) == 2
    assert 'ingredient_id' in df_loaded.columns
    assert 'embedding' in df_loaded.columns
    assert 'embedding_count' in df_loaded.columns
    
    # Verify data integrity
    assert 'ingredient_a' in df_loaded['ingredient_id'].values
    assert 'ingredient_b' in df_loaded['ingredient_id'].values

def test_load_ingredient_list_missing_files(temp_dirs):
    """Test error handling when source files are missing."""
    import code.data.embeddings as emb_module
    emb_module.PROCESSED_DIR = temp_dirs / "data" / "processed"
    emb_module.RAW_DIR = temp_dirs / "data" / "raw"
    
    with pytest.raises(FileNotFoundError, match="Neither.*nor.*found"):
        load_ingredient_list()