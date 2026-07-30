"""
Unit tests for batch_correction module.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock rpy2 if not available in test environment, but the task requires real execution.
# For unit tests, we mock the R calls.
try:
    from src.data.batch_correction import (
        calculate_cv_for_genes,
        calculate_cv_reduction,
        apply_batch_correction,
        calculate_georm_m_value
    )
except ImportError:
    # If rpy2 is not installed, we might skip or mock heavily.
    # But the task requires the code to be runnable.
    # We assume rpy2 is installed for the test environment.
    pass

@pytest.fixture
def sample_tpm_matrix():
    """Create a sample count matrix (genes x samples)."""
    np.random.seed(42)
    genes = 100
    samples = 10
    # Generate log-normal distributed counts
    data = np.random.lognormal(mean=2, sigma=1, size=(genes, samples))
    df = pd.DataFrame(data, index=[f"GENE_{i}" for i in range(genes)], 
                      columns=[f"SAMPLE_{i}" for i in range(samples)])
    return df

@pytest.fixture
def housekeeping_genes():
    """Return a list of housekeeping gene names."""
    return [f"GENE_{i}" for i in range(10)]  # First 10 genes as HK

@pytest.fixture
def temp_tpm_file(sample_tpm_matrix):
    """Save sample matrix to a temp CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_tpm_matrix.to_csv(f.name)
        return f.name

@pytest.fixture
def temp_report_path():
    """Return a temp path for the report."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        return f.name

def test_calculate_cv_for_genes():
    """Test CV calculation."""
    # Create a matrix with known CV
    # Gene 1: constant value 10 -> CV = 0
    # Gene 2: values 10, 20 -> mean=15, std=7.07 -> CV = 0.47
    data = np.array([
        [10, 10, 10],
        [10, 20, 15]
    ])
    indices = [0, 1]
    cv = calculate_cv_for_genes(data, indices)
    # Check that CV is calculated correctly (approx)
    assert 0.1 < cv < 0.6

def test_calculate_cv_reduction():
    """Test CV reduction calculation."""
    assert calculate_cv_reduction(1.0, 0.5) == 50.0
    assert calculate_cv_reduction(1.0, 1.0) == 0.0
    assert calculate_cv_reduction(1.0, 0.0) == 100.0
    assert calculate_cv_reduction(0.0, 0.0) == 0.0

@patch('src.data.batch_correction._init_r_packages')
@patch('src.data.batch_correction.apply_combat_seq')
@patch('src.data.batch_correction.get_housekeeping_genes')
def test_batch_correction_logic(
    mock_get_hk, 
    mock_combat, 
    mock_init_r,
    temp_tpm_file,
    temp_report_path
):
    """Test the main batch correction logic with mocked R calls."""
    # Setup mocks
    mock_init_r.return_value = (MagicMock(), MagicMock(), MagicMock())
    mock_combat.return_value = np.ones((100, 10)) * 10  # Corrected matrix
    mock_get_hk.return_value = [f"GENE_{i}" for i in range(10)]
    
    # Mock batch mapping
    batch_mapping = {f"SAMPLE_{i}": "batch_A" if i < 5 else "batch_B" for i in range(10)}
    batch_file = temp_tpm_file.replace('.csv', '_batches.json')
    with open(batch_file, 'w') as f:
        json.dump(batch_mapping, f)
    
    # Run
    result = apply_batch_correction(
        counts_matrix_path=temp_tpm_file,
        batch_labels=list(batch_mapping.values()),
        output_manifest_path=temp_report_path,
        gene_ids=[f"GENE_{i}" for i in range(100)]
    )
    
    # Assertions
    assert 'pre_correction_cv' in result
    assert 'post_correction_cv' in result
    assert 'reduction_percent' in result
    assert os.path.exists(temp_report_path)
    
    with open(temp_report_path, 'r') as f:
        report = json.load(f)
    assert 'pre_correction_cv' in report
    assert 'post_correction_cv' in report
    assert 'reduction_percent' in report

def test_calculate_georm_m_value():
    """Test M-value calculation."""
    # Create a small matrix
    data = np.array([
        [10, 10, 10],
        [10, 10, 10],
        [10, 20, 10]
    ])
    gene_ids = ["G1", "G2", "G3"]
    m_values = calculate_georm_m_value(data, gene_ids)
    
    # G1 and G2 should have low M-values (stable)
    # G3 should have higher M-value (less stable)
    assert m_values["G1"] < m_values["G3"]
    assert m_values["G2"] < m_values["G3"]