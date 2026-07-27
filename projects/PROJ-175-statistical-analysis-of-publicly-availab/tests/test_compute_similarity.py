import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.compute_similarity import (
    load_ingredient_pairs,
    load_embeddings,
    compute_cosine_similarity,
    main,
    INGREDIENT_PAIRS_PATH,
    EMBEDDINGS_PATH,
    OUTPUT_PATH,
    LOG_PATH
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    # Create expected subdirectories
    processed_dir = Path(temp_dir) / "data" / "processed"
    raw_dir = Path(temp_dir) / "data" / "raw"
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_ingredient_pairs(temp_data_dir):
    """Create mock ingredient pairs file."""
    pairs_path = Path(temp_data_dir) / "data" / "processed" / "ingredient_pairs.parquet"
    data = {
        'ingredient_1': ['salt', 'sugar', 'butter', 'olive_oil'],
        'ingredient_2': ['pepper', 'honey', 'garlic', 'lemon']
    }
    df = pd.DataFrame(data)
    df.to_parquet(pairs_path, index=False)
    return pairs_path

@pytest.fixture
def mock_embeddings(temp_data_dir):
    """Create mock embeddings file."""
    embeddings_path = Path(temp_data_dir) / "data" / "raw" / "recipe1m_embeddings.parquet"
    
    # Create simple 4-dimensional embeddings
    embeddings = {
        'salt': np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
        'pepper': np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        'sugar': np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float32),
        'honey': np.array([0.6, 0.4, 0.0, 0.0], dtype=np.float32),
        'butter': np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32),
        'garlic': np.array([0.0, 0.0, 0.5, 0.5], dtype=np.float32),
        'olive_oil': np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        'lemon': np.array([0.0, 0.0, 0.0, 0.8], dtype=np.float32),
        # Missing ingredient for testing
    }
    
    df = pd.DataFrame([
        {'ingredient_id': k, 'embedding_vector': v.tolist()}
        for k, v in embeddings.items()
    ])
    df.to_parquet(embeddings_path, index=False)
    return embeddings_path

def test_compute_cosine_similarity_identical():
    """Test cosine similarity with identical vectors."""
    v = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert abs(compute_cosine_similarity(v, v) - 1.0) < 1e-6

def test_compute_cosine_similarity_orthogonal():
    """Test cosine similarity with orthogonal vectors."""
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    assert abs(compute_cosine_similarity(v1, v2) - 0.0) < 1e-6

def test_compute_cosine_similarity_opposite():
    """Test cosine similarity with opposite vectors."""
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
    assert abs(compute_cosine_similarity(v1, v2) - (-1.0)) < 1e-6

def test_compute_cosine_similarity_zero_vector():
    """Test cosine similarity with zero vector."""
    v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    assert compute_cosine_similarity(v1, v2) == 0.0

def test_load_ingredient_pairs_missing_file():
    """Test loading pairs when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_ingredient_pairs()

def test_load_embeddings_missing_file():
    """Test loading embeddings when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_embeddings()

@patch('data.compute_similarity.PROCESSED_DIR')
@patch('data.compute_similarity.DATA_DIR')
@patch('data.compute_similarity.INGREDIENT_PAIRS_PATH')
@patch('data.compute_similarity.EMBEDDINGS_PATH')
@patch('data.compute_similarity.OUTPUT_PATH')
@patch('data.compute_similarity.LOG_PATH')
def test_main_execution(
    mock_log_path, mock_output_path, mock_emb_path, mock_pairs_path,
    mock_data_dir, mock_processed_dir, temp_data_dir, mock_ingredient_pairs, mock_embeddings
):
    """Test the main execution flow with mock data."""
    # Setup paths to point to temp directory
    data_dir = Path(temp_data_dir) / "data"
    processed_dir = data_dir / "processed"
    raw_dir = data_dir / "raw"
    
    mock_data_dir.__truediv__.return_value = data_dir
    mock_processed_dir.__truediv__.return_value = processed_dir
    mock_processed_dir.__rtruediv__.return_value = processed_dir
    
    mock_pairs_path.__truediv__.return_value = mock_ingredient_pairs
    mock_emb_path.__truediv__.return_value = mock_embeddings
    mock_output_path.__truediv__.return_value = processed_dir / "flavor_similarity.parquet"
    mock_log_path.__truediv__.return_value = data_dir / "similarity_computation_log.json"
    
    # Run main
    main()
    
    # Verify output exists
    output_path = processed_dir / "flavor_similarity.parquet"
    assert output_path.exists(), "Output file was not created"
    
    # Verify output content
    result_df = pd.read_parquet(output_path)
    assert 'flavor_similarity' in result_df.columns
    assert len(result_df) > 0
    
    # Verify log exists
    log_path = data_dir / "similarity_computation_log.json"
    assert log_path.exists()
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    assert log_data['status'] == 'SUCCESS'
    assert log_data['valid_pairs'] > 0
