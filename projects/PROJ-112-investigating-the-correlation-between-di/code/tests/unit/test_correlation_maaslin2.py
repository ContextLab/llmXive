import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from src.analysis.correlation_maaslin2 import (
    get_project_root,
    calculate_fisher_se,
    compute_spearman_correlations,
    merge_and_finalize_results,
    run_correlation_analysis
)

@pytest.fixture
def sample_taxon_data():
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'taxon_A': [0.1, 0.2, 0.15, 0.3, 0.25],
        'taxon_B': [0.5, 0.4, 0.6, 0.3, 0.45],
        'fiber_g_day': [10, 20, 15, 30, 25],
        'age': [30, 40, 35, 50, 45],
        'BMI': [22, 25, 24, 28, 26],
        'antibiotic_use': [0, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    df.set_index('sample_id', inplace=True)
    return df

@pytest.fixture
def sample_metadata():
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'fiber_g_day': [10, 20, 15, 30, 25],
        'age': [30, 40, 35, 50, 45],
        'BMI': [22, 25, 24, 28, 26],
        'antibiotic_use': [0, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    df.set_index('sample_id', inplace=True)
    return df

@pytest.fixture
def temp_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_fisher_se():
    # Test basic calculation
    rho = 0.5
    n = 100
    se = calculate_fisher_se(rho, n)
    expected_se = (1.0 / np.sqrt(n - 3)) * (1 - rho**2)
    assert np.isclose(se, expected_se)

    # Test edge case n <= 3
    assert np.isinf(calculate_fisher_se(0.5, 3))
    assert np.isinf(calculate_fisher_se(0.5, 2))

def test_compute_spearman_correlations(sample_taxon_data, sample_metadata):
    # Extract taxa only
    taxa_df = sample_taxon_data[['taxon_A', 'taxon_B']]
    
    results = compute_spearman_correlations(taxa_df, sample_metadata, target_feature="fiber_g_day")
    
    assert 'taxon' in results.columns
    assert 'spearman_rho' in results.columns
    assert 'spearman_p_value' in results.columns
    assert 'spearman_se' in results.columns
    assert len(results) == 2

def test_merge_and_finalize_results(temp_files):
    # Mock MaAsLin2 results
    maaslin2_data = {
        'taxon': ['taxon_A', 'taxon_B'],
        'maaslin2_beta': [0.1, -0.2],
        'maaslin2_se': [0.05, 0.06],
        'maaslin2_p_value': [0.01, 0.04],
        'maaslin2_q_value': [0.02, 0.08]
    }
    maaslin2_df = pd.DataFrame(maaslin2_data)

    # Mock Spearman results
    spearman_data = {
        'taxon': ['taxon_A', 'taxon_B'],
        'spearman_rho': [0.5, -0.3],
        'spearman_p_value': [0.02, 0.05],
        'spearman_se': [0.1, 0.12]
    }
    spearman_df = pd.DataFrame(spearman_data)

    merged = merge_and_finalize_results(maaslin2_df, spearman_df, pd.DataFrame())

    assert 'taxon' in merged.columns
    assert 'maaslin2_beta' in merged.columns
    assert 'spearman_rho' in merged.columns
    assert len(merged) == 2

@patch('src.analysis.correlation_maaslin2.run_maaslin2')
@patch('src.analysis.correlation_maaslin2.compute_spearman_correlations')
@patch('src.analysis.correlation_maaslin2.merge_and_finalize_results')
def test_run_correlation_analysis(mock_merge, mock_spearman, mock_maaslin2, sample_taxon_data, temp_files):
    # Mock inputs
    input_file = temp_files / "input.tsv"
    output_file = temp_files / "output.tsv"
    sample_taxon_data.to_csv(input_file, sep='\t')

    # Mock outputs
    mock_maaslin2.return_value = pd.DataFrame({
        'feature': ['taxon_A'],
        'coefficient': [0.1],
        'std_error': [0.05],
        'pval': [0.01],
        'qval': [0.02]
    })
    mock_spearman.return_value = pd.DataFrame({
        'taxon': ['taxon_A'],
        'spearman_rho': [0.5],
        'spearman_p_value': [0.02],
        'spearman_se': [0.1]
    })
    mock_merge.return_value = pd.DataFrame({
        'taxon': ['taxon_A'],
        'maaslin2_beta': [0.1],
        'maaslin2_se': [0.05],
        'maaslin2_p_value': [0.01],
        'maaslin2_q_value': [0.02],
        'spearman_rho': [0.5],
        'spearman_se': [0.1],
        'spearman_p_value': [0.02]
    })

    run_correlation_analysis(input_file, output_file)

    assert output_file.exists()
    mock_maaslin2.assert_called_once()
    mock_spearman.assert_called_once()
    mock_merge.assert_called_once()