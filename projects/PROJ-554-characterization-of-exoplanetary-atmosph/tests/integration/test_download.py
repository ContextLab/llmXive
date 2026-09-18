"""
Integration tests for the NASA Exoplanet Archive data download pipeline.
This module verifies that the download logic correctly fetches and validates
metadata from the real API, ensuring data integrity before processing.
"""

import os
import sys
import json
import pytest
from pathlib import Path
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from download import fetch_raw_metadata, process_metadata, save_metadata_csv
from config import get_config
from data_models import PlanetCategory
from utils import setup_logging

# Setup logging for tests
logger = setup_logging("tests/integration/test_download.log")


@pytest.mark.integration
def test_download_returns_valid_metadata():
    """
    Integration test: Verify that the download pipeline returns valid metadata
    with non-null values for required fields.

    This test performs a real fetch from the NASA Exoplanet Archive API (or a
    verified local cache if configured) and validates the schema and data quality.
    It depends on T007 (data models) being implemented.

    Validates:
    1. The fetch function returns a non-empty list of records.
    2. The processed DataFrame contains required columns.
    3. Critical fields (temperature, metallicity, snr, resolution, planet_category)
       are populated (non-null) for the majority of rows.
    4. The output file `data/processed/metadata.csv` is created and readable.
    """
    # Ensure output directory exists
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "metadata.csv"

    # Remove existing file to ensure we are testing a fresh run
    if output_file.exists():
        output_file.unlink()

    try:
        # 1. Fetch raw metadata
        # Note: In a real CI environment with no network, this would fail.
        # However, per task requirements, we must use real data sources.
        # We catch the exception if the network is truly unreachable to provide
        # a meaningful test result rather than a generic import error.
        raw_data = fetch_raw_metadata()

        assert raw_data is not None, "fetch_raw_metadata returned None"
        assert len(raw_data) > 0, "fetch_raw_metadata returned empty list"

        logger.info(f"Fetched {len(raw_data)} raw records from NASA Exoplanet Archive.")

        # 2. Process metadata
        df = process_metadata(raw_data)

        assert isinstance(df, pd.DataFrame), "process_metadata did not return a DataFrame"
        assert len(df) > 0, "process_metadata returned empty DataFrame"

        # 3. Verify required columns exist
        required_columns = [
            'planet_name', 'temperature', 'metallicity', 'snr',
            'resolution', 'planet_category', 'instrument', 'wavelength_range'
        ]

        missing_cols = [col for col in required_columns if col not in df.columns]
        assert not missing_cols, f"Missing required columns: {missing_cols}"

        # 4. Verify data quality (non-null values for critical fields)
        # We allow a small tolerance for missing data in real-world APIs,
        # but the majority must be present.
        critical_fields = ['temperature', 'metallicity', 'snr', 'resolution', 'planet_category']

        for field in critical_fields:
            non_null_count = df[field].notna().sum()
            total_count = len(df)
            fill_rate = non_null_count / total_count if total_count > 0 else 0

            # Require at least 80% fill rate for critical fields
            assert fill_rate >= 0.80, (
                f"Field '{field}' has too many null values: "
                f"{non_null_count}/{total_count} ({fill_rate:.2%})"
            )
            logger.info(f"Field '{field}' fill rate: {fill_rate:.2%}")

        # 5. Verify planet_category values are valid enum members
        valid_categories = [cat.value for cat in PlanetCategory]
        invalid_cats = df[~df['planet_category'].isin(valid_categories)]
        assert len(invalid_cats) == 0, (
            f"Found invalid planet categories: {invalid_cats['planet_category'].unique()}"
        )

        # 6. Save to CSV (T012 implementation check)
        save_metadata_csv(df, str(output_file))

        assert output_file.exists(), "save_metadata_csv failed to create output file"

        # 7. Verify saved file is readable
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) == len(df), "Saved file row count mismatch"
        assert list(saved_df.columns) == list(df.columns), "Saved file column mismatch"

        logger.info("Integration test passed: Metadata schema and data quality validated.")

    except Exception as e:
        # Log the error but fail the test explicitly
        logger.error(f"Integration test failed with error: {e}", exc_info=True)
        raise e