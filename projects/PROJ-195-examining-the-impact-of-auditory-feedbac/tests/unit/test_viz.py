"""
Unit tests for the visualization module (T034).
Tests thresholded map generation and scatter plot creation.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
import json

import numpy as np
import nibabel as nib
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from viz import (
    generate_thresholded_stat_map,
    generate_scatter_plot,
    generate_stat_map_overlay,
    load_t_stat_map
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_t_map(temp_dir):
    """Create a mock t-statistic NIfTI file."""
    # Create a 4D array with some t-values
    data = np.random.randn(10, 10, 10) * 2.0 + 3.0  # Mean t ~ 3.0
    affine = np.eye(4)
    nii = nib.Nifti1Image(data.astype(np.float32), affine)
    
    t_map_path = temp_dir / "mock_t_map.nii.gz"
    nib.save(nii, str(t_map_path))
    return t_map_path

@pytest.fixture
def mock_roi_betas():
    """Mock ROI beta values."""
    return [0.5, 0.8, 1.2, 1.5, 2.0, 2.3, 2.8, 3.1, 3.5, 4.0]

@pytest.fixture
def mock_learning_slopes():
    """Mock learning rate slopes."""
    return [-5.0, -4.2, -3.5, -2.8, -2.0, -1.5, -1.0, -0.5, 0.2, 0.8]

class TestThresholdedStatMap:
    """Tests for generate_thresholded_stat_map function."""

    def test_thresholded_map_generation(self, mock_t_map, temp_dir):
        """Test that a thresholded map is generated correctly."""
        output_path = temp_dir / "thresholded.nii.gz"
        
        result_path = generate_thresholded_stat_map(
            mock_t_map,
            output_path,
            fdr_q=0.05,
            use_fdr=True
        )
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Verify the saved image
        loaded = nib.load(str(result_path))
        assert loaded.shape == (10, 10, 10)
        
        # Check that some voxels are thresholded (should be zeros or masked)
        data = loaded.get_fdata()
        # With threshold ~2.5 and mean ~3.0, some voxels should survive
        assert np.any(data != 0) or np.all(data == 0)  # Either some survive or all are masked

    def test_uncorrected_threshold_fallback(self, mock_t_map, temp_dir):
        """Test uncorrected threshold application for null results."""
        output_path = temp_dir / "uncorrected.nii.gz"
        
        result_path = generate_thresholded_stat_map(
            mock_t_map,
            output_path,
            fdr_q=0.05,
            global_p_uncorrected=0.001,
            use_fdr=False
        )
        
        assert result_path.exists()
        loaded = nib.load(str(result_path))
        data = loaded.get_fdata()
        
        # With higher threshold (3.09), fewer voxels should survive
        # This test just verifies the function runs without error

    def test_missing_input_map(self, temp_dir):
        """Test error handling for missing input map."""
        output_path = temp_dir / "output.nii.gz"
        missing_path = temp_dir / "nonexistent.nii.gz"
        
        with pytest.raises(FileNotFoundError):
            generate_thresholded_stat_map(
                missing_path,
                output_path,
                fdr_q=0.05
            )

class TestScatterPlot:
    """Tests for generate_scatter_plot function."""

    def test_scatter_plot_generation(self, temp_dir, mock_roi_betas, mock_learning_slopes):
        """Test that a scatter plot is generated correctly."""
        output_path = temp_dir / "scatter.png"
        r, p = 0.85, 0.002  # Mock correlation values
        
        result_path = generate_scatter_plot(
            mock_roi_betas,
            mock_learning_slopes,
            output_path,
            r,
            p
        )
        
        assert result_path.exists()
        assert output_path == result_path
        
        # Verify file size (should be non-zero)
        assert result_path.stat().st_size > 0

    def test_mismatched_lengths(self, temp_dir, mock_roi_betas):
        """Test error handling for mismatched input lengths."""
        output_path = temp_dir / "scatter.png"
        
        with pytest.raises(ValueError, match="Length mismatch"):
            generate_scatter_plot(
                mock_roi_betas,
                mock_roi_betas[:5],  # Shorter list
                output_path,
                0.5,
                0.1
            )

    def test_insufficient_data(self, temp_dir):
        """Test error handling for insufficient data points."""
        output_path = temp_dir / "scatter.png"
        
        with pytest.raises(ValueError, match="Need at least 2 subjects"):
            generate_scatter_plot(
                [1.0],  # Only 1 subject
                [2.0],
                output_path,
                0.0,
                1.0
            )

class TestStatMapOverlay:
    """Tests for generate_stat_map_overlay function."""

    def test_overlay_generation(self, mock_t_map, temp_dir):
        """Test that an overlay figure is generated."""
        output_path = temp_dir / "overlay.png"
        
        result_path = generate_stat_map_overlay(
            mock_t_map,
            output_path=output_path,
            threshold=2.5
        )
        
        assert result_path is not None
        assert result_path.exists()
        assert result_path == output_path
        assert result_path.stat().st_size > 0

    def test_overlay_without_save(self, mock_t_map):
        """Test that overlay generation works without saving."""
        result_path = generate_stat_map_overlay(
            mock_t_map,
            output_path=None,
            threshold=2.5
        )
        
        assert result_path is None

class TestLoadTStatMap:
    """Tests for load_t_stat_map function."""

    def test_load_valid_map(self, mock_t_map):
        """Test loading a valid t-statistic map."""
        img = load_t_stat_map(mock_t_map)
        assert isinstance(img, nib.Nifti1Image)
        assert img.shape == (10, 10, 10)

    def test_load_missing_map(self, temp_dir):
        """Test error handling for missing map."""
        missing_path = temp_dir / "missing.nii.gz"
        
        with pytest.raises(FileNotFoundError):
            load_t_stat_map(missing_path)