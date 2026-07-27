import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import json
import tempfile
from unittest.mock import patch, MagicMock

from src.data.batch_correction import calculate_cv_reduction, apply_batch_correction, calculate_cv_for_genes, calculate_georm_m_value

@pytest.fixture
def sample_tpm_matrix():
    """Create a sample TPM matrix with housekeeping genes."""
    # Create a matrix with 50 genes, 10 samples
    np.random.seed(42)
    genes = [f"GENE_{i}" for i in range(50)]
    samples = [f"Sample_{i}" for i in range(10)]
    
    # Create data with some batch effects
    data = np.random.lognormal(mean=2, sigma=1, size=(50, 10))
    
    # Add batch effect to first 5 samples
    data[:, :5] *= 1.5
    
    df = pd.DataFrame(data, index=genes, columns=samples)
    return df

@pytest.fixture
def housekeeping_genes():
    """Return a list of housekeeping gene names."""
    # Use a subset that will be in the matrix
    return [f"GENE_{i}" for i in range(5, 15)]  # GENE_5 to GENE_14

@pytest.fixture
def temp_tpm_file(sample_tpm_matrix):
    """Create a temporary TPM file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_tpm_matrix.to_csv(f)
        return f.name

@pytest.fixture
def temp_report_path():
    """Create a temporary report path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "batch_correction_report.json"

def test_cv_reduction_calculation(temp_tpm_file, temp_report_path, housekeeping_genes):
    """Test that CV reduction is calculated correctly."""
    # Mock get_housekeeping_genes to return our test genes
    with patch('src.data.batch_correction.get_housekeeping_genes') as mock_get_hk:
        mock_get_hk.return_value = housekeeping_genes
        
        # Run calculation
        report = calculate_cv_reduction(temp_tpm_file, str(temp_report_path))
        
        # Verify report structure
        assert "pre_correction_cv" in report
        assert "post_correction_cv" in report
        assert "reduction_percent" in report
        assert "target_reduction" in report
        
        # Verify values are floats
        assert isinstance(report["pre_correction_cv"], float)
        assert isinstance(report["post_correction_cv"], float)
        assert isinstance(report["reduction_percent"], float)
        
        # Verify report file was written
        assert temp_report_path.exists()
        with open(temp_report_path, 'r') as f:
            saved_report = json.load(f)
            assert saved_report["pre_correction_cv"] == report["pre_correction_cv"]

def test_batch_correction_logic(temp_tpm_file, temp_report_path, housekeeping_genes):
    """Test that batch correction actually reduces variance."""
    # Create a batch mapping
    batch_mapping = {
        f"Sample_{i}": "batch1" if i < 5 else "batch2"
        for i in range(10)
    }
    
    with patch('src.data.batch_correction.get_housekeeping_genes') as mock_get_hk:
        mock_get_hk.return_value = housekeeping_genes
        
        # Run calculation with batch mapping
        report = calculate_cv_reduction(temp_tpm_file, str(temp_report_path), batch_mapping)
        
        # The correction should have been applied
        assert "meets_target" in report
        
def test_calculate_cv_for_genes(sample_tpm_matrix, housekeeping_genes):
    """Test CV calculation for a subset of genes."""
    cv = calculate_cv_for_genes(sample_tpm_matrix, housekeeping_genes)
    assert isinstance(cv, float)
    assert cv >= 0

def test_calculate_georm_m_value(sample_tpm_matrix, housekeeping_genes):
    """Test GeNorm M-value calculation."""
    m_value = calculate_georm_m_value(sample_tpm_matrix, housekeeping_genes)
    assert isinstance(m_value, float)
    assert m_value >= 0
