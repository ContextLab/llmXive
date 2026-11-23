import os
import tempfile
import pandas as pd
import numpy as np
from analysis.plot_bias import load_and_prepare_data, aggregate_bias_by_beta, plot_bias_vs_beta

def test_load_and_prepare_data():
    """Test loading and preparing data for bias plot."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data = """beta,method,estimator,ate,bias,rmse,coverage_rate,seed,run_id,ground_truth_ate,beta_value,status
        0.0,mean,ipw,0.5,0.0,0.0,0.95,42,abc123,0.5,0.0,success
        0.5,mean,ipw,0.6,0.1,0.1,0.85,43,def456,0.5,0.5,success
        1.0,mean,ipw,0.8,0.3,0.3,0.70,44,ghi789,0.5,1.0,success"""
        f.write(data)
        temp_path = f.name
    
    try:
        df = load_and_prepare_data(temp_path)
        assert 'abs_bias' in df.columns
        assert len(df) == 3
        assert df['abs_bias'].iloc[0] == 0.0
        assert df['abs_bias'].iloc[1] == 0.1
        assert df['abs_bias'].iloc[2] == 0.3
    finally:
        os.unlink(temp_path)

def test_aggregate_bias_by_beta():
    """Test aggregation of bias by beta level."""
    df = pd.DataFrame({
        'beta': [0.0, 0.0, 0.5, 0.5, 1.0, 1.0],
        'abs_bias': [0.0, 0.1, 0.1, 0.2, 0.3, 0.4]
    })
    
    agg_df = aggregate_bias_by_beta(df)
    
    assert len(agg_df) == 3
    assert agg_df['beta'].tolist() == [0.0, 0.5, 1.0]
    assert agg_df['mean_abs_bias'].iloc[0] == 0.05
    assert agg_df['mean_abs_bias'].iloc[1] == 0.15
    assert agg_df['mean_abs_bias'].iloc[2] == 0.35

def test_plot_bias_vs_beta():
    """Test plot generation."""
    agg_df = pd.DataFrame({
        'beta': [0.0, 0.5, 1.0],
        'mean_abs_bias': [0.05, 0.15, 0.35],
        'std_abs_bias': [0.01, 0.02, 0.03]
    })
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        temp_path = f.name
    
    try:
        plot_bias_vs_beta(agg_df, temp_path)
        assert os.path.exists(temp_path)
        assert os.path.getsize(temp_path) > 1000  # Should be a real image
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_file_not_found():
    """Test error handling for missing input file."""
    try:
        load_and_prepare_data('nonexistent_file.csv')
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass  # Expected
