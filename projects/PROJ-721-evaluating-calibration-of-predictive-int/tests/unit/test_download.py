import os
import json
import pandas as pd
import pytest
from code.download import stratified_sample_metadata, compare_distributions, generate_sampling_report

@pytest.fixture
def sample_metadata():
    data = {
        'series_id': [f's{i}' for i in range(100)],
        'frequency': ['monthly'] * 50 + ['quarterly'] * 30 + ['yearly'] * 20,
        'seasonality': ['yes'] * 80 + ['no'] * 20
    }
    # Create a mix
    df = pd.DataFrame(data)
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df

def test_stratified_sample_metadata(sample_metadata):
    strata = ['frequency', 'seasonality']
    sample_size = 20
    sample_df = stratified_sample_metadata(sample_metadata, strata, sample_size, seed=42)
    
    assert len(sample_df) == sample_size
    assert set(sample_df.columns) == set(sample_metadata.columns)
    
    # Check that all strata present in full are in sample (if possible)
    full_strata = set(sample_metadata.groupby(strata).size().index)
    sample_strata = set(sample_df.groupby(strata).size().index)
    # With our logic, we try to include at least one from each group
    # But if a group is very small, it might be missed if sample_size is too small?
    # Our logic forces 1 per group if needed.
    # So sample_strata should be a superset or equal to the intersection.
    # Actually, we force 1 per group, so all groups should be represented.
    assert sample_strata == full_strata

def test_compare_distributions(sample_metadata):
    strata = ['frequency', 'seasonality']
    sample_df = stratified_sample_metadata(sample_metadata, strata, 50, seed=42)
    
    result = compare_distributions(sample_metadata, sample_df, strata)
    
    assert 'coverage' in result
    assert 'details' in result
    assert 0.0 <= result['coverage'] <= 1.0
    # With stratified sampling, coverage should be high
    assert result['coverage'] >= 0.90

def test_generate_sampling_report(tmp_path, sample_metadata):
    strata = ['frequency', 'seasonality']
    sample_df = stratified_sample_metadata(sample_metadata, strata, 50, seed=42)
    
    output_path = os.path.join(tmp_path, "test_report.json")
    generate_sampling_report(sample_metadata, sample_df, strata, output_path)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert 'total_series' in report
    assert 'sample_size' in report
    assert 'distribution_coverage' in report
    assert 'sample_indices' in report
    assert report['sample_size'] == 50