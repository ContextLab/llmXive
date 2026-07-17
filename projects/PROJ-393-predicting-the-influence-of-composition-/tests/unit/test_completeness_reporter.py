"""
Unit tests for the Completeness Reporter module.
"""
import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.preprocessing.completeness_reporter import (
    load_processed_data,
    calculate_source_proportions,
    generate_completeness_report,
    REQUIRED_SOURCE_COLUMN
)


class TestCompletenessReporter:

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame with source_type column."""
        data = {
            "alloy": ["Co2MnGa", "Co2FeAl", "NiMnSb", "Co2MnSi"],
            "source_type": ["NIST", "NIST", "Journal", "Manual"]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_csv_path(self, sample_df):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_df.to_csv(f, index=False)
            path = Path(f.name)
        yield path
        path.unlink(missing_ok=True)

    def test_load_processed_data_success(self, temp_csv_path):
        """Test successful loading of processed data."""
        df = load_processed_data(temp_csv_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4
        assert REQUIRED_SOURCE_COLUMN in df.columns

    def test_load_processed_data_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(Path("non_existent_file.csv"))

    def test_load_processed_data_missing_column(self):
        """Test error handling for missing required column."""
        data = {"alloy": ["A", "B"], "value": [1, 2]}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame(data).to_csv(f, index=False)
            path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                load_processed_data(path)
            assert REQUIRED_SOURCE_COLUMN in str(exc_info.value)
        finally:
            path.unlink(missing_ok=True)

    def test_calculate_source_proportions(self, sample_df):
        """Test proportion calculation logic."""
        result = calculate_source_proportions(sample_df)

        assert "counts" in result
        assert "proportions" in result
        assert "total_records" in result

        assert result["total_records"] == 4
        assert result["counts"]["NIST"] == 2
        assert result["counts"]["Journal"] == 1
        assert result["counts"]["Manual"] == 1

        # Check proportions (allowing for float precision)
        assert abs(result["proportions"]["NIST"] - 0.5) < 0.01
        assert abs(result["proportions"]["Journal"] - 0.25) < 0.01
        assert abs(result["proportions"]["Manual"] - 0.25) < 0.01

    def test_calculate_source_proportions_empty_df(self):
        """Test behavior with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["alloy", REQUIRED_SOURCE_COLUMN])
        result = calculate_source_proportions(empty_df)

        assert result["total_records"] == 0
        assert result["counts"] == {}
        assert result["proportions"] == {}

    def test_generate_completeness_report(self, sample_df):
        """Test full report generation and file writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            report = generate_completeness_report(sample_df, output_path)

            # Verify file exists
            assert output_path.exists()

            # Verify content
            with open(output_path, 'r') as f:
                loaded_report = json.load(f)

            assert loaded_report["total_records"] == 4
            assert loaded_report["report_type"] == "data_completeness"
            assert "proportions" in loaded_report