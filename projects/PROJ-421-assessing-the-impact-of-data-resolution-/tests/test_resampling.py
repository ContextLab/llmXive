"""
Unit tests for nearest-neighbor resampling logic.
Ensures that unique integer values are preserved during aggregation.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import Resampling

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from resampling import generate_resolution
from config import DATA_RAW_DIR, DATA_DERIVED_DIR


class TestNearestNeighborResampling(unittest.TestCase):
    """Tests for nearest-neighbor resampling preserving integer values."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_input_path = os.path.join(self.temp_dir, "test_input.tif")
        self.test_output_path = os.path.join(self.temp_dir, "test_output.tif")

        # Create a synthetic test raster with known unique integer values
        # Using a small 100x100 grid for speed
        self.height = 100
        self.width = 100
        self.original_res = 30  # meters

        # Create data with distinct integer values (e.g., land cover classes)
        # Values: 1, 2, 5, 10, 15, 20, 25, 30
        unique_values = np.array([1, 2, 5, 10, 15, 20, 25, 30], dtype=np.uint8)
        
        # Create a patterned array to ensure all values appear
        data = np.zeros((self.height, self.width), dtype=np.uint8)
        for i, val in enumerate(unique_values):
            y_start = (i * self.height) // len(unique_values)
            y_end = ((i + 1) * self.height) // len(unique_values)
            data[y_start:y_end, :] = val

        # Create a simple GeoTIFF
        transform = rasterio.transform.from_origin(0, 1000, self.original_res, self.original_res)
        
        with rasterio.open(
            self.test_input_path,
            'w',
            driver='GTiff',
            height=self.height,
            width=self.width,
            count=1,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            dst.write(data, 1)

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_input_path):
            os.remove(self.test_input_path)
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)
        os.rmdir(self.temp_dir)

    def test_nearest_neighbor_preserves_integers(self):
        """
        Asserts that unique values in output == unique values in input
        after nearest-neighbor resampling.
        
        Nearest-neighbor resampling should NOT interpolate values,
        so the set of unique values must remain identical.
        """
        # Generate resampled raster with factor 2 (nearest neighbor)
        generate_resolution(self.test_input_path, factor=2, output_path=self.test_output_path)

        # Read original unique values
        with rasterio.open(self.test_input_path) as src:
            original_data = src.read(1)
            original_unique = set(np.unique(original_data))

        # Read resampled unique values
        with rasterio.open(self.test_output_path) as src:
            resampled_data = src.read(1)
            resampled_unique = set(np.unique(resampled_data))

        # Assert that unique values are preserved exactly
        self.assertEqual(
            original_unique,
            resampled_unique,
            f"Unique values changed during resampling. "
            f"Original: {sorted(original_unique)}, Resampled: {sorted(resampled_unique)}"
        )

        # Additional check: ensure no new values were introduced (e.g., from interpolation)
        self.assertTrue(
            resampled_unique.issubset(original_unique),
            "Resampled data contains values not present in original data. "
            "This suggests interpolation occurred instead of nearest-neighbor."
        )

    def test_nearest_neighbor_no_float_artifacts(self):
        """
        Asserts that no floating point artifacts appear in output.
        Nearest-neighbor should produce exact integer values.
        """
        generate_resolution(self.test_input_path, factor=2, output_path=self.test_output_path)

        with rasterio.open(self.test_output_path) as src:
            resampled_data = src.read(1)

            # Check that all values are exactly representable as integers
            # (i.e., no 1.0000001 or similar artifacts)
            self.assertTrue(
                np.all(resampled_data == resampled_data.astype(int)),
                "Resampled data contains non-integer values."
            )

            # Check dtype is preserved or compatible
            self.assertIn(
                resampled_data.dtype,
                [np.uint8, np.uint16, np.int32, np.int64],
                f"Unexpected dtype: {resampled_data.dtype}"
            )


if __name__ == '__main__':
    unittest.main()