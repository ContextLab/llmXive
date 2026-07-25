import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from sensitivity_analysis import run_sensitivity_analysis, generate_sensitivity_table

def test_run_sensitivity_analysis_basic():
    """Test that sensitivity analysis correctly counts significant channels."""
    # Create mock data with known p-values
    data = {
        'channel': ['C1', 'C2', 'C3', 'C4', 'C5'],
        'p_value': [0.04, 0.06, 0.01, 0.10, 0.005]
    }
    df = pd.DataFrame(data)
    
    # Test at p <= 0.05
    result = run_sensitivity_analysis(df, thresholds=[0.05])
    assert len(result) == 1
    assert result.iloc[0]['threshold'] == 0.05
    assert result.iloc[0]['count_significant'] == 3  # C1, C3, C5
    
    # Test at p <= 0.01
    result = run_sensitivity_analysis(df, thresholds=[0.01])
    assert result.iloc[0]['threshold'] == 0.01
    assert result.iloc[0]['count_significant'] == 1  # Only C5

def test_run_sensitivity_analysis_multiple_thresholds():
    """Test sensitivity analysis with multiple thresholds."""
    data = {
        'channel': ['C1', 'C2', 'C3'],
        'p_value': [0.04, 0.02, 0.001]
    }
    df = pd.DataFrame(data)
    
    result = run_sensitivity_analysis(df, thresholds=[0.05, 0.01])
    assert len(result) == 2
    
    # Check 0.05 threshold
    row_05 = result[result['threshold'] == 0.05].iloc[0]
    assert row_05['count_significant'] == 3
    
    # Check 0.01 threshold
    row_01 = result[result['threshold'] == 0.01].iloc[0]
    assert row_01['count_significant'] == 1

def test_generate_sensitivity_table_saves_file(tmp_path):
    """Test that generate_sensitivity_table writes a valid CSV."""
    data = {
        'channel': ['C1', 'C2'],
        'p_value': [0.04, 0.06]
    }
    df = pd.DataFrame(data)
    
    output_path = tmp_path / "sensitivity_table.csv"
    result_df = generate_sensitivity_table(df, output_path)
    
    # Verify file exists
    assert output_path.exists()
    
    # Verify content
    saved_df = pd.read_csv(output_path)
    assert 'threshold' in saved_df.columns
    assert 'count_significant' in saved_df.columns
    assert len(saved_df) == 2  # Two thresholds
    
    # Verify values
    row_05 = saved_df[saved_df['threshold'] == 0.05].iloc[0]
    assert row_05['count_significant'] == 1
    
    row_01 = saved_df[saved_df['threshold'] == 0.01].iloc[0]
    assert row_01['count_significant'] == 0

def test_generate_sensitivity_table_schema():
    """Test that the output CSV strictly matches the required schema."""
    data = {
        'channel': ['C1'],
        'p_value': [0.04]
    }
    df = pd.DataFrame(data)
    
    # Use a temporary directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "sensitivity_table.csv"
        generate_sensitivity_table(df, output_path)
        
        saved_df = pd.read_csv(output_path)
        
        # Check exact column names and types
        assert list(saved_df.columns) == ['threshold', 'count_significant']
        assert saved_df['threshold'].dtype in ['float64', 'float32']
        assert saved_df['count_significant'].dtype in ['int64', 'int32']
