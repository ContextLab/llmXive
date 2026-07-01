"""
Integration test for preprocessing pipeline: verify VIF calculation and missing value handling.
Depends on: T014 completion (code/preprocessing/preprocess.py).

This test verifies that:
1. The VIF calculation correctly identifies collinear features.
2. Missing value handling (imputation or dropping) works as expected.
3. The preprocessing pipeline produces the correct output structure.
"""
import os
import sys
import json
import tempfile
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.preprocessing.preprocess import calculate_vif, run_preprocessing
from code.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_vif_calculation():
    """Test that VIF calculation correctly identifies collinear features."""
    # Create a dataset with known collinearity
    np.random.seed(42)
    n_samples = 100
    
    # Feature A and B are highly correlated (collinear)
    feature_a = np.random.normal(0, 1, n_samples)
    feature_b = feature_a * 0.95 + np.random.normal(0, 0.1, n_samples)  # High correlation
    
    # Feature C is independent
    feature_c = np.random.normal(0, 1, n_samples)
    
    # Target variable
    agency_score = 0.5 * feature_a + 0.3 * feature_b + 0.2 * feature_c + np.random.normal(0, 0.1, n_samples)
    
    df = pd.DataFrame({
        'feature_a': feature_a,
        'feature_b': feature_b,
        'feature_c': feature_c,
        'agency_score': agency_score
    })
    
    # Calculate VIF for each feature (excluding target)
    features = ['feature_a', 'feature_b', 'feature_c']
    vif_results = calculate_vif(df, features)
    
    logger.info(f"VIF Results: {vif_results}")
    
    # Check that VIF is calculated for all features
    assert len(vif_results) == len(features), "VIF should be calculated for all features"
    
    # Check that collinear features (A and B) have high VIF (> 5)
    # Note: Due to random noise, we expect VIF > 5 for highly correlated features
    assert vif_results['feature_a'] > 5.0, f"Feature A should have VIF > 5, got {vif_results['feature_a']}"
    assert vif_results['feature_b'] > 5.0, f"Feature B should have VIF > 5, got {vif_results['feature_b']}"
    
    # Check that independent feature has low VIF
    assert vif_results['feature_c'] < 5.0, f"Feature C should have VIF < 5, got {vif_results['feature_c']}"
    
    logger.info("VIF calculation test passed.")


def test_missing_value_handling():
    """Test that missing value handling works correctly."""
    # Create a dataset with missing values
    np.random.seed(42)
    n_samples = 100
    
    df = pd.DataFrame({
        'feature_a': np.random.normal(0, 1, n_samples),
        'feature_b': np.random.normal(0, 1, n_samples),
        'feature_c': np.random.normal(0, 1, n_samples),
        'agency_score': np.random.normal(0.5, 0.2, n_samples)
    })
    
    # Introduce missing values
    df.loc[0:4, 'feature_a'] = np.nan
    df.loc[5:9, 'feature_b'] = np.nan
    df.loc[10:14, 'feature_c'] = np.nan
    
    # Count missing values before processing
    missing_before = df.isnull().sum()
    logger.info(f"Missing values before processing: {missing_before.to_dict()}")
    
    # Run preprocessing with missing value handling
    # The run_preprocessing function should handle missing values
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.csv"
        output_path = Path(temp_dir) / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        config = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "handle_missing": "drop",  # Drop rows with missing values
            "vif_threshold": 5.0
        }
        
        result = run_preprocessing(config)
        
        # Load processed data
        processed_df = pd.read_csv(output_path)
        
        # Verify no missing values in output
        missing_after = processed_df.isnull().sum()
        logger.info(f"Missing values after processing: {missing_after.to_dict()}")
        
        assert missing_after.sum() == 0, "Processed data should have no missing values"
        
        # Verify that rows with missing values were dropped
        # Original had 15 rows with missing values (some might overlap)
        # We expect fewer rows in output
        assert len(processed_df) < len(df), "Rows with missing values should be dropped"
        
        logger.info("Missing value handling test passed.")


def test_preprocessing_pipeline_integration():
    """Integration test for the full preprocessing pipeline."""
    # Create a realistic dataset
    np.random.seed(42)
    n_samples = 150
    
    # Simulate motion features
    latency = np.random.normal(0.2, 0.05, n_samples)
    smoothness = np.random.normal(0.8, 0.1, n_samples)
    lead_time = np.random.normal(0.3, 0.08, n_samples)
    
    # Add some collinearity (lead_time and latency might be correlated in real data)
    lead_time = lead_time + 0.3 * (latency - 0.2)
    
    # Generate agency score based on features
    agency_score = (
        0.4 * (1 - latency) +  # Lower latency -> higher agency
        0.4 * smoothness +      # Higher smoothness -> higher agency
        0.2 * lead_time +       # Higher lead_time -> higher agency
        np.random.normal(0, 0.1, n_samples)
    )
    
    # Clip agency score to [0, 1] range
    agency_score = np.clip(agency_score, 0, 1)
    
    df = pd.DataFrame({
        'latency': latency,
        'smoothness': smoothness,
        'lead_time': lead_time,
        'agency_score': agency_score
    })
    
    # Add some missing values
    df.loc[0:2, 'latency'] = np.nan
    df.loc[3:5, 'smoothness'] = np.nan
    
    with tempfile.TemporaryDirectory() as temp_dir:
        input_path = Path(temp_dir) / "input.csv"
        output_path = Path(temp_dir) / "output.csv"
        vif_log_path = Path(temp_dir) / "vif_log.json"
        
        df.to_csv(input_path, index=False)
        
        config = {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "vif_log_path": str(vif_log_path),
            "handle_missing": "drop",
            "vif_threshold": 5.0,
            "standardize": True
        }
        
        result = run_preprocessing(config)
        
        # Verify output file exists
        assert Path(output_path).exists(), "Output file should be created"
        
        # Load and verify processed data
        processed_df = pd.read_csv(output_path)
        
        # Check columns
        expected_columns = {'latency', 'smoothness', 'lead_time', 'agency_score'}
        assert set(processed_df.columns) == expected_columns, f"Expected columns {expected_columns}, got {set(processed_df.columns)}"
        
        # Check no missing values
        assert processed_df.isnull().sum().sum() == 0, "Processed data should have no missing values"
        
        # Check VIF log file
        assert Path(vif_log_path).exists(), "VIF log file should be created"
        
        with open(vif_log_path, 'r') as f:
            vif_log = json.load(f)
        
        assert 'vif_values' in vif_log, "VIF log should contain vif_values"
        assert 'features_flagged' in vif_log, "VIF log should contain features_flagged"
        
        logger.info(f"VIF log: {vif_log}")
        
        # Verify that the pipeline ran successfully
        assert result['success'], "Preprocessing should succeed"
        assert result['n_samples'] == len(processed_df), "Sample count should match"
        
        logger.info("Preprocessing pipeline integration test passed.")


if __name__ == "__main__":
    # Run tests
    test_vif_calculation()
    test_missing_value_handling()
    test_preprocessing_pipeline_integration()
    print("All integration tests passed.")