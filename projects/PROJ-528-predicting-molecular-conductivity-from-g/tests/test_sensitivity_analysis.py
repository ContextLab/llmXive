import pytest
import os
import json
import pandas as pd
import numpy as np
from scipy.stats import kruskal

from code.sensitivity_analysis import run_sensitivity_analysis
from code.config import SEED, DATA_PATH

@pytest.fixture
def sample_descriptors(tmp_path):
    """Create a sample descriptors CSV for testing"""
    data = {
        'smiles': ['CCO', 'CCCO', 'CCCCO', 'c1ccccc1', 'c1ccccc1O', 
                  'CC=CC', 'C=CC=C', 'CCCC', 'CCCCC', 'CCCCCC'] * 100,
        'status': ['valid'] * 1000,
        'degree_mean': np.random.uniform(1.5, 3.5, 1000),
        'degree_std': np.random.uniform(0.1, 0.5, 1000),
        'degree_max': np.random.uniform(3, 5, 1000),
        'degree_min': np.random.uniform(1, 2, 1000),
        'path_length_mean': np.random.uniform(2, 5, 1000),
        'path_length_std': np.random.uniform(0.5, 1.5, 1000),
        'path_length_max': np.random.uniform(5, 10, 1000),
        'path_length_min': np.random.uniform(2, 4, 1000),
        'aromaticity_index': np.random.uniform(0, 1, 1000),
        'conjugation_length': np.random.uniform(0, 10, 1000),
        'ring_count': np.random.randint(0, 3, 1000),
        'bond_polarity': np.random.uniform(0, 2, 1000),
        'resonance_energy': np.random.uniform(0, 50, 1000),
        'conductivity': np.random.uniform(-5, 5, 1000)
    }
    df = pd.DataFrame(data)
    output_path = os.path.join(tmp_path, 'descriptors.csv')
    df.to_csv(output_path, index=False)
    return output_path

def test_run_sensitivity_analysis_creates_output(tmp_path, sample_descriptors):
    """Test that sensitivity analysis creates the expected output file"""
    output_path = os.path.join(tmp_path, 'sensitivity_analysis.json')
    
    results = run_sensitivity_analysis(
        thresholds=[1.0, 3.0],
        input_path=sample_descriptors,
        output_path=output_path
    )
    
    assert os.path.exists(output_path)
    assert 'thresholds_tested' in results
    assert 'results' in results
    assert len(results['results']) == 2
    
    for res in results['results']:
        assert 'threshold' in res
        assert 'r2' in res
        assert 'kruskal_stat' in res or res['r2'] is None
        assert 'kruskal_pval' in res or res['r2'] is None

def test_sensitivity_analysis_with_extreme_thresholds(tmp_path, sample_descriptors):
    """Test behavior with thresholds that remove most data"""
    output_path = os.path.join(tmp_path, 'sensitivity_analysis.json')
    
    # Use extreme thresholds
    results = run_sensitivity_analysis(
        thresholds=[0.1, 10.0],
        input_path=sample_descriptors,
        output_path=output_path
    )
    
    assert 'results' in results
    # At least some results should be recorded
    assert len(results['results']) > 0

def test_kruskal_wallis_computation(tmp_path, sample_descriptors):
    """Test that Kruskal-Wallis statistics are computed"""
    output_path = os.path.join(tmp_path, 'sensitivity_analysis.json')
    
    results = run_sensitivity_analysis(
        thresholds=[1.0, 2.0, 3.0],
        input_path=sample_descriptors,
        output_path=output_path
    )
    
    # Check that Kruskal-Wallis results are present
    for res in results['results']:
        if res['r2'] is not None:
            assert res['kruskal_stat'] is not None
            assert res['kruskal_pval'] is not None
            assert isinstance(res['kruskal_stat'], float)
            assert isinstance(res['kruskal_pval'], float)

def test_invalid_input_path_raises_error():
    """Test that missing input file raises appropriate error"""
    with pytest.raises(FileNotFoundError):
        run_sensitivity_analysis(
            input_path='/nonexistent/path.csv',
            output_path='/tmp/test.json'
        )