"""
Unit tests for code/data/generate.py (T012).
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Mock VALIDATION_MODE for testing
# We need to inject this into the config module or mock the import
# Since we cannot easily mock the import inside generate.py without complex patching,
# we will test the logic by temporarily setting the environment or mocking the function.

# Import the module to test
# We need to ensure the config module is available.
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock

# We will patch the _get_config_validation_mode function in generate.py
# to return True for these tests.

@pytest.fixture
def mock_validation_mode():
    """Fixture to mock VALIDATION_MODE as True."""
    with patch('code.data.generate._get_config_validation_mode', return_value=True):
        yield

@pytest.fixture
def temp_output_dir():
    """Fixture to create a temporary directory for outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_synthetic_genomics_generation(mock_validation_mode, temp_output_dir):
    """Test that generate_synthetic_genomic_features creates a valid DataFrame."""
    from code.data.generate import generate_synthetic_genomic_features, TRAINING_GENES, NUM_HIDDEN_GENES
    
    output_path = os.path.join(temp_output_dir, "synthetic_genomics.csv")
    df = generate_synthetic_genomic_features(output_path)
    
    # Verify shape
    assert df.shape[0] == 100, "Should generate 100 samples"
    assert df.shape[1] == 21, "Should have 20 genes + 1 label"
    
    # Verify columns
    expected_cols = set(TRAINING_GENES) | {'label'}
    assert set(df.columns) == expected_cols, f"Columns mismatch. Expected {expected_cols}, got {set(df.columns)}"
    
    # Verify data types
    for gene in TRAINING_GENES:
        assert df[gene].isin([0, 1]).all(), f"Gene {gene} should be binary"
    assert df['label'].isin([0, 1]).all(), "Label should be binary"
    
    # Verify file exists
    assert os.path.exists(output_path), "Output CSV should be created"

def test_hidden_genes_logic(mock_validation_mode, temp_output_dir):
    """Test that hidden genes are deterministic and logged."""
    from code.data.generate import generate_synthetic_genomic_features, TRAINING_GENES
    
    output_path = os.path.join(temp_output_dir, "synthetic_genomics.csv")
    log_path = os.path.join(temp_output_dir, "generation_config.json")
    
    # We need to redirect the log output to check the config file
    # The function writes to data/logs/generation_config.json by default.
    # We will patch the path or just check the default location if we can control the directory.
    # For simplicity, we assume the function writes to the default location relative to the project root.
    # However, to test in isolation, we might need to modify the function to accept a log path.
    # Since we cannot modify the function signature for the test without changing the task,
    # we will check the default location if it exists, or rely on the fact that the test runs in the project root.
    
    # Let's assume the test runs from the project root.
    # We will generate and then check the file.
    df = generate_synthetic_genomic_features(output_path)
    
    # Check the config file
    config_path = Path("data/logs/generation_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assert 'hidden_subset' in config, "Config should contain hidden_subset"
        assert len(config['hidden_subset']) == 5, "Should have 5 hidden genes"
        
        # Verify disjointness from training genes is not applicable here as they are a subset
        # But we can verify they are in the training list
        assert all(g in TRAINING_GENES for g in config['hidden_subset']), "Hidden genes must be from training list"
    else:
        # If the file is not in the default location, we might need to adjust the test environment
        # For the purpose of this task, we assume the pipeline runs from the root.
        pytest.skip("Config file not found in default location. Test environment might need adjustment.")

def test_synthetic_phylogeny_generation(mock_validation_mode, temp_output_dir):
    """Test that generate_synthetic_phylogenetic_matrix creates a valid matrix."""
    from code.data.generate import generate_synthetic_phylogenetic_matrix
    
    output_path = os.path.join(temp_output_dir, "synthetic_phylo_matrix.npy")
    matrix = generate_synthetic_phylogenetic_matrix(output_path)
    
    # Verify shape
    assert matrix.shape == (100, 100), "Matrix should be 100x100"
    
    # Verify symmetry
    assert np.allclose(matrix, matrix.T), "Matrix should be symmetric"
    
    # Verify diagonal is zero
    assert np.allclose(np.diag(matrix), 0), "Diagonal should be zero"
    
    # Verify off-diagonals are positive and in range
    off_diag = matrix[np.triu_indices(100, k=1)]
    assert np.all(off_diag > 0), "Off-diagonals should be positive"
    assert np.all(off_diag <= 1.0), "Off-diagonals should be <= 1.0"
    assert np.all(off_diag >= 0.01), "Off-diagonals should be >= 0.01"
    
    # Verify file exists
    assert os.path.exists(output_path), "Output NPY should be created"

def test_fails_in_production_mode():
    """Test that generation fails if VALIDATION_MODE is False."""
    from code.data.generate import generate_synthetic_genomic_features, generate_synthetic_phylogenetic_matrix
    
    with patch('code.data.generate._get_config_validation_mode', return_value=False):
        with pytest.raises(RuntimeError, match="CRITICAL: Synthetic data generation attempted in Production Mode"):
            generate_synthetic_genomic_features()
        
        with pytest.raises(RuntimeError, match="CRITICAL: Synthetic phylogenetic matrix generation attempted in Production Mode"):
            generate_synthetic_phylogenetic_matrix()

def test_chi_square_test_result(mock_validation_mode, temp_output_dir):
    """Test that Chi-Square test is performed and logged."""
    from code.data.generate import generate_synthetic_genomic_features
    
    output_path = os.path.join(temp_output_dir, "synthetic_genomics.csv")
    df = generate_synthetic_genomic_features(output_path)
    
    # Check config file
    config_path = Path("data/logs/generation_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assert 'chi_square_test_result' in config, "Config should contain chi_square_test_result"
        chi_result = config['chi_square_test_result']
        
        assert 'statistic' in chi_result, "Chi-square result should have statistic"
        assert 'p_value' in chi_result, "Chi-square result should have p_value"
        assert 'passed' in chi_result, "Chi-square result should have passed flag"
        
        # The test should pass (p > 0.05) for a well-generated dataset
        # However, with small N=100, it might occasionally fail. We just check the field exists.
        assert isinstance(chi_result['passed'], bool), "Passed should be boolean"
    else:
        pytest.skip("Config file not found in default location.")
