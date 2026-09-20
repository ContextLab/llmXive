"""
Unit tests for the transform module.
"""
import os
import json
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from transform import apply_clr_transformation, detect_compositionality, manual_clr, transform_data

def test_manual_clr_basic():
    """Test basic CLR transformation on a simple array."""
    # Input: [1, 2, 3]
    # Geometric mean: (1*2*3)^(1/3) = 1.332
    # Log values: [0, 0.693, 1.099]
    # Mean of log: 0.493
    # CLR: [-0.493, 0.199, 0.606]
    values = np.array([1.0, 2.0, 3.0])
    result = manual_clr(values, pseudo_count=1e-6)
    
    # Check that result sum is approximately 0 (property of CLR)
    assert np.isclose(np.sum(result), 0.0, atol=1e-6), "CLR values should sum to 0"
    assert len(result) == len(values), "Output length should match input"

def test_apply_clr_transformation_dataframe():
    """Test CLR transformation on a DataFrame."""
    df = pd.DataFrame({
        'A': [1.0, 2.0, 3.0],
        'B': [4.0, 5.0, 6.0],
        'C': [7.0, 8.0, 9.0]
    })
    
    result = apply_clr_transformation(df, predictor_cols=['A', 'B'])
    
    # Check that transformed columns sum to ~0 per row
    row_sums = result[['A', 'B']].sum(axis=1)
    assert np.allclose(row_sums, 0.0, atol=1e-6), "CLR rows should sum to 0"
    
    # Check that non-transformed column C is unchanged
    assert np.allclose(result['C'], df['C']), "Non-transformed columns should be unchanged"

def test_detect_compositionality_true():
    """Test detection of compositional data (sums ~ 1)."""
    df = pd.DataFrame({
        'A': [0.2, 0.3, 0.4],
        'B': [0.3, 0.4, 0.3],
        'C': [0.5, 0.3, 0.3]
    })
    
    is_comp = detect_compositionality(df, predictor_cols=['A', 'B', 'C'])
    assert is_comp is True, "Should detect compositional data"

def test_detect_compositionality_false():
    """Test detection of non-compositional data."""
    df = pd.DataFrame({
        'A': [10.0, 20.0, 30.0],
        'B': [40.0, 50.0, 60.0]
    })
    
    is_comp = detect_compositionality(df, predictor_cols=['A', 'B'])
    assert is_comp is False, "Should not detect compositional data"

def test_transform_data_integration():
    """Integration test for the full transform_data function."""
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "output.parquet")
        metadata_path = os.path.join(tmpdir, "metadata.json")
        log_path = os.path.join(tmpdir, "log.json")
        
        # Create test data
        df = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'taxon_A': [0.2, 0.3, 0.4],
            'taxon_B': [0.3, 0.4, 0.3],
            'taxon_C': [0.5, 0.3, 0.3]
        })
        df.to_csv(input_path, index=False)
        
        # Run transformation
        transform_data(
            input_path=input_path,
            output_path=output_path,
            metadata_path=metadata_path,
            method_selection_log_path=log_path,
            predictor_cols=['taxon_A', 'taxon_B', 'taxon_C']
        )
        
        # Verify output file exists
        assert os.path.exists(output_path), "Output file should exist"
        
        # Load and verify output
        result_df = pd.read_parquet(output_path)
        assert len(result_df) == 3, "Row count should match"
        
        # Verify log file
        assert os.path.exists(log_path), "Log file should exist"
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        assert "transformation_log" in log_data, "Log should contain transformation_log"
        assert log_data["transformation_log"][0]["transformation_method"] == "CLR", "Method should be CLR"
