"""
Integration test: Verify end-to-end download and CSV generation for LAGEOS-1.

This test validates the full data ingestion pipeline for a single satellite (LAGEOS-1).
It ensures that:
1. The correct URL is retrieved from config.
2. Data is successfully downloaded and parsed.
3. The output CSV is written to the expected location.
4. The CSV contains a valid number of rows (>= 500 to satisfy data sufficiency).
5. No NaN values exist in the critical columns.
"""
import os
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path

# Import from project modules
from config import get_config
from data.ingestion import fetch_single_satellite, get_satellite_urls
from utils.logging import get_logger

logger = get_logger(__name__)

# Configuration for the test
TARGET_SATELLITE = "LAGEOS-1"
EXPECTED_MIN_ROWS = 500  # Threshold for "sufficient data" as per task description
OUTPUT_FILENAME = "lageos_1_test.csv"

class TestDataPipeline:
    """Integration tests for the LAGEOS-1 data download pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup temporary directory for test outputs and cleanup after."""
        # Create a temporary directory for this test run
        self.test_dir = tempfile.mkdtemp(prefix="lageos_test_")
        self.output_path = os.path.join(self.test_dir, OUTPUT_FILENAME)
        
        yield
        
        # Cleanup: remove temporary directory and files
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_url_retrieval(self):
        """Verify that the URL for LAGEOS-1 exists in configuration."""
        urls = get_satellite_urls()
        assert TARGET_SATELLITE in urls, f"URL for {TARGET_SATELLITE} not found in config"
        assert urls[TARGET_SATELLITE] is not None
        assert urls[TARGET_SATELLITE] != ""
        logger.info(f"Retrieved URL for {TARGET_SATELLITE}: {urls[TARGET_SATELLITE]}")

    def test_end_to_end_download_and_csv_generation(self):
        """
        Execute the full pipeline: fetch data for LAGEOS-1 and write to CSV.
        
        Assertions:
        - File exists on disk.
        - DataFrame has >= EXPECTED_MIN_ROWS rows.
        - No NaN values in 'time' or 'range_residual' columns.
        """
        config = get_config()
        urls = get_satellite_urls()
        
        if not urls.get(TARGET_SATELLITE):
            pytest.skip(f"Data for {TARGET_SATELLITE} not configured or unavailable.")

        logger.info(f"Starting end-to-end test for {TARGET_SATELLITE}...")
        
        # 1. Fetch Data
        # Using a small timeout for CI safety, but the function has backoff logic
        try:
            df = fetch_single_satellite(TARGET_SATELLITE, urls[TARGET_SATELLITE])
        except Exception as e:
            # If the real data source is unreachable, we fail loudly rather than fake data
            logger.error(f"Failed to fetch data for {TARGET_SATELLITE}: {str(e)}")
            pytest.fail(f"Data ingestion failed for {TARGET_SATELLITE}: {str(e)}")

        # 2. Validate In-Memory Data
        assert isinstance(df, pd.DataFrame), "Fetched data must be a DataFrame"
        assert len(df) > 0, "Fetched DataFrame must not be empty"
        
        # Check for expected columns (common to SLR normal points)
        expected_cols = ['time', 'range_residual']
        for col in expected_cols:
            assert col in df.columns, f"Expected column '{col}' missing in DataFrame"
            assert df[col].notna().all(), f"Column '{col}' contains NaN values"

        # 3. Write to Disk (Simulating the pipeline output step)
        df.to_csv(self.output_path, index=False)
        logger.info(f"Data written to {self.output_path}")

        # 4. Verify File Existence and Integrity
        assert os.path.exists(self.output_path), f"Output file {self.output_path} was not created"
        
        # Read back to ensure it's a valid CSV
        df_read = pd.read_csv(self.output_path)
        
        # Verify row count meets minimum threshold
        assert len(df_read) >= EXPECTED_MIN_ROWS, (
            f"Data sufficiency check failed: {len(df_read)} rows found, "
            f"expected >= {EXPECTED_MIN_ROWS}"
        )

        # Verify no NaNs in critical columns after write/read cycle
        for col in expected_cols:
            assert df_read[col].notna().all(), (
                f"NaN values detected in '{col}' after CSV write/read cycle"
            )

        logger.info(f"Test passed for {TARGET_SATELLITE}: {len(df_read)} rows validated.")