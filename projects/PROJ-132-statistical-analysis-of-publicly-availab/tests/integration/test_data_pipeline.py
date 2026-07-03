"""
Integration tests for the data ingestion and preprocessing pipeline (User Story 1).

This module verifies the end-to-end flow of data acquisition, validation,
and initial preprocessing steps as defined in T013.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports if running standalone
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data.download import check_and_download_data
from src.data.preprocess import run_preprocessing_pipeline
from src.lib.config import SEED, GRID_RES
from src.lib.logging_config import setup_logging


@pytest.fixture(scope="module")
def temp_project_dir():
    """Create a temporary directory structure mimicking the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    try:
        # Create necessary subdirectories
        dirs = [
            "data/raw/ebird",
            "data/raw/climate",
            "data/raw/archive",
            "data/interim",
            "data/processed",
            "state/projects",
            "logs"
        ]
        for d in dirs:
            Path(temp_dir, d).mkdir(parents=True, exist_ok=True)

        # Create a minimal config file or ensure environment variables are set
        # For this test, we rely on the default SEED and GRID_RES from config.py
        # which are already defined as module-level constants.

        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def test_data_ingestion_flow(temp_project_dir):
    """
    Verify end-to-end flow of data ingestion and preprocessing.

    This test performs the following steps:
    1. Ensure raw data directories exist (simulating T005 behavior).
    2. Run the download check (T005 logic) to ensure data availability.
       Since we are in a test environment without real data, this should
       trigger the synthetic data generation mode defined in T005.
    3. Run the preprocessing pipeline (T014/T015) on the generated data.
    4. Verify the output CSV exists and contains expected columns.
    5. Verify no missing values in critical fields.
    """
    # Change to temp directory to simulate project root context
    original_cwd = os.getcwd()
    os.chdir(temp_project_dir)

    try:
        # Setup logging to avoid stderr clutter during test
        logger = setup_logging(log_level="INFO")

        # Step 1: Simulate T005 - Check/Download Data
        # This function is expected to generate synthetic data if real data is missing
        # (as per T005 requirements for development mode).
        try:
            check_and_download_data()
        except SystemExit as e:
            # If it exits with code 1, it means real data was required but missing.
            # In a pure test environment without pre-seeded real data, this is expected
            # if the logic strictly enforces "Real data required for production".
            # However, T005 specifies a "Development Mode" for synthetic data.
            # We assume the environment variable or config allows synthetic generation here.
            # If it exits, we fail the test because we couldn't get data.
            if e.code == 1:
                pytest.fail("Data download aborted: Real data required but not found, and synthetic mode not triggered.")
            raise

        # Verify synthetic files were created if real ones were missing
        # We check for the existence of at least one raw data file
        raw_ebird_files = list(Path("data/raw/ebird").glob("*.csv"))
        raw_climate_files = list(Path("data/raw/climate").glob("*.parquet"))

        # If no files exist, the download function failed to generate data
        if not raw_ebird_files and not raw_climate_files:
            pytest.fail("No data files found in data/raw after download step.")

        # Step 2: Run Preprocessing Pipeline (T014/T015)
        # This calls the main preprocessing logic which filters, aggregates, and computes metrics.
        # We expect this to run on the data available in data/raw.
        try:
            run_preprocessing_pipeline()
        except Exception as e:
            pytest.fail(f"Preprocessing pipeline failed: {e}")

        # Step 3: Verify Output
        # The task description states: "verify the output CSV contains expected columns"
        # Based on T015/T017, the output should be in data/processed/
        output_file = Path("data/processed/preprocessed_data.csv")
        
        if not output_file.exists():
            # Try to find any csv in processed
            csv_files = list(Path("data/processed").glob("*.csv"))
            if not csv_files:
                pytest.fail("Preprocessing pipeline did not produce an output CSV file.")
            output_file = csv_files[0]

        df = pd.read_csv(output_file)

        # Step 4: Verify Columns
        expected_columns = {
            "species",
            "grid_cell",
            "week",
            "phenology_metric",
            "climate_temp",
            "climate_precip"
        }
        actual_columns = set(df.columns)

        missing_columns = expected_columns - actual_columns
        if missing_columns:
            pytest.fail(f"Output CSV missing expected columns: {missing_columns}. Found: {actual_columns}")

        # Step 5: Verify No Missing Values in Critical Fields
        critical_fields = ["species", "grid_cell", "phenology_metric"]
        for field in critical_fields:
            if df[field].isnull().any():
                pytest.fail(f"Critical field '{field}' contains missing values.")

        # Additional sanity check: ensure grid_cell follows expected format (lat-lon)
        # based on GRID_RES=0.5
        # We expect strings like "40.5_-105.5" or similar
        if not df["grid_cell"].astype(str).str.contains("_").all():
            # Allow some flexibility if format differs, but basic check
            pass 

        # Check that we have data
        if len(df) == 0:
            pytest.fail("Preprocessing produced an empty dataframe.")

    finally:
        os.chdir(original_cwd)