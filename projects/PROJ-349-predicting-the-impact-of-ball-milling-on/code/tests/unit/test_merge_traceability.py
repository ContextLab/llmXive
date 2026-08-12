"""
Unit tests for T015b: Validate Traceability.
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.ingest.merge import validate_traceability, process_flagged_entries
from src.utils.exceptions import InsufficientDataError


class TestValidateTraceability:
    """Tests for the validate_traceability function."""

    def test_all_rows_valid(self):
        """Test when all rows have source_name and source_id."""
        data = {
            "source_name": ["MP", "NIST", "arXiv"],
            "source_id": ["123", "456", "789"],
            "d50": [100.0, 200.0, 300.0],
        }
        df = pd.DataFrame(data)

        valid_count, flagged = validate_traceability(df)

        assert valid_count == 3
        assert len(flagged) == 0

    def test_missing_source_name(self):
        """Test when source_name is missing."""
        data = {
            "source_name": [None, "NIST", "arXiv"],
            "source_id": ["123", "456", "789"],
            "d50": [100.0, 200.0, 300.0],
        }
        df = pd.DataFrame(data)

        valid_count, flagged = validate_traceability(df)

        assert valid_count == 2
        assert len(flagged) == 1
        assert flagged[0]["issues"] == ["missing source_name"]
        assert flagged[0]["index"] == 0

    def test_missing_source_id(self):
        """Test when source_id is missing."""
        data = {
            "source_name": ["MP", "NIST", "arXiv"],
            "source_id": [None, "456", "789"],
            "d50": [100.0, 200.0, 300.0],
        }
        df = pd.DataFrame(data)

        valid_count, flagged = validate_traceability(df)

        assert valid_count == 2
        assert len(flagged) == 1
        assert flagged[0]["issues"] == ["missing source_id"]

    def test_both_missing(self):
        """Test when both source_name and source_id are missing."""
        data = {
            "source_name": [None, "NIST"],
            "source_id": [None, "456"],
            "d50": [100.0, 200.0],
        }
        df = pd.DataFrame(data)

        valid_count, flagged = validate_traceability(df)

        assert valid_count == 1
        assert len(flagged) == 1
        assert set(flagged[0]["issues"]) == {"missing source_name", "missing source_id"}

    def test_empty_dataframe(self):
        """Test with an empty DataFrame."""
        df = pd.DataFrame(columns=["source_name", "source_id", "d50"])

        valid_count, flagged = validate_traceability(df)

        assert valid_count == 0
        assert len(flagged) == 0

    def test_process_flagged_entries(self):
        """Test that flagged entries are saved to JSON."""
        flagged_data = [
            {"index": 0, "issues": ["missing source_name"], "source_name": None, "source_id": "123", "row_hash": "abc"}
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flagged.json"
            process_flagged_entries(flagged_data, str(output_path))

            assert output_path.exists()
            with open(output_path) as f:
                saved_data = json.load(f)

            assert len(saved_data) == 1
            assert saved_data[0]["index"] == 0
            assert saved_data[0]["issues"] == ["missing source_name"]