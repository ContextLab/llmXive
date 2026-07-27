"""
Integration test for end-to-end download and harmonization.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.harmonize import harmonize_experiment
from data.loaders import HarmonizedDataset

def test_end_to_end_harmonization():
    """Simulate the full pipeline from raw data to harmonized dataset."""
    # 1. Create raw data
    raw_data = pd.DataFrame({
        'separation_um': [10.0, 20.0, 30.0, 40.0],
        'force_dyne': [1e-5, 2.5e-6, 1.1e-6, 6.25e-7],
        'experiment_id': 'test_001'
    })
    
    # 2. Define target grid
    target_grid = np.linspace(10, 40, 31) * 1e-6
    
    # 3. Harmonize
    harmonized_df = harmonize_experiment(raw_data, target_grid)
    
    # 4. Verify output structure
    assert 'separation_m' in harmonized_df.columns
    assert 'force_N' in harmonized_df.columns
    assert len(harmonized_df) == 31
    
    # 5. Check units (sanity check: force should be ~1e-10 to 1e-12 range for these inputs)
    assert harmonized_df['force_N'].max() < 1e-4
    assert harmonized_df['separation_m'].min() >= 10e-6
    assert harmonized_df['separation_m'].max() <= 40e-6

def test_harmonized_dataset_integration():
    """Test creating the dataset object from harmonized dataframe."""
    raw_data = pd.DataFrame({
        'separation_um': [10.0, 20.0, 30.0],
        'force_dyne': [1e-5, 2.5e-6, 1.1e-6],
        'experiment_id': 'test_001'
    })
    
    target_grid = np.linspace(10, 30, 21) * 1e-6
    harmonized_df = harmonize_experiment(raw_data, target_grid)
    
    # Construct covariance (identity for simplicity)
    n = len(harmonized_df)
    cov = np.eye(n)
    
    dataset = HarmonizedDataset(
        separation_m=harmonized_df['separation_m'].values,
        force_N=harmonized_df['force_N'].values,
        covariance_matrix=cov,
        experiment_id=harmonized_df['experiment_id'].iloc[0]
    )
    
    assert dataset.experiment_id == 'test_001'
    assert dataset.force_N.shape[0] == 21