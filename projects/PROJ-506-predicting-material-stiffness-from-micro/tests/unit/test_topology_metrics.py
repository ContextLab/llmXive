"""
Unit tests for code/utils/topology_metrics.py
"""
import numpy as np
import pytest
from pathlib import Path
from skimage import io, morphology
import tempfile
import os

# Import the functions to test
from code.utils.topology_metrics import (
    calculate_shape_factor,
    calculate_connectivity,
    compute_topological_metrics,
    calculate_topological_metrics_from_array
)


class TestCalculateShapeFactor:
    def test_perfect_circle(self):
        """Test shape factor for a perfect circle (should be ~1.0)"""
        # Create a 100x100 grid
        y, x = np.ogrid[-50:50, -50:50]
        r = 25
        mask = (x**2 + y**2) <= r**2

        sf = calculate_shape_factor(mask)
        # For a discrete circle, it won't be exactly 1.0 due to pixelation,
        # but it should be close (typically 1.0 - 1.2 range)
        assert 0.9 <= sf <= 1.5, f"Shape factor for circle should be near 1.0, got {sf}"

    def test_square(self):
        """Test shape factor for a square (should be > 1.0)"""
        mask = np.zeros((50, 50), dtype=bool)
        mask[10:40, 10:40] = True

        sf = calculate_shape_factor(mask)
        # A square has a higher perimeter-to-area ratio than a circle
        assert sf > 1.0, f"Shape factor for square should be > 1.0, got {sf}"

    def test_empty_mask(self):
        """Test shape factor for an empty mask"""
        mask = np.zeros((50, 50), dtype=bool)
        sf = calculate_shape_factor(mask)
        assert np.isnan(sf), "Shape factor for empty mask should be NaN"

    def test_full_mask(self):
        """Test shape factor for a full mask (square image)"""
        mask = np.ones((50, 50), dtype=bool)
        sf = calculate_shape_factor(mask)
        assert sf > 1.0, "Shape factor for full square should be > 1.0"


class TestCalculateConnectivity:
    def test_single_object_no_holes(self):
        """Test connectivity for a single object with no holes"""
        mask = np.zeros((50, 50), dtype=bool)
        mask[10:40, 10:40] = True

        conn = calculate_connectivity(mask)
        # 1 object, 0 holes -> Euler number = 1
        assert conn == 1, f"Connectivity for single object should be 1, got {conn}"

    def test_single_object_with_hole(self):
        """Test connectivity for a single object with a hole"""
        mask = np.zeros((50, 50), dtype=bool)
        mask[10:40, 10:40] = True
        # Add a hole in the middle
        mask[20:30, 20:30] = False

        conn = calculate_connectivity(mask)
        # 1 object, 1 hole -> Euler number = 0
        assert conn == 0, f"Connectivity for object with 1 hole should be 0, got {conn}"

    def test_multiple_objects(self):
        """Test connectivity for multiple disconnected objects"""
        mask = np.zeros((50, 50), dtype=bool)
        mask[10:20, 10:20] = True
        mask[30:40, 30:40] = True

        conn = calculate_connectivity(mask)
        # 2 objects, 0 holes -> Euler number = 2
        assert conn == 2, f"Connectivity for 2 objects should be 2, got {conn}"

    def test_empty_mask(self):
        """Test connectivity for an empty mask"""
        mask = np.zeros((50, 50), dtype=bool)
        conn = calculate_connectivity(mask)
        assert conn == 0, f"Connectivity for empty mask should be 0, got {conn}"


class TestComputeTopologicalMetrics:
    def test_compute_from_file(self):
        """Test computing metrics from a temporary image file"""
        # Create a temporary image
        mask = np.zeros((50, 50), dtype=np.uint8)
        mask[10:40, 10:40] = 255  # Square

        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "test_square.png")
            io.imsave(img_path, mask)

            metrics = compute_topological_metrics(img_path)

            assert "shape_factor" in metrics
            assert "connectivity" in metrics
            assert "area_fraction" in metrics
            assert metrics["shape_factor"] > 1.0
            assert metrics["connectivity"] == 1

    def test_invalid_file(self):
        """Test handling of invalid file path"""
        with pytest.raises(Exception):
            compute_topological_metrics("/non/existent/path.png")


class TestCalculateTopologicalMetricsFromArray:
    def test_basic_calculation(self):
        """Test basic calculation from array"""
        mask = np.zeros((50, 50), dtype=bool)
        mask[10:40, 10:40] = True

        result = calculate_topological_metrics_from_array(mask)

        assert "shape_factor" in result
        assert "connectivity" in result
        assert isinstance(result["shape_factor"], float)
        assert isinstance(result["connectivity"], float)