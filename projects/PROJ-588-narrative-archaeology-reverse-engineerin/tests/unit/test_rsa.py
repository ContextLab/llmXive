"""
Unit tests for RSA module (T021).
"""
import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.rsa import compute_dissimilarity_matrix, compare_early_late, run_rsa_analysis

def test_compute_dissimilarity_matrix_basic():
    """Test basic dissimilarity matrix computation."""
    # Create simple 2D array: 3 events, 4 voxels
    np.random.seed(42)
    timecourses = np.random.rand(3, 4)
    
    rdm = compute_dissimilarity_matrix(timecourses)
    
    # Check shape
    assert rdm.shape == (3, 3)
    
    # Check diagonal is zero (or very close)
    assert np.allclose(np.diag(rdm), 0.0)
    
    # Check symmetry
    assert np.allclose(rdm, rdm.T)
    
    # Check values are in [0, 2] (correlation distance range)
    assert np.all((rdm >= 0) & (rdm <= 2))

def test_compute_dissimilarity_matrix_identical():
    """Test with identical timecourses (should be 0 dissimilarity)."""
    timecourses = np.ones((3, 4))
    rdm = compute_dissimilarity_matrix(timecourses)
    assert np.allclose(rdm, 0.0)

def test_compare_early_late():
    """Test Early vs. Late comparison."""
    early_matrix = np.array([[0, 0.5, 0.6], [0.5, 0, 0.7], [0.6, 0.7, 0]])
    late_matrix = np.array([[0, 0.2, 0.3], [0.2, 0, 0.4], [0.3, 0.4, 0]])
    
    diff = compare_early_late(early_matrix, late_matrix)
    
    # Mean of early (excluding diagonal): (0.5+0.6+0.5+0.7+0.6+0.7)/6 = 3.6/6 = 0.6
    # Mean of late (excluding diagonal): (0.2+0.3+0.2+0.4+0.3+0.4)/6 = 1.8/6 = 0.3
    # Difference: 0.6 - 0.3 = 0.3
    assert np.isclose(diff, 0.3)

def test_run_rsa_analysis_integration():
    """
    Integration test for run_rsa_analysis.
    This test creates a mock roi_timecourses.h5 file and verifies the output.
    """
    import h5py
    import tempfile
    
    # Create temporary directory and file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_file = tmpdir / "roi_timecourses.h5"
        output_file = tmpdir / "rsa_matrices.json"
        
        # Create mock data
        with h5py.File(input_file, 'w') as f:
            # Create mock ROI group
            roi_group = f.create_group("hippocampus")
            
            # Create mock early and late data (5 events, 10 voxels)
            np.random.seed(123)
            early_data = np.random.rand(5, 10)
            late_data = np.random.rand(5, 10)
            
            roi_group.create_dataset("early", data=early_data)
            roi_group.create_dataset("late", data=late_data)
        
        # Temporarily override config paths
        import code.config as config
        original_get_data_path = config.get_data_path
        original_get_output_path = config.get_output_path
        
        def mock_get_data_path(suffix):
            if "roi_timecourses.h5" in suffix:
                return str(input_file)
            return str(tmpdir / suffix)
        
        def mock_get_output_path(suffix):
            return str(tmpdir / suffix)
        
        config.get_data_path = mock_get_data_path
        config.get_output_path = mock_get_output_path
        
        try:
            # Run the analysis
            result = run_rsa_analysis()
            
            # Verify output file exists
            assert output_file.exists()
            
            # Verify JSON structure
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert "hippocampus" in data
            assert "early_early" in data["hippocampus"]
            assert "late_late" in data["hippocampus"]
            assert "early_late" in data["hippocampus"]
            
            # Verify values are floats
            assert isinstance(data["hippocampus"]["early_early"], float)
            assert isinstance(data["hippocampus"]["late_late"], float)
            assert isinstance(data["hippocampus"]["early_late"], float)
            
        finally:
            # Restore original functions
            config.get_data_path = original_get_data_path
            config.get_output_path = original_get_output_path
