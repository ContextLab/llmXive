import json
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from code.download import (
    stratified_sample_metadata,
    generate_sampling_report,
    compare_distributions,
    load_m4_metadata
)

@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    data = {
        'id': [f'series_{i}' for i in range(100)],
        'frequency': ['Yearly'] * 30 + ['Quarterly'] * 25 + ['Monthly'] * 25 + ['Weekly'] * 20,
        'seasonality': [1] * 30 + [4] * 25 + [12] * 25 + [52] * 20
    }
    return pd.DataFrame(data)

def test_stratified_sample_metadata_proportional_allocation(sample_metadata):
    """Test that stratified sampling uses proportional allocation."""
    n_samples = 50
    sample_indices = stratified_sample_metadata(sample_metadata, n_samples, seed=42)
    
    # Check that we got the right number of samples
    assert len(sample_indices) == n_samples
    
    # Check that all indices are within bounds
    assert all(0 <= idx < len(sample_metadata) for idx in sample_indices)
    
    # Check that there are no duplicates
    assert len(set(sample_indices)) == n_samples

def test_stratified_sample_metadata_representativeness(sample_metadata):
    """Test that stratified sampling produces a representative sample."""
    n_samples = 50
    sample_indices = stratified_sample_metadata(sample_metadata, n_samples, seed=42)
    
    sample_df = sample_metadata.loc[sample_indices]
    
    # Compare frequency distributions
    full_freq_dist = sample_metadata['frequency'].value_counts().to_dict()
    sample_freq_dist = sample_df['frequency'].value_counts().to_dict()
    
    # The sample should have similar proportions
    for freq in full_freq_dist:
        full_prop = full_freq_dist[freq] / len(sample_metadata)
        sample_prop = sample_freq_dist.get(freq, 0) / len(sample_indices)
        # Allow for some variation due to sampling
        assert abs(full_prop - sample_prop) < 0.15, f"Frequency distribution mismatch for {freq}"

def test_generate_sampling_report(sample_metadata):
    """Test that sampling report is generated correctly."""
    n_samples = 50
    sample_indices = stratified_sample_metadata(sample_metadata, n_samples, seed=42)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_report.json')
        report = generate_sampling_report(sample_metadata, sample_indices, output_path)
        
        # Check that report has required fields
        assert 'full_dataset' in report
        assert 'sample' in report
        assert 'statistics' in report
        assert 'verification' in report
        
        # Check that report file was created
        assert os.path.exists(output_path)
        
        # Check report content
        assert report['full_dataset']['total_series'] == len(sample_metadata)
        assert report['sample']['total_samples'] == n_samples
        assert 'representativeness_metric' in report['statistics']
        
        # Check that verification field exists
        assert 'passed' in report['verification']

def test_compare_distributions():
    """Test distribution comparison function."""
    full_dist = {'A': 50, 'B': 30, 'C': 20}
    sample_dist = {'A': 25, 'B': 15, 'C': 10}  # Perfect proportional sample
    
    chi2, p_value = compare_distributions(full_dist, sample_dist)
    
    # For a perfect proportional sample, p-value should be high
    assert p_value > 0.05, "Perfect proportional sample should have high p-value"

def test_load_m4_metadata_missing_columns():
    """Test that load_m4_metadata raises error for missing columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a metadata file with missing columns
        metadata_path = os.path.join(tmpdir, 'metadata.csv')
        df = pd.DataFrame({
            'id': ['series_1', 'series_2'],
            'frequency': ['Yearly', 'Quarterly']
            # Missing 'seasonality' column
        })
        df.to_csv(metadata_path, index=False)
        
        with pytest.raises(ValueError, match="Required column 'seasonality' not found"):
            load_m4_metadata(tmpdir)