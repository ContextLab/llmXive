"""
Integration test for the download and aggregation pipeline (Task T012).

This test verifies the end-to-end flow of:
1. Downloading the NLCD 30m subset for Colorado (or using existing cached data).
2. Generating coarser resolution rasters (60m, 120m, 240m, 480m) via nearest-neighbor resampling.
3. Validating that generated files exist, have correct metadata (resolution), and preserve integer values.

It relies on the implementation in code/data_ingestion.py and code/resampling.py.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Add project root to path to import code modules
# Assuming this test is run from the project root or the path is set up correctly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import RESOLUTIONS, DATA_DIR, RAW_DATA_PATH, DERIVED_DATA_DIR
from data_ingestion import download_and_validate_nlcd
from resampling import generate_resolution
from utils import checksum_file, get_raster_info


class TestDownloadAndAggregationPipeline:
    """
    Integration test suite for the data ingestion and resolution aggregation pipeline.
    """

    @classmethod
    def setup_class(cls):
        """
        Setup fixtures before running any tests in this class.
        Ensures directories exist and attempts to download raw data if missing.
        """
        # Create necessary directories
        os.makedirs(DATA_DIR / "raw", exist_ok=True)
        os.makedirs(DATA_DIR / "derived", exist_ok=True)

        # Check if raw data exists; if not, attempt download
        if not RAW_DATA_PATH.exists():
            print(f"Raw data not found at {RAW_DATA_PATH}. Attempting download...")
            # Note: In a real CI environment, this might fail if network is restricted.
            # For this integration test, we assume the download logic in data_ingestion.py
            # is robust or the data is pre-seeded.
            try:
                download_and_validate_nlcd()
            except Exception as e:
                # If download fails, we skip the integration test or mark it as skipped
                # depending on strictness. Here, we raise to fail the test if data is missing.
                raise RuntimeError(
                    f"Integration test cannot proceed: Failed to download raw data. "
                    f"Error: {e}. "
                    f"Please ensure the data source is reachable or the file exists at {RAW_DATA_PATH}."
                )

    def test_pipeline_execution(self):
        """
        Test the full pipeline: Download (if needed) -> Aggregate -> Validate.
        """
        # 1. Ensure raw data exists (handled in setup_class, but good to double-check)
        assert RAW_DATA_PATH.exists(), f"Raw data file {RAW_DATA_PATH} missing after setup."

        # 2. Generate coarser resolutions
        expected_factors = [2, 4, 8, 16]
        expected_resolutions = [60, 120, 240, 480]
        generated_files = []

        for factor, res in zip(expected_factors, expected_resolutions):
            output_path = generate_resolution(RAW_DATA_PATH, factor)
            assert output_path is not None, f"Failed to generate resolution for factor {factor}"
            assert output_path.exists(), f"Generated file {output_path} does not exist."
            generated_files.append(output_path)

            # 3. Validate metadata (resolution)
            info = get_raster_info(output_path)
            # The pixel size should be approximately res meters (allowing for float precision)
            # We check the 'pixel_size' or 'transform' from rasterio info
            # Assuming get_raster_info returns a dict with 'pixel_size' or similar
            # If the function returns a ResolutionRaster object, access .resolution
            # Let's assume get_raster_info returns a dict for now based on common utils patterns
            # or we re-read with rasterio to be safe if utils is thin.
            
            with rasterio.open(output_path) as src:
                # Get the transform to estimate pixel size
                transform = src.transform
                # Pixel width and height
                pixel_width = abs(transform.a)
                pixel_height = abs(transform.e)
                
                # Check if the pixel size is close to the expected resolution (30 * factor)
                expected_pixel_size = 30 * factor
                assert abs(pixel_width - expected_pixel_size) < 1.0, \
                    f"Resolution mismatch for factor {factor}: expected ~{expected_pixel_size}, got {pixel_width}"
                assert abs(pixel_height - expected_pixel_size) < 1.0, \
                    f"Resolution mismatch for factor {factor}: expected ~{expected_pixel_size}, got {pixel_height}"

            # 4. Validate that values are integers (nearest neighbor property)
            with rasterio.open(output_path) as src:
                data = src.read(1)
                # Check if data is integer type or if float values are whole numbers
                # NLCD is categorical integer data
                if np.issubdtype(data.dtype, np.floating):
                    # If float, ensure all are whole numbers
                    assert np.all(data == data.astype(int)), \
                        f"Data for factor {factor} contains non-integer values: {np.unique(data)}"
                else:
                    # If integer, good
                    pass

            # 5. Validate checksum (optional but good for integrity)
            # We can't compare to a known checksum without a reference, but we can ensure
            # the checksum function runs without error and produces a consistent result.
            checksum = checksum_file(output_path)
            assert len(checksum) > 0, "Checksum generation failed."

    def test_artifacts_in_results(self):
        """
        Verify that the pipeline produces the expected artifacts in the data directory.
        """
        # Re-run generation to ensure files are present for this check
        # (In a real test suite, we might share the state from the previous test)
        for factor in [2, 4, 8, 16]:
            output_path = generate_resolution(RAW_DATA_PATH, factor)
            assert output_path.exists(), f"Expected artifact {output_path} missing."
            
            # Check that the file is not empty
            assert output_path.stat().st_size > 0, f"Artifact {output_path} is empty."

    def test_nearest_neighbor_preservation(self):
        """
        Specific test for the nearest-neighbor property: unique values in output
        should be a subset of unique values in input (no new values created).
        """
        # Load raw data
        with rasterio.open(RAW_DATA_PATH) as src:
            raw_data = src.read(1)
            raw_unique = set(np.unique(raw_data))

        for factor in [2, 4, 8, 16]:
            output_path = generate_resolution(RAW_DATA_PATH, factor)
            with rasterio.open(output_path) as src:
                agg_data = src.read(1)
                agg_unique = set(np.unique(agg_data))
            
            # All values in aggregated data must exist in raw data
            assert agg_unique.issubset(raw_unique), \
                f"Factor {factor} introduced new values: {agg_unique - raw_unique}"

    def test_consistency_across_runs(self):
        """
        Verify that running the aggregation twice produces the same checksum.
        """
        factor = 4
        output_path_1 = generate_resolution(RAW_DATA_PATH, factor)
        checksum_1 = checksum_file(output_path_1)
        
        # Run again
        output_path_2 = generate_resolution(RAW_DATA_PATH, factor)
        checksum_2 = checksum_file(output_path_2)
        
        assert checksum_1 == checksum_2, \
            "Aggregation is not deterministic. Checksums do not match."


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])