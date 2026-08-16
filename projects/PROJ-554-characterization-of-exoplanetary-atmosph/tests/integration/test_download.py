"""
Integration tests for the NASA Exoplanet Archive API download functionality.

This module tests the end-to-end flow of fetching spectrum data and metadata
from the NASA Exoplanet Archive API, ensuring that the returned data conforms
to the expected schema and contains valid values for critical fields.

Dependencies:
    - code/download.py: fetch_spectrum_data, parse_spectrum_metadata
    - code/api_config.py: QUERY_PARAMS
    - code/config.py: get_config
"""
import os
import sys
import pytest
from pathlib import Path
import logging
import pandas as pd
import numpy as np

# Add the project root to the path to allow imports from code/
# In a real execution environment, this would be handled by the runner
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from download import fetch_spectrum_data, parse_spectrum_metadata
from api_config import QUERY_PARAMS
from config import get_config
from utils import setup_logging

# Setup logging for the test
logger = setup_logging("tests/integration/test_download.log", level=logging.INFO)


class TestDownloadIntegration:
    """Integration tests for API download functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.required_columns = [
            "planet_name",
            "temperature",
            "metallicity",
            "snr",
            "resolution",
            "planet_category",
            "instrument",
            "wavelength_range"
        ]

    def test_download_returns_valid_metadata(self):
        """
        Test that the download function returns valid metadata for Hot Jupiters and Super-Earths.
        
        This test:
        1. Fetches data from the NASA Exoplanet Archive API using the defined QUERY_PARAMS.
        2. Parses the raw metadata.
        3. Validates that the resulting DataFrame contains all required columns.
        4. Checks that critical fields (temperature, metallicity, SNR, resolution, planet_category)
           are not null and contain reasonable values.
        5. Verifies that the planet_category logic correctly classifies planets based on radius and temperature.
        
        Note: This is an integration test that makes real API calls. It will fail if the API is unreachable
        or if the API structure changes.
        """
        logger.info("Starting integration test for API download")
        
        # Fetch spectrum data using the configured query parameters
        try:
            raw_data = fetch_spectrum_data(QUERY_PARAMS)
            logger.info(f"Fetched {len(raw_data)} raw records from API")
        except Exception as e:
            logger.error(f"Failed to fetch data from API: {str(e)}")
            # If the API is unreachable, the test should fail loudly rather than using synthetic data
            raise RuntimeError(f"API fetch failed: {str(e)}") from e
        
        # Parse the metadata
        try:
            parsed_df = parse_spectrum_metadata(raw_data)
            logger.info(f"Parsed metadata for {len(parsed_df)} planets")
        except Exception as e:
            logger.error(f"Failed to parse metadata: {str(e)}")
            raise RuntimeError(f"Metadata parsing failed: {str(e)}") from e
        
        # Verify the DataFrame is not empty
        assert len(parsed_df) > 0, "Parsed DataFrame is empty"
        
        # Check that all required columns exist
        missing_columns = set(self.required_columns) - set(parsed_df.columns)
        assert not missing_columns, f"Missing required columns: {missing_columns}"
        
        # Validate critical fields are not null
        critical_fields = ["temperature", "metallicity", "snr", "resolution", "planet_category"]
        for field in critical_fields:
            null_count = parsed_df[field].isnull().sum()
            assert null_count == 0, f"Field '{field}' has {null_count} null values"
        
        # Validate data types and ranges
        # Temperature should be positive (in Kelvin)
        assert all(parsed_df["temperature"] > 0), "Temperature values must be positive"
        assert all(parsed_df["temperature"] < 10000), "Temperature values seem unreasonably high (>10000K)"
        
        # SNR should be positive
        assert all(parsed_df["snr"] > 0), "SNR values must be positive"
        
        # Resolution should be positive
        assert all(parsed_df["resolution"] > 0), "Resolution values must be positive"
        
        # Planet category should be either "Hot Jupiter" or "Temperate Super-Earth"
        valid_categories = {"Hot Jupiter", "Temperate Super-Earth"}
        invalid_categories = set(parsed_df["planet_category"].unique()) - valid_categories
        assert not invalid_categories, f"Invalid planet categories found: {invalid_categories}"
        
        # Verify classification logic for a subset of planets
        # Hot Jupiters: Radius > 0.8 R_Jup AND T_eq > 1000K
        hot_jupiters = parsed_df[parsed_df["planet_category"] == "Hot Jupiter"]
        if len(hot_jupiters) > 0:
            # We can't directly check radius without it being in the parsed metadata,
            # but we can at least verify temperature > 1000K
            assert all(hot_jupiters["temperature"] > 1000), "Hot Jupiters should have T_eq > 1000K"
        
        # Temperate Super-Earths: Radius < 1.6 R_E AND T_eq < 1000K
        super_earths = parsed_df[parsed_df["planet_category"] == "Temperate Super-Earth"]
        if len(super_earths) > 0:
            # Verify temperature < 1000K
            assert all(super_earths["temperature"] < 1000), "Temperate Super-Earths should have T_eq < 1000K"
        
        # Check that instrument names are present
        assert all(parsed_df["instrument"].str.len() > 0), "Instrument names cannot be empty"
        
        # Check that wavelength ranges are present and valid
        assert all(parsed_df["wavelength_range"].str.len() > 0), "Wavelength ranges cannot be empty"
        
        logger.info("All integration test assertions passed")
        print(f"SUCCESS: Download returned valid metadata for {len(parsed_df)} planets")
        print(f"Categories: {parsed_df['planet_category'].value_counts().to_dict()}")
        print(f"Sample instruments: {parsed_df['instrument'].unique()[:5]}")

    def test_download_handles_api_errors_gracefully(self):
        """
        Test that the download function handles API errors gracefully.
        
        This test verifies that if the API returns an error or is unreachable,
        the function raises an appropriate exception rather than returning
        corrupted or empty data.
        """
        # This is a negative test - we can't easily simulate an API error
        # without mocking, so we just verify that the fetch function raises
        # an exception when given invalid parameters
        
        invalid_params = {
            "non_existent_field": "value",
            "another_invalid_field": "another_value"
        }
        
        with pytest.raises(Exception):
            fetch_spectrum_data(invalid_params)

    def test_download_preserves_raw_spectrum_files(self):
        """
        Test that raw spectrum files are saved to the correct location.
        
        This test verifies that the download process saves raw spectrum files
        to the data/raw/ directory as specified in the requirements.
        """
        # First, perform a download
        raw_data = fetch_spectrum_data(QUERY_PARAMS)
        parsed_df = parse_spectrum_metadata(raw_data)
        
        # Check that data/raw/ directory exists
        raw_dir = self.config["data_paths"]["raw"]
        assert Path(raw_dir).exists(), f"Raw data directory {raw_dir} does not exist"
        
        # Check that at least one file was saved
        # (The actual file saving logic is in fetch_spectrum_data)
        files = list(Path(raw_dir).glob("*"))
        assert len(files) > 0, "No raw spectrum files were saved"