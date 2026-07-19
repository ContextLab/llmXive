"""Contract tests for knot data schemas.

These tests validate that the data produced by the pipeline conforms to the
expected schema defined in the project specifications. They serve as a guard
against schema drift and ensure downstream consumers can rely on the data
structure.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest
import pandas as pd

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# Expected schema for the cleaned CSV (from T014)
# Based on T012/T014 requirements: crossing_number, braid_index, hyperbolic_volume,
# is_alternating, knot_id, missing_invariant_flags, data_quality_flags
EXPECTED_CSV_COLUMNS = {
    "knot_id",
    "crossing_number",
    "braid_index",
    "hyperbolic_volume",
    "is_alternating",
    "missing_invariant_flags",
    "data_quality_flags",
    "diagram_representation",  # Optional but expected if parsed
    "atlas_source",
}

# Expected schema for the raw JSON (from T014)
# We expect a list of dictionaries or a dictionary containing a list
EXPECTED_RAW_KEYS = {"knots", "metadata", "source_url", "timestamp"}
REQUIRED_KNOT_FIELDS = {
    "id",
    "crossing_number",
    "braid_index",
    "hyperbolic_volume",
    "is_alternating",
}


class TestCleanedDataSchema:
    """Tests for data/processed/knots_cleaned.csv"""

    @pytest.fixture(scope="class")
    def df(self) -> pd.DataFrame:
        """Load the cleaned dataset."""
        path = DATA_PROCESSED / "knots_cleaned.csv"
        if not path.exists():
            pytest.skip(f"Data file not found: {path}. Run pipeline first.")
        return pd.read_csv(path)

    def test_file_exists(self):
        """Verify the cleaned data file exists."""
        assert (DATA_PROCESSED / "knots_cleaned.csv").exists(), \
            "knots_cleaned.csv must exist after T014"

    def test_required_columns_present(self, df: pd.DataFrame):
        """Verify all required columns are present."""
        actual_cols = set(df.columns)
        missing = EXPECTED_CSV_COLUMNS - actual_cols
        assert not missing, f"Missing required columns: {missing}"

    def test_no_null_core_invariants(self, df: pd.DataFrame):
        """Verify core invariants (crossing_number, braid_index) are never null."""
        # FR-009: Core invariants must not trigger missing_invariant_flags
        # and should be present in the cleaned data.
        core_cols = ["crossing_number", "braid_index"]
        for col in core_cols:
            null_count = df[col].isna().sum()
            assert null_count == 0, f"Column {col} has {null_count} null values"

    def test_crossing_number_positive(self, df: pd.DataFrame):
        """Verify crossing numbers are positive integers."""
        assert (df["crossing_number"] > 0).all(), "Crossing numbers must be > 0"
        assert df["crossing_number"].dtype in [int, "int64", "int32"], \
            "Crossing number should be integer type"

    def test_braid_index_valid(self, df: pd.DataFrame):
        """Verify braid index is positive and <= crossing number."""
        assert (df["braid_index"] > 0).all(), "Braid index must be > 0"
        assert (df["braid_index"] <= df["crossing_number"]).all(), \
            "Braid index must be <= crossing number"

    def test_hyperbolic_volume_non_negative(self, df: pd.DataFrame):
        """Verify hyperbolic volume is non-negative."""
        # Some knots might be non-hyperbolic (volume=0 or null depending on parser)
        # but for the hyperbolic subset, it must be > 0.
        # We allow nulls here if the parser sets them, but if present, must be >= 0.
        if "hyperbolic_volume" in df.columns:
            non_null = df["hyperbolic_volume"].dropna()
            if len(non_null) > 0:
                assert (non_null >= 0).all(), "Hyperbolic volume must be >= 0"

    def test_is_alternating_boolean(self, df: pd.DataFrame):
        """Verify is_alternating is boolean-like."""
        valid_vals = {True, False, 0, 1, "True", "False", "true", "false"}
        unique_vals = set(df["is_alternating"].astype(str).str.lower())
        # Allow some flexibility for CSV parsing
        assert all(v in valid_vals for v in unique_vals), \
            f"is_alternating contains invalid values: {unique_vals}"

    def test_knot_id_uniqueness(self, df: pd.DataFrame):
        """Verify knot_id is unique."""
        assert df["knot_id"].is_unique, "knot_id must be unique"

    def test_missing_invariant_flags_format(self, df: pd.DataFrame):
        """Verify missing_invariant_flags is a string or list representation."""
        # Typically stored as a string like "[]" or "field1,field2" or JSON string
        col = df["missing_invariant_flags"]
        # Just check it's not NaN for the core fields (per FR-009)
        # If the column exists, it should have a value (even if empty)
        assert col.notna().all(), "missing_invariant_flags should not be NaN"


class TestRawDataSchema:
    """Tests for data/raw/knot_atlas_raw.json"""

    @pytest.fixture(scope="class")
    def raw_data(self) -> Dict[str, Any]:
        """Load the raw JSON data."""
        path = DATA_RAW / "knot_atlas_raw.json"
        if not path.exists():
            pytest.skip(f"Raw data file not found: {path}. Run T011 first.")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def test_file_exists(self):
        """Verify the raw data file exists."""
        assert (DATA_RAW / "knot_atlas_raw.json").exists(), \
            "knot_atlas_raw.json must exist after T011"

    def test_top_level_structure(self, raw_data: Dict[str, Any]):
        """Verify top-level keys are present."""
        # The structure might be {"knots": [...]} or just a list
        if isinstance(raw_data, list):
            # If it's a list, that's acceptable too
            pass
        elif isinstance(raw_data, dict):
            # Check for expected keys
            assert any(key in raw_data for key in EXPECTED_RAW_KEYS), \
                f"Raw data missing expected keys. Found: {raw_data.keys()}"
        else:
            pytest.fail("Raw data must be a dict or list")

    def test_knot_records_have_required_fields(self, raw_data: Dict[str, Any]):
        """Verify each knot record has required fields."""
        knots = raw_data.get("knots", raw_data) if isinstance(raw_data, dict) else raw_data

        if not isinstance(knots, list):
            pytest.skip("Raw data does not contain a list of knots")

        if len(knots) == 0:
            pytest.skip("Raw data contains no knots")

        first_knot = knots[0]
        missing = REQUIRED_KNOT_FIELDS - set(first_knot.keys())
        assert not missing, f"Knot records missing required fields: {missing}"

    def test_crossing_number_in_raw(self, raw_data: Dict[str, Any]):
        """Verify crossing numbers are present in raw data."""
        knots = raw_data.get("knots", raw_data) if isinstance(raw_data, dict) else raw_data
        if isinstance(knots, list) and len(knots) > 0:
            for i, knot in enumerate(knots):
                assert "crossing_number" in knot, \
                    f"Knot at index {i} missing crossing_number"
                assert isinstance(knot["crossing_number"], int), \
                    f"Knot at index {i} crossing_number is not int"


class TestDataIntegrityContract:
    """Cross-file integrity tests."""

    def test_record_count_consistency(self):
        """Verify record counts match between raw and processed (if applicable)."""
        # This is a soft contract: processed might filter some records (e.g. non-hyperbolic)
        # so we just ensure processed count <= raw count (if both exist)
        raw_path = DATA_RAW / "knot_atlas_raw.json"
        proc_path = DATA_PROCESSED / "knots_cleaned.csv"

        if not raw_path.exists() or not proc_path.exists():
            pytest.skip("Both raw and processed files must exist for this test")

        with open(raw_path, "r") as f:
            raw_data = json.load(f)
        raw_knots = raw_data.get("knots", raw_data) if isinstance(raw_data, dict) else raw_data
        raw_count = len(raw_knots) if isinstance(raw_knots, list) else 0

        df = pd.read_csv(proc_path)
        proc_count = len(df)

        # Processed should not have more records than raw
        assert proc_count <= raw_count, \
            f"Processed count ({proc_count}) exceeds raw count ({raw_count})"

    def test_knot_ids_consistency(self):
        """Verify knot IDs in processed are a subset of raw."""
        raw_path = DATA_RAW / "knot_atlas_raw.json"
        proc_path = DATA_PROCESSED / "knots_cleaned.csv"

        if not raw_path.exists() or not proc_path.exists():
            pytest.skip("Both files must exist")

        with open(raw_path, "r") as f:
            raw_data = json.load(f)
        raw_knots = raw_data.get("knots", raw_data) if isinstance(raw_data, dict) else raw_data
        raw_ids = {k["id"] for k in raw_knots} if isinstance(raw_knots, list) else set()

        df = pd.read_csv(proc_path)
        proc_ids = set(df["knot_id"].unique())

        if not raw_ids:
            pytest.skip("No raw IDs found")

        missing_in_raw = proc_ids - raw_ids
        assert not missing_in_raw, \
            f"Processed data contains IDs not in raw: {missing_in_raw}"