"""
Unit tests for T027: Null Result Handler.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from glm_null_result_handler import (
    calculate_global_p_value,
    save_uncorrected_map,
    handle_null_result,
    main
)

@pytest.fixture
def temp_t_map():
    """Create a temporary t-map file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        data = np.random.randn(10, 10, 10) * 2 + 3  # Some signal
        data[5, 5, 5] = 5.0  # A strong peak
        img = nib.Nifti1Image(data, np.eye(4))
        filepath = tmppath / "test_t_map.nii.gz"
        nib.save(img, filepath)
        yield filepath, tmppath

@pytest.fixture
def empty_clusters():
    return []

def test_calculate_global_p_value(temp_t_map):
    """Test that global p-value calculation runs without error."""
    t_path, _ = temp_t_map
    p_val = calculate_global_p_value(t_path)
    assert isinstance(p_val, float)
    assert 0.0 <= p_val <= 1.0

def test_save_uncorrected_map(temp_t_map):
    """Test that uncorrected map is saved correctly."""
    t_path, output_dir = temp_t_map
    output_file = output_dir / "uncorrected.nii.gz"
    
    save_uncorrected_map(t_path, output_file, threshold=3.0)
    
    assert output_file.exists()
    img = nib.load(str(output_file))
    assert img.get_fdata().shape == (10, 10, 10)
    # Check that some values are zero (thresholded)
    assert np.any(img.get_fdata() == 0)

def test_handle_null_result(temp_t_map, empty_clusters):
    """Test the full null result handling flow."""
    t_path, output_dir = temp_t_map
    
    handle_null_result(t_path, output_dir, empty_clusters)
    
    # Check for output files
    assert (output_dir / "uncorrected_map.nii.gz").exists()
    assert (output_dir / "null_result_log.json").exists()
    
    # Verify log content
    with open(output_dir / "null_result_log.json", 'r') as f:
        log_data = json.load(f)
    
    assert log_data["status"] == "NULL_RESULT"
    assert "No clusters survived FDR" in log_data["message"]
    assert "global_p_value_proxy" in log_data
    assert log_data["clusters_survived_fdr"] == 0

def test_handle_result_with_clusters(temp_t_map):
    """Test that handler exits early if clusters exist."""
    t_path, output_dir = temp_t_map
    fake_clusters = [{"id": 1, "size": 10}]
    
    # This should log info and return without creating files
    handle_null_result(t_path, output_dir, fake_clusters)
    
    # Files should NOT be created if clusters exist
    assert not (output_dir / "uncorrected_map.nii.gz").exists()
    assert not (output_dir / "null_result_log.json").exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])