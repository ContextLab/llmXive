import pytest
import os
import json
import numpy as np
import tempfile
from pathlib import Path
from data.flow import compute_flow_magnitude, extract_flow_magnitudes_for_dataset

class TestFlowMagnitudeExtraction:
    """Tests for T009a: Lightweight flow magnitude extraction."""

    def test_compute_flow_magnitude_basic(self):
        """Test basic magnitude computation on a simple flow field."""
        # Create a flow field with known magnitudes
        # 2x2 flow: (1, 0), (0, 1), (1, 1), (0, 0)
        flow = np.array([
            [[1.0, 0.0], [0.0, 1.0]],
            [[1.0, 1.0], [0.0, 0.0]]
        ], dtype=np.float32)
        
        # Magnitudes: 1.0, 1.0, sqrt(2)≈1.414, 0.0
        # Mean: (1 + 1 + 1.414 + 0) / 4 ≈ 0.8535
        mean_mag = compute_flow_magnitude(flow)
        
        expected = (1.0 + 1.0 + np.sqrt(2.0) + 0.0) / 4.0
        assert np.isclose(mean_mag, expected, rtol=1e-4)

    def test_compute_flow_magnitude_all_zeros(self):
        """Test that zero flow returns zero magnitude."""
        flow = np.zeros((10, 10, 2), dtype=np.float32)
        assert compute_flow_magnitude(flow) == 0.0

    def test_compute_flow_magnitude_with_nan(self):
        """Test that NaN values are ignored in magnitude computation."""
        flow = np.ones((10, 10, 2), dtype=np.float32)
        flow[0, 0, :] = np.nan
        flow[5, 5, :] = np.inf
        
        # All other values are magnitude 1.0
        mean_mag = compute_flow_magnitude(flow)
        assert np.isclose(mean_mag, 1.0, rtol=1e-4)

    def test_compute_flow_magnitude_all_invalid(self):
        """Test that all-invalid flow returns 0.0."""
        flow = np.full((10, 10, 2), np.nan, dtype=np.float32)
        assert compute_flow_magnitude(flow) == 0.0

    def test_extract_flow_magnitudes_for_dataset_writes_file(self):
        """Test that the extraction function writes the output JSON file."""
        # Create a temporary directory and mock video file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy video file (using a simple BMP as proxy for testing)
            # Since we can't easily create a real video in a test, we test the file writing logic
            # by providing a non-existent path and checking that the output file is still created
            # with the expected structure (empty or with error entries)
            
            output_path = os.path.join(tmpdir, "magnitudes.json")
            clip_paths = [os.path.join(tmpdir, "nonexistent.mp4")]
            
            # This should handle the missing file gracefully and create the output file
            results = extract_flow_magnitudes_for_dataset(
                clip_paths=clip_paths,
                output_path=output_path,
                flow_method="farneback"
            )
            
            # Check that the output file was created
            assert os.path.exists(output_path)
            
            # Check that the file contains valid JSON
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # The result should be a dictionary
            assert isinstance(data, dict)
            # The nonexistent clip should be in the results (with 0.0 or skipped)
            # Based on implementation, it logs warning and skips, so dict might be empty
            # or contain the clip with 0.0. We verify the file exists and is valid JSON.

    def test_flow_magnitude_extraction_creates_output_directory(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create output path in a non-existent subdirectory
            output_path = os.path.join(tmpdir, "subdir", "nested", "magnitudes.json")
            clip_paths = []
            
            # Call the function
            extract_flow_magnitudes_for_dataset(
                clip_paths=clip_paths,
                output_path=output_path,
                flow_method="farneback"
            )
            
            # Verify the file was created (even if empty)
            assert os.path.exists(output_path)
            
            # Verify the directory structure was created
            assert os.path.exists(os.path.dirname(output_path))

    def test_extract_flow_magnitudes_returns_dict(self):
        """Test that the function returns a dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "magnitudes.json")
            clip_paths = []
            
            results = extract_flow_magnitudes_for_dataset(
                clip_paths=clip_paths,
                output_path=output_path,
                flow_method="farneback"
            )
            
            assert isinstance(results, dict)