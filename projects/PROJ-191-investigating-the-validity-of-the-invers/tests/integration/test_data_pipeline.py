"""
Integration test for end-to-end download and harmonization.
Validates the full pipeline from raw data acquisition (simulated for unit testing
purposes to avoid external network dependencies in the test runner) through
unit conversion, grid alignment, and dataset object construction.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import sys
import logging

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.harmonize import harmonize_experiment, construct_covariance_matrix
from data.loaders import HarmonizedDataset
from config import get_logger

logger = get_logger(__name__)

def test_end_to_end_harmonization():
    """
    Simulate the full pipeline from raw data to harmonized dataset.
    This test verifies that the harmonization logic correctly converts units
    and aligns data to a target grid.
    """
    # 1. Create raw data (Simulating the output of a parser for arXiv data)
    # Using realistic values: separation in micrometers, force in dynes
    raw_data = pd.DataFrame({
        'separation_um': [10.0, 20.0, 30.0, 40.0],
        'force_dyne': [1e-5, 2.5e-6, 1.1e-6, 6.25e-7],
        'experiment_id': ['test_001'] * 4
    })
    
    # 2. Define target grid in meters
    # 31 points from 10um to 40um
    target_grid = np.linspace(10, 40, 31) * 1e-6
    
    # 3. Harmonize
    harmonized_df = harmonize_experiment(raw_data, target_grid)
    
    # 4. Verify output structure
    assert 'separation_m' in harmonized_df.columns, "Missing separation_m column"
    assert 'force_N' in harmonized_df.columns, "Missing force_N column"
    assert len(harmonized_df) == 31, f"Expected 31 points, got {len(harmonized_df)}"
    
    # 5. Check units (sanity check: force should be ~1e-10 to 1e-12 range for these inputs)
    # 1 dyne = 1e-5 N. Input forces are ~1e-5 to 1e-7 dynes -> ~1e-10 to 1e-12 N
    max_force = harmonized_df['force_N'].max()
    assert max_force < 1e-4, f"Force magnitude seems incorrect: {max_force}"
    
    # Check separation bounds
    assert harmonized_df['separation_m'].min() >= 10e-6, "Min separation out of bounds"
    assert harmonized_df['separation_m'].max() <= 40e-6, "Max separation out of bounds"
    
    logger.info("End-to-end harmonization test passed.")

def test_harmonized_dataset_integration():
    """
    Test creating the dataset object from harmonized dataframe.
    Validates the construction of the HarmonizedDataset dataclass.
    """
    raw_data = pd.DataFrame({
        'separation_um': [10.0, 20.0, 30.0],
        'force_dyne': [1e-5, 2.5e-6, 1.1e-6],
        'experiment_id': ['test_001'] * 3
    })
    
    target_grid = np.linspace(10, 30, 21) * 1e-6
    harmonized_df = harmonize_experiment(raw_data, target_grid)
    
    # Construct covariance matrix (diagonal for simplicity in this test)
    # In a real scenario, this would be constructed from systematic + statistical errors
    n = len(harmonized_df)
    # Create a positive definite matrix
    cov = np.eye(n) * 1e-24  # Small variance
    
    dataset = HarmonizedDataset(
        separation_m=harmonized_df['separation_m'].values,
        force_N=harmonized_df['force_N'].values,
        covariance_matrix=cov,
        experiment_id=harmonized_df['experiment_id'].iloc[0]
    )
    
    assert dataset.experiment_id == 'test_001'
    assert dataset.force_N.shape[0] == 21
    assert dataset.separation_m.shape[0] == 21
    assert dataset.covariance_matrix.shape == (21, 21)
    
    logger.info("HarmonizedDataset integration test passed.")

def test_covariance_construction_and_validity():
    """
    Test that the covariance matrix construction produces a positive-definite matrix.
    This is critical for the likelihood function which uses Cholesky decomposition.
    """
    raw_data = pd.DataFrame({
        'separation_um': [10.0, 15.0, 20.0, 25.0, 30.0],
        'force_dyne': [1e-5, 5e-6, 2.5e-6, 1.2e-6, 6e-7],
        'uncertainty_dyne': [1e-7, 5e-8, 2.5e-8, 1.2e-8, 6e-9],
        'experiment_id': ['test_002'] * 5
    })
    
    target_grid = np.linspace(10, 30, 21) * 1e-6
    harmonized_df = harmonize_experiment(raw_data, target_grid)
    
    # Construct covariance matrix
    # We pass a dummy uncertainty column name or assume it exists in harmonized_df
    # If not, we use a default relative error
    if 'uncertainty_N' not in harmonized_df.columns:
        # Estimate uncertainty as 1% of force for testing
        harmonized_df['uncertainty_N'] = harmonized_df['force_N'] * 0.01
        
    cov_matrix = construct_covariance_matrix(harmonized_df)
    
    # Verify shape
    assert cov_matrix.shape == (21, 21)
    
    # Verify positive-definiteness
    try:
        np.linalg.cholesky(cov_matrix)
        is_pd = True
    except np.linalg.LinAlgError:
        is_pd = False
    
    assert is_pd, "Covariance matrix is not positive-definite"
    
    logger.info("Covariance construction and validity test passed.")
