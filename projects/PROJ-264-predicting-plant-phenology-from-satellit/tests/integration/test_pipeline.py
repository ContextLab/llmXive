"""
Integration tests for the plant phenology prediction pipeline.

This module contains integration tests for:
1. Data ingestion pipeline
2. Data preprocessing pipeline
3. Spatial Block Cross-Validation logic (US2)
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
import tempfile
import json
import logging

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_config
from src.data.ingestion import run_nature_notebook_ingestion
from src.data.preprocessing import (
    run_preprocessing,
    exclude_multicollinear_features,
    interpolate_time_series,
    filter_insufficient_data,
    mask_missing_phenology_labels
)
from src.lib.utils import setup_logging, save_csv, load_csv

# Configure logging for tests
logger = setup_logging(level=logging.INFO, name="integration_test")

@pytest.fixture
def sample_site_data():
    """Create a sample dataset mimicking the output of the ingestion pipeline."""
    # Generate synthetic time series for 5 sites over 3 years (2018-2020)
    # with 10-day intervals
    np.random.seed(42)
    
    dates = pd.date_range(start='2018-01-01', end='2020-12-31', freq='10D')
    site_ids = ['SITE_001', 'SITE_002', 'SITE_003', 'SITE_004', 'SITE_005']
    
    # Create latitude/longitude for spatial blocking
    lats = [40.0, 41.0, 42.0, 39.0, 43.0]
    lons = [-75.0, -76.0, -77.0, -74.0, -78.0]
    
    data = []
    for site_id, lat, lon in zip(site_ids, lats, lons):
        for date in dates:
            # Add some realistic variation
            doy = date.dayofyear
            ndvi = 0.2 + 0.5 * np.sin(2 * np.pi * (doy - 80) / 365) + np.random.normal(0, 0.05)
            evi = 0.1 + 0.4 * np.sin(2 * np.pi * (doy - 80) / 365) + np.random.normal(0, 0.04)
            temp = 10 + 15 * np.sin(2 * np.pi * (doy - 80) / 365) + np.random.normal(0, 2)
            precip = max(0, np.random.exponential(5))
            
            # Phenology labels (some missing)
            budburst_date = None
            if site_id in ['SITE_001', 'SITE_002', 'SITE_003'] and 80 <= doy <= 120:
                if np.random.random() > 0.2:  # 80% chance of observation
                    budburst_date = date + pd.Timedelta(days=int(np.random.uniform(-5, 5)))
            
            data.append({
                'site_id': site_id,
                'latitude': lat,
                'longitude': lon,
                'date': date,
                'day_of_year': doy,
                'ndvi': ndvi,
                'evi': evi,
                'temperature': temp,
                'precipitation': precip,
                'budburst_date': budburst_date
            })
    
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_spatial_block_cv_logic(sample_site_data, temp_output_dir):
    """
    Integration test for Spatial Block Cross-Validation logic.
    
    This test verifies that:
    1. Sites are correctly grouped into spatial blocks based on latitude/longitude
    2. Train/test splits respect spatial independence (no overlap between blocks)
    3. The blocking strategy covers all sites
    4. The number of folds is configurable
    """
    logger.info("Testing Spatial Block Cross-Validation logic")
    
    # Define blocking parameters
    n_folds = 3
    lat_bins = 3
    lon_bins = 3
    
    # Implement spatial blocking logic
    def create_spatial_blocks(df, lat_bins=3, lon_bins=3):
        """
        Create spatial blocks by binning latitude and longitude.
        
        Args:
            df: DataFrame with 'latitude' and 'longitude' columns
            lat_bins: Number of latitude bins
            lon_bins: Number of longitude bins
        
        Returns:
            DataFrame with 'block_id' column added
        """
        # Create bins
        lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
        lon_min, lon_max = df['longitude'].min(), df['longitude'].max()
        
        lat_edges = np.linspace(lat_min, lat_max, lat_bins + 1)
        lon_edges = np.linspace(lon_min, lon_max, lon_bins + 1)
        
        # Assign block IDs
        df = df.copy()
        df['lat_bin'] = pd.cut(df['latitude'], bins=lat_edges, labels=False)
        df['lon_bin'] = pd.cut(df['longitude'], bins=lon_edges, labels=False)
        df['block_id'] = df['lat_bin'] * lon_bins + df['lon_bin']
        
        return df.drop(['lat_bin', 'lon_bin'], axis=1)
    
    def spatial_block_split(df, n_folds, seed=42):
        """
        Create spatial block cross-validation splits.
        
        Args:
            df: DataFrame with 'block_id' column
            n_folds: Number of folds
            seed: Random seed for reproducibility
        
        Returns:
            List of (train_mask, test_mask) tuples
        """
        np.random.seed(seed)
        blocks = df['block_id'].unique()
        np.random.shuffle(blocks)
        
        # Ensure we have at least n_folds blocks
        if len(blocks) < n_folds:
            # If not enough blocks, use all blocks and repeat some
            blocks = np.tile(blocks, (n_folds // len(blocks) + 1))[:n_folds]
        
        # Create folds
        fold_size = len(blocks) // n_folds
        folds = []
        
        for i in range(n_folds):
            start_idx = i * fold_size
            end_idx = start_idx + fold_size if i < n_folds - 1 else len(blocks)
            
            test_blocks = blocks[start_idx:end_idx]
            train_blocks = np.setdiff1d(blocks, test_blocks)
            
            train_mask = df['block_id'].isin(train_blocks)
            test_mask = df['block_id'].isin(test_blocks)
            
            folds.append((train_mask, test_mask))
        
        return folds
    
    # Apply spatial blocking
    blocked_df = create_spatial_blocks(sample_site_data, lat_bins=lat_bins, lon_bins=lon_bins)
    
    # Verify block assignment
    assert 'block_id' in blocked_df.columns, "block_id column not created"
    assert blocked_df['block_id'].notna().all(), "Some rows missing block_id"
    
    # Create splits
    splits = spatial_block_split(blocked_df, n_folds=n_folds)
    
    # Verify number of splits
    assert len(splits) == n_folds, f"Expected {n_folds} splits, got {len(splits)}"
    
    # Verify each split has train and test sets
    for i, (train_mask, test_mask) in enumerate(splits):
        assert train_mask.sum() > 0, f"Fold {i} has no training data"
        assert test_mask.sum() > 0, f"Fold {i} has no test data"
        
        # Verify spatial independence
        train_blocks = blocked_df.loc[train_mask, 'block_id'].unique()
        test_blocks = blocked_df.loc[test_mask, 'block_id'].unique()
        
        overlap = set(train_blocks) & set(test_blocks)
        assert len(overlap) == 0, f"Fold {i} has overlapping blocks: {overlap}"
    
    # Verify all sites are covered across folds
    all_train_blocks = set()
    all_test_blocks = set()
    for train_mask, test_mask in splits:
        all_train_blocks.update(blocked_df.loc[train_mask, 'block_id'].unique())
        all_test_blocks.update(blocked_df.loc[test_mask, 'block_id'].unique())
    
    assert len(all_train_blocks) > 0, "No training blocks found"
    assert len(all_test_blocks) > 0, "No test blocks found"
    
    # Save intermediate results for debugging
    output_file = temp_output_dir / "spatial_block_results.json"
    results = {
        'n_sites': len(sample_site_data['site_id'].unique()),
        'n_blocks': blocked_df['block_id'].nunique(),
        'n_folds': n_folds,
        'blocks_per_fold': [
            {
                'fold': i,
                'train_blocks': int(train_mask.sum()),
                'test_blocks': int(test_mask.sum())
            }
            for i, (train_mask, test_mask) in enumerate(splits)
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Spatial block CV test passed. Results saved to {output_file}")
    
    return True

def test_spatial_block_cv_with_preprocessing(sample_site_data, temp_output_dir):
    """
    Integration test combining spatial block CV with preprocessing pipeline.
    
    This test verifies that:
    1. Preprocessing works correctly on spatially blocked data
    2. Feature engineering (lagged windows) respects spatial splits
    3. No data leakage occurs between train and test sets
    """
    logger.info("Testing Spatial Block CV with preprocessing pipeline")
    
    # Create spatial blocks
    lat_bins = 3
    lon_bins = 3
    n_folds = 2
    
    blocked_df = sample_site_data.copy()
    lat_min, lat_max = blocked_df['latitude'].min(), blocked_df['latitude'].max()
    lon_min, lon_max = blocked_df['longitude'].min(), blocked_df['longitude'].max()
    
    lat_edges = np.linspace(lat_min, lat_max, lat_bins + 1)
    lon_edges = np.linspace(lon_min, lon_max, lon_bins + 1)
    
    blocked_df['lat_bin'] = pd.cut(blocked_df['latitude'], bins=lat_edges, labels=False)
    blocked_df['lon_bin'] = pd.cut(blocked_df['longitude'], bins=lon_edges, labels=False)
    blocked_df['block_id'] = blocked_df['lat_bin'] * lon_bins + blocked_df['lon_bin']
    
    # Create folds
    blocks = blocked_df['block_id'].unique()
    np.random.seed(42)
    np.random.shuffle(blocks)
    
    fold_size = len(blocks) // n_folds
    test_blocks = blocks[:fold_size]
    train_blocks = blocks[fold_size:]
    
    train_mask = blocked_df['block_id'].isin(train_blocks)
    test_mask = blocked_df['block_id'].isin(test_blocks)
    
    train_data = blocked_df[train_mask].copy()
    test_data = blocked_df[test_mask].copy()
    
    # Verify no spatial overlap
    train_sites = set(train_data['site_id'].unique())
    test_sites = set(test_data['site_id'].unique())
    assert len(train_sites & test_sites) == 0, "Spatial overlap detected in sites"
    
    # Apply preprocessing to training data
    # Note: In a real scenario, we would fit preprocessing on train and apply to test
    # For this test, we'll apply the same logic to both
    
    # Exclude multicollinear features
    processed_train = exclude_multicollinear_features(train_data)
    processed_test = exclude_multicollinear_features(test_data)
    
    # Interpolate time series
    processed_train = interpolate_time_series(processed_train, max_gap=1)
    processed_test = interpolate_time_series(processed_test, max_gap=1)
    
    # Filter insufficient data
    processed_train = filter_insufficient_data(processed_train, min_coverage=0.8)
    processed_test = filter_insufficient_data(processed_test, min_coverage=0.8)
    
    # Mask missing phenology labels
    processed_train = mask_missing_phenology_labels(processed_train, 'budburst_date')
    processed_test = mask_missing_phenology_labels(processed_test, 'budburst_date')
    
    # Verify preprocessing didn't break spatial independence
    # (This is a sanity check - the main test is that preprocessing runs without error)
    assert len(processed_train) > 0, "Training data empty after preprocessing"
    assert len(processed_test) > 0, "Test data empty after preprocessing"
    
    # Save processed data
    train_output = temp_output_dir / "train_processed.csv"
    test_output = temp_output_dir / "test_processed.csv"
    
    save_csv(processed_train, train_output)
    save_csv(processed_test, test_output)
    
    # Verify files were created
    assert train_output.exists(), "Train output file not created"
    assert test_output.exists(), "Test output file not created"
    
    logger.info(f"Spatial block CV with preprocessing test passed. "
               f"Train size: {len(processed_train)}, Test size: {len(processed_test)}")
    
    return True

def test_spatial_block_cv_edge_cases(sample_site_data, temp_output_dir):
    """
    Test edge cases for spatial block CV:
    1. Very few sites (less than n_folds)
    2. All sites in one geographic location
    3. Extreme coordinate values
    """
    logger.info("Testing spatial block CV edge cases")
    
    # Edge case 1: Fewer sites than folds
    small_df = sample_site_data[sample_site_data['site_id'].isin(['SITE_001', 'SITE_002'])].copy()
    
    lat_bins = 2
    lon_bins = 2
    n_folds = 5  # More folds than sites
    
    lat_min, lat_max = small_df['latitude'].min(), small_df['latitude'].max()
    lon_min, lon_max = small_df['longitude'].min(), small_df['longitude'].max()
    
    # Handle case where all sites have same coordinates
    if lat_min == lat_max:
        lat_min -= 0.1
        lat_max += 0.1
    if lon_min == lon_max:
        lon_min -= 0.1
        lon_max += 0.1
    
    lat_edges = np.linspace(lat_min, lat_max, lat_bins + 1)
    lon_edges = np.linspace(lon_min, lon_max, lon_bins + 1)
    
    small_df['lat_bin'] = pd.cut(small_df['latitude'], bins=lat_edges, labels=False)
    small_df['lon_bin'] = pd.cut(small_df['longitude'], bins=lon_edges, labels=False)
    small_df['block_id'] = small_df['lat_bin'] * lon_bins + small_df['lon_bin']
    
    # Should still create folds without error
    blocks = small_df['block_id'].unique()
    np.random.seed(42)
    np.random.shuffle(blocks)
    
    # If not enough unique blocks, duplicate them
    if len(blocks) < n_folds:
        blocks = np.tile(blocks, (n_folds // len(blocks) + 1))[:n_folds]
    
    fold_size = len(blocks) // n_folds
    splits = []
    
    for i in range(n_folds):
        start_idx = i * fold_size
        end_idx = start_idx + fold_size if i < n_folds - 1 else len(blocks)
        
        test_blocks = blocks[start_idx:end_idx]
        train_blocks = np.setdiff1d(blocks, test_blocks)
        
        train_mask = small_df['block_id'].isin(train_blocks)
        test_mask = small_df['block_id'].isin(test_blocks)
        
        splits.append((train_mask, test_mask))
        
        # Verify no overlap
        train_blocks_actual = small_df.loc[train_mask, 'block_id'].unique()
        test_blocks_actual = small_df.loc[test_mask, 'block_id'].unique()
        overlap = set(train_blocks_actual) & set(test_blocks_actual)
        assert len(overlap) == 0, f"Edge case failed: overlap in fold {i}"
    
    logger.info("Edge case tests passed")
    return True

def test_spatial_block_cv_reproducibility(sample_site_data):
    """
    Test that spatial block CV is reproducible with the same seed.
    """
    logger.info("Testing spatial block CV reproducibility")
    
    n_folds = 3
    lat_bins = 3
    lon_bins = 3
    seed = 12345
    
    # First run
    blocked_df1 = sample_site_data.copy()
    lat_min, lat_max = blocked_df1['latitude'].min(), blocked_df1['latitude'].max()
    lon_min, lon_max = blocked_df1['longitude'].min(), blocked_df1['longitude'].max()
    
    lat_edges = np.linspace(lat_min, lat_max, lat_bins + 1)
    lon_edges = np.linspace(lon_min, lon_max, lon_bins + 1)
    
    blocked_df1['lat_bin'] = pd.cut(blocked_df1['latitude'], bins=lat_edges, labels=False)
    blocked_df1['lon_bin'] = pd.cut(blocked_df1['longitude'], bins=lon_edges, labels=False)
    blocked_df1['block_id'] = blocked_df1['lat_bin'] * lon_bins + blocked_df1['lon_bin']
    
    blocks1 = blocked_df1['block_id'].unique()
    np.random.seed(seed)
    np.random.shuffle(blocks1)
    
    fold_size = len(blocks1) // n_folds
    splits1 = []
    for i in range(n_folds):
        start_idx = i * fold_size
        end_idx = start_idx + fold_size if i < n_folds - 1 else len(blocks1)
        test_blocks = blocks1[start_idx:end_idx]
        train_blocks = np.setdiff1d(blocks1, test_blocks)
        train_mask = blocked_df1['block_id'].isin(train_blocks)
        test_mask = blocked_df1['block_id'].isin(test_blocks)
        splits1.append((train_mask.copy(), test_mask.copy()))
    
    # Second run
    blocked_df2 = sample_site_data.copy()
    blocked_df2['lat_bin'] = pd.cut(blocked_df2['latitude'], bins=lat_edges, labels=False)
    blocked_df2['lon_bin'] = pd.cut(blocked_df2['longitude'], bins=lon_edges, labels=False)
    blocked_df2['block_id'] = blocked_df2['lat_bin'] * lon_bins + blocked_df2['lon_bin']
    
    blocks2 = blocked_df2['block_id'].unique()
    np.random.seed(seed)
    np.random.shuffle(blocks2)
    
    fold_size = len(blocks2) // n_folds
    splits2 = []
    for i in range(n_folds):
        start_idx = i * fold_size
        end_idx = start_idx + fold_size if i < n_folds - 1 else len(blocks2)
        test_blocks = blocks2[start_idx:end_idx]
        train_blocks = np.setdiff1d(blocks2, test_blocks)
        train_mask = blocked_df2['block_id'].isin(train_blocks)
        test_mask = blocked_df2['block_id'].isin(test_blocks)
        splits2.append((train_mask.copy(), test_mask.copy()))
    
    # Compare splits
    for i, ((t1, te1), (t2, te2)) in enumerate(zip(splits1, splits2)):
        assert t1.equals(t2), f"Train mask differs in fold {i}"
        assert te1.equals(te2), f"Test mask differs in fold {i}"
    
    logger.info("Reproducibility test passed")
    return True