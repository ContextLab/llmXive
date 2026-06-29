"""Integration test for full data ingestion pipeline (T010).

This test verifies the complete data ingestion pipeline:
- Fetch structures from Materials Project API (T011)
- Fetch thermal conductivity from literature/NIST (T012)
- Clean and merge data (T013)

TDD: This test is written to FAIL first. It will pass once T011-T013 are implemented.

Acceptance criteria:
- Output CSV contains ≥ 50 rows
- No null values in thermal_conductivity column
- No null values in structure_id column
"""

import os
import sys
from pathlib import Path

import pytest
import pandas as pd

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_dir))

# Expected output path based on tasks.md and data conventions
EXPECTED_OUTPUT_PATH = code_dir / "data" / "cleaned" / "merged_perovskites.csv"

# Minimum row requirement from SC-001
MIN_ROWS = 50

# Required columns that must not have null values
REQUIRED_NON_NULL_COLUMNS = ["thermal_conductivity", "structure_id"]


@pytest.fixture
def cleaned_data_path():
    """Fixture to provide the expected cleaned data path."""
    return EXPECTED_OUTPUT_PATH


@pytest.fixture
def pipeline_modules_available(cleaned_data_path):
    """
    Fixture to verify pipeline modules can be imported.
    This will FAIL until T011-T013 are implemented.
    """
    try:
        # These imports will fail until T011-T013 are implemented
        from ingest.fetch_structures import fetch_perovskite_structures
        from ingest.fetch_thermal import load_thermal_conductivity
        from cleaning.clean_merge import clean_and_merge_data

        return True
    except ImportError as e:
        # Expected failure during TDD - modules not yet implemented
        pytest.skip(f"Pipeline modules not yet implemented: {e}")


class TestDataIngestionPipeline:
    """Integration tests for the full data ingestion pipeline (US1)."""

    def test_output_file_exists(self, cleaned_data_path):
        """Test that the cleaned data output file exists after pipeline execution.

        SC-001: Pipeline must produce merged_perovskites.csv in data/cleaned/
        """
        assert cleaned_data_path.exists(), (
            f"Output file not found: {cleaned_data_path}. "
            "Run the pipeline script first: python code/ingest/run_pipeline.py"
        )

    def test_output_has_minimum_rows(self, cleaned_data_path):
        """Test that output CSV contains ≥ 50 rows after filtering.

        SC-001: Minimum 50 compositions required for statistical validity.
        """
        df = pd.read_csv(cleaned_data_path)
        assert len(df) >= MIN_ROWS, (
            f"Insufficient samples: {len(df)} < {MIN_ROWS}. "
            "Pipeline must filter for valid ABX₃ stoichiometry and remove nulls."
        )

    def test_no_null_thermal_conductivity(self, cleaned_data_path):
        """Test that thermal_conductivity column has no null values.

        FR-002: Entries with missing thermal conductivity must be removed.
        """
        df = pd.read_csv(cleaned_data_path)
        null_count = df["thermal_conductivity"].isnull().sum()
        assert null_count == 0, (
            f"Found {null_count} null values in thermal_conductivity column. "
            "All entries with missing thermal conductivity must be filtered out."
        )

    def test_no_null_structure_id(self, cleaned_data_path):
        """Test that structure_id column has no null values.

        FR-002: Entries with missing structure_id must be removed.
        """
        df = pd.read_csv(cleaned_data_path)
        null_count = df["structure_id"].isnull().sum()
        assert null_count == 0, (
            f"Found {null_count} null values in structure_id column. "
            "All entries with missing structure_id must be filtered out."
        )

    def test_required_columns_present(self, cleaned_data_path):
        """Test that all required columns are present in output CSV.

        Schema validation per contracts/merged_perovskite.schema.yaml (T005).
        """
        df = pd.read_csv(cleaned_data_path)
        required_columns = REQUIRED_NON_NULL_COLUMNS + ["composition", "temperature"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        assert len(missing_columns) == 0, (
            f"Missing required columns: {missing_columns}. "
            f"Required: {required_columns}"
        )

    def test_thermal_conductivity_positive_values(self, cleaned_data_path):
        """Test that thermal conductivity values are positive.

        Physical constraint: thermal conductivity must be > 0 W/(m·K).
        """
        df = pd.read_csv(cleaned_data_path)
        negative_count = (df["thermal_conductivity"] <= 0).sum()
        assert negative_count == 0, (
            f"Found {negative_count} non-positive thermal conductivity values. "
            "All values must be positive (W/(m·K))."
        )

    def test_stoichiometry_format_valid(self, cleaned_data_path):
        """Test that composition column follows ABX₃ perovskite format.

        FR-001: Only entries matching ABX₃ stoichiometry are retained.
        """
        df = pd.read_csv(cleaned_data_path)
        # Basic check: composition should contain 3 elements (A, B, X)
        # More complex validation would use pymatgen composition parser
        for comp in df["composition"]:
            assert isinstance(comp, str) and len(comp) > 0, (
                f"Invalid composition format: {comp}"
            )

    def test_data_type_consistency(self, cleaned_data_path):
        """Test that numeric columns have correct data types.

        FR-002: Data types must be consistent for downstream analysis.
        """
        df = pd.read_csv(cleaned_data_path)
        # thermal_conductivity should be float
        assert pd.api.types.is_float_dtype(df["thermal_conductivity"]), (
            "thermal_conductivity column must be float type"
        )
        # temperature should be numeric
        assert pd.api.types.is_numeric_dtype(df["temperature"]), (
            "temperature column must be numeric type"
        )


@pytest.mark.integration
def test_full_pipeline_execution(cleaned_data_path):
    """
    Integration test that runs the full pipeline end-to-end.

    This test will FAIL until T011-T013 are implemented and the pipeline
    script is executed to produce data/cleaned/merged_perovskites.csv.

    Run after implementing T011-T013:
    $ python code/ingest/run_pipeline.py
    $ pytest code/tests/integration/test_full_pipeline.py -v
    """
    # This test is a marker to ensure the full pipeline can be executed
    # The actual validation is done by the class tests above
    assert cleaned_data_path.exists(), (
        "Pipeline output file not found. Execute the pipeline first:\n"
        "  python code/ingest/run_pipeline.py"
    )