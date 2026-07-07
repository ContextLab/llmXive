import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.ingest import apply_mice_imputation
from code.utils.logging import DataPipelineLog

def test_apply_mice_imputation_with_missing_values():
    """Test that MICE imputation correctly handles missing values."""
    # Create test data with missing values
    data = {
        'species_id': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
        'trait_1': [1.0, np.nan, 3.0, np.nan, 5.0],
        'trait_2': [np.nan, 2.0, 3.0, 4.0, np.nan],
        'trait_3': [1.1, 2.2, 3.3, 4.4, 5.5]
    }
    df = pd.DataFrame(data)
    
    # Apply imputation
    imputed_df, dropped_cols, imputation_counts = apply_mice_imputation(df)
    
    # Verify no missing values remain
    assert imputed_df.isna().sum().sum() == 0, "Imputation failed to fill all missing values"
    
    # Verify imputation counts
    assert 'trait_1' in imputation_counts
    assert 'trait_2' in imputation_counts
    assert imputation_counts['trait_1'] == 2
    assert imputation_counts['trait_2'] == 2
    
    # Verify dropped columns is empty
    assert len(dropped_cols) == 0, f"Unexpected columns dropped: {dropped_cols}"
    
    # Verify logger recorded the event
    logger = DataPipelineLog()
    # Check that the log file exists and contains imputation stats
    log_path = Path('data/logs/pipeline_log.json')
    if log_path.exists():
        import json
        with open(log_path, 'r') as f:
            log_data = json.load(f)
            # Verify imputation stats are present
            assert any('imputed_count' in str(entry) for entry in log_data.get('events', []))

def test_apply_mice_imputation_drops_unimputable_columns():
    """Test that columns with all missing values are dropped."""
    # Create test data with an unimputable column
    data = {
        'species_id': ['sp1', 'sp2', 'sp3'],
        'trait_1': [1.0, 2.0, 3.0],
        'trait_all_nan': [np.nan, np.nan, np.nan]
    }
    df = pd.DataFrame(data)
    
    # Apply imputation
    imputed_df, dropped_cols, imputation_counts = apply_mice_imputation(df)
    
    # Verify unimputable column was dropped
    assert 'trait_all_nan' in dropped_cols
    assert 'trait_all_nan' not in imputed_df.columns
    
    # Verify logger recorded the drop
    logger = DataPipelineLog()
    log_path = Path('data/logs/pipeline_log.json')
    if log_path.exists():
        import json
        with open(log_path, 'r') as f:
            log_data = json.load(f)
            assert any('dropped_columns' in str(entry) for entry in log_data.get('events', []))

def test_apply_mice_imputation_no_missing_values():
    """Test that imputation works correctly when no missing values exist."""
    data = {
        'species_id': ['sp1', 'sp2', 'sp3'],
        'trait_1': [1.0, 2.0, 3.0],
        'trait_2': [4.0, 5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    # Apply imputation
    imputed_df, dropped_cols, imputation_counts = apply_mice_imputation(df)
    
    # Verify no changes
    assert imputed_df.equals(df)
    assert len(dropped_cols) == 0
    assert len(imputation_counts) == 0