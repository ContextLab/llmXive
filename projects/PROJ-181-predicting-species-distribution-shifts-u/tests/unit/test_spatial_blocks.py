"""
Unit tests for spatial block generation utilities.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from utils.spatial_blocks import create_spatial_blocks, generate_spatial_folds, get_spatial_block_summary
from config import DATA_DIR, RND_SEED


def test_create_spatial_blocks():
    """Test that spatial blocks are created correctly."""
    # Create a simple mock dataset
    np.random.seed(RND_SEED)
    n_points = 100
    lats = np.random.uniform(25, 50, n_points)
    lons = np.random.uniform(-125, -70, n_points)
    
    df = pd.DataFrame({'latitude': lats, 'longitude': lons})
    
    # Test block creation
    blocks = create_spatial_blocks(df, n_blocks=4)
    
    assert 'block_id' in blocks.columns
    assert len(blocks) == n_points
    assert blocks['block_id'].nunique() == 4


def test_generate_spatial_folds():
    """Test that spatial folds are generated correctly."""
    np.random.seed(RND_SEED)
    n_points = 100
    lats = np.random.uniform(25, 50, n_points)
    lons = np.random.uniform(-125, -70, n_points)
    
    df = pd.DataFrame({'latitude': lats, 'longitude': lons})
    
    # Test fold generation
    folds = generate_spatial_folds(df, n_folds=5)
    
    assert 'fold_id' in folds.columns
    assert len(folds) == n_points
    assert folds['fold_id'].nunique() == 5


def test_get_spatial_block_summary():
    """Test that block summary statistics are computed correctly."""
    np.random.seed(RND_SEED)
    n_points = 100
    lats = np.random.uniform(25, 50, n_points)
    lons = np.random.uniform(-125, -70, n_points)
    blocks = np.random.randint(0, 4, n_points)
    
    df = pd.DataFrame({
        'latitude': lats, 
        'longitude': lons, 
        'block_id': blocks
    })
    
    summary = get_spatial_block_summary(df)
    
    assert 'block_id' in summary.columns
    assert 'count' in summary.columns
    assert len(summary) == 4
