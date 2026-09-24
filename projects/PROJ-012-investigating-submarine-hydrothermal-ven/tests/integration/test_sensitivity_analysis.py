"""
Integration test for Sensitivity Analysis (Task T026).

Verifies that the sensitivity analysis script runs successfully,
processes multiple rarefaction depths, and produces a valid JSON output
with stability metrics.
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Import the function to test
from sensitivity_analysis import run_sensitivity_analysis

@pytest.fixture
def mock_data(tmp_path):
    """
    Create mock OTU table and metadata for testing.
    """
    # Create mock OTU table (samples as rows, OTUs as columns)
    np.random.seed(42)
    n_samples = 20
    n_otus = 100
    
    # Generate counts that ensure most samples have > 20000 reads
    # to pass all rarefaction depths
    counts = np.random.poisson(lam=500, size=(n_samples, n_otus))
    otu_df = pd.DataFrame(counts, columns=[f'OTU_{i}' for i in range(n_otus)])
    otu_df.index = [f'Sample_{i}' for i in range(n_samples)]
    
    # Save OTU table
    otu_path = tmp_path / "otu_table.tsv"
    otu_df.to_csv(otu_path, sep='\t')
    
    # Create mock metadata
    metadata = pd.DataFrame({
        'sample_id': otu_df.index,
        'pH': np.random.uniform(6.0, 8.5, n_samples),
        'site': np.random.choice(['Site_A', 'Site_B', 'Site_C'], n_samples)
    })
    
    meta_path = tmp_path / "metadata.csv"
    metadata.to_csv(meta_path, index=False)
    
    return str(otu_path), str(meta_path), tmp_path

def test_sensitivity_analysis_execution(mock_data):
    """
    Test that the sensitivity analysis runs without error and produces valid JSON.
    """
    otu_path, meta_path, tmp_path = mock_data
    output_path = tmp_path / "sensitivity_log.json"
    
    # Run the analysis
    result = run_sensitivity_analysis(
        otu_table_path=otu_path,
        metadata_path=meta_path,
        depths=[5000, 10000, 20000],
        output_path=output_path
    )
    
    # Verify output file exists
    assert output_path.exists(), "Output JSON file was not created."
    
    # Verify JSON structure
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'task_id' in data
    assert data['task_id'] == 'T026'
    assert 'depths_tested' in data
    assert 5000 in data['depths_tested']
    assert 10000 in data['depths_tested']
    assert 20000 in data['depths_tested']
    assert 'results' in data
    assert len(data['results']) == 3 # One for each depth
    
    # Verify each result has required fields
    for res in data['results']:
        assert 'depth' in res
        assert 'status' in res
        if res['status'] == 'success':
            assert 'lme_pH_estimate' in res
            assert 'lme_pH_se' in res
            assert 'lme_pH_p_value' in res
            assert 'sample_count' in res
    
    # Verify stability metrics exist
    assert 'stability_metrics' in data
    assert 'interpretation' in data['stability_metrics']
    
    # Verify at least one successful run (given our mock data generation)
    successful = [r for r in data['results'] if r['status'] == 'success']
    assert len(successful) > 0, "No successful runs occurred in mock test."

def test_sensitivity_analysis_insufficient_samples(mock_data):
    """
    Test behavior when samples don't have enough reads for a specific depth.
    """
    otu_path, meta_path, tmp_path = mock_data
    
    # Create a very low-depth mock OTU table
    np.random.seed(1)
    n_samples = 10
    counts = np.random.poisson(lam=10, size=(n_samples, 10)) # Very low counts
    otu_df = pd.DataFrame(counts, columns=[f'OTU_{i}' for i in range(10)])
    otu_df.index = [f'Sample_{i}' for i in range(n_samples)]
    
    low_otu_path = tmp_path / "low_otu.tsv"
    otu_df.to_csv(low_otu_path, sep='\t')
    
    output_path = tmp_path / "low_depth_log.json"
    
    # Run with a high depth that should fail
    result = run_sensitivity_analysis(
        otu_table_path=str(low_otu_path),
        metadata_path=meta_path,
        depths=[5000, 10000],
        output_path=output_path
    )
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # All should be skipped
    for res in data['results']:
        assert res['status'] == 'skipped'
        assert res['reason'] == 'insufficient_samples'