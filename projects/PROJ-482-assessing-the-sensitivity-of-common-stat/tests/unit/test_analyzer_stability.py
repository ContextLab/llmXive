import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from analyzer import load_simulation_results, aggregate_results, analyze_stability_trend

@pytest.fixture
def sample_raw_data():
    """Create a temporary CSV with simulated raw p-values for testing."""
    data = []
    # Generate synthetic but realistic looking data for testing purposes
    # We simulate 3 sample sizes, 2 distributions, 1 test, 100 replicates each
    sample_sizes = [10, 50, 100]
    distributions = ['normal', 'uniform']
    test_type = 't-test'
    
    for n in sample_sizes:
        for dist in distributions:
            # Simulate Null hypothesis (effect=0) -> p-values should be uniform [0,1]
            # We generate 100 random p-values for each config
            p_values = np.random.uniform(0, 1, 100)
            for p in p_values:
                data.append({
                    'sample_size': n,
                    'distribution_type': dist,
                    'test_type': test_type,
                    'p_value': p,
                    'hypothesis_type': 'Null'
                })
    
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def temp_input_file(sample_raw_data):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_raw_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_simulation_results(temp_input_file):
    df = load_simulation_results(temp_input_file)
    assert len(df) > 0
    assert 'p_value' in df.columns
    assert 'hypothesis_type' in df.columns

def test_aggregate_results(temp_input_file):
    df = load_simulation_results(temp_input_file)
    agg = aggregate_results(df)
    assert len(agg) > 0
    assert 'type_i_error_rate' in agg.columns
    # Check that error rates are between 0 and 1
    assert agg['type_i_error_rate'].between(0, 1).all()

def test_analyze_stability_trend(temp_input_file, temp_output_dir):
    df = load_simulation_results(temp_input_file)
    agg = aggregate_results(df)
    
    csv_path = os.path.join(temp_output_dir, 'stability_trend.csv')
    plot_path = os.path.join(temp_output_dir, 'stability_trend.png')
    
    result_df = analyze_stability_trend(agg, output_csv=csv_path, plot_path=plot_path)
    
    # Check CSV output
    assert os.path.exists(csv_path)
    assert 'sample_size' in result_df.columns
    assert 'mean_error_rate' in result_df.columns
    assert 'regression_slope' in result_df.columns
    
    # Check Plot output
    assert os.path.exists(plot_path)
    
    # Check trend analysis logic
    # For uniform p-values (Null), expected error rate is alpha (0.05)
    # The mean should be close to 0.05
    assert result_df['mean_error_rate'].between(0, 0.2).all() # Allow some variance

def test_analyze_stability_trend_empty_data(temp_output_dir):
    empty_df = pd.DataFrame(columns=['sample_size', 'distribution_type', 'test_type', 'type_i_error_rate'])
    csv_path = os.path.join(temp_output_dir, 'stability_trend.csv')
    plot_path = os.path.join(temp_output_dir, 'stability_trend.png')
    
    result_df = analyze_stability_trend(empty_df, output_csv=csv_path, plot_path=plot_path)
    assert result_df.empty
    # Should not crash, but return empty