"""
Contract tests for report schemas, specifically top_features.csv (US2).
"""
import os
import sys
import csv
import json
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

import pytest
from config import get_reports_path


REQUIRED_TOP_FEATURES_COLUMNS = {
    "feature_id",
    "feature_type",
    "selection_frequency",
    "p_value",
    "adj_p_value",
    "effect_size",
    "rank"
}

REQUIRED_METRICS_JSON_KEYS = {
    "cv_accuracy",
    "auc_roc",
    "r_squared",
    "null_model_accuracy",
    "null_model_auc",
    "null_model_r2",
    "permutation_p_value",
    "model_type",
    "timestamp"
}

REQUIRED_SELECTION_FREQUENCY_COLUMNS = {
    "feature_id",
    "threshold",
    "frequency"
}


class TestTopFeaturesSchema:
    """Contract tests for artifacts/reports/top_features.csv schema."""

    @pytest.fixture
    def reports_path(self):
        """Provide the path to the reports directory."""
        return get_reports_path()

    def test_top_features_file_exists(self, reports_path):
        """Verify that top_features.csv exists in the reports directory."""
        file_path = reports_path / "top_features.csv"
        assert file_path.exists(), f"File not found: {file_path}"

    def test_top_features_csv_is_valid(self, reports_path):
        """Verify that top_features.csv is a valid CSV file."""
        file_path = reports_path / "top_features.csv"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
            assert len(rows) >= 1, "CSV file is empty (no header)."
        except csv.Error as e:
            pytest.fail(f"Invalid CSV format: {e}")

    def test_top_features_has_required_columns(self, reports_path):
        """Verify that top_features.csv contains all required columns."""
        file_path = reports_path / "top_features.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = set(reader.fieldnames) if reader.fieldnames else set()

        missing_columns = REQUIRED_TOP_FEATURES_COLUMNS - header
        assert not missing_columns, (
            f"Missing required columns in top_features.csv: {missing_columns}. "
            f"Expected: {REQUIRED_TOP_FEATURES_COLUMNS}, Found: {header}"
        )

    def test_top_features_has_at_least_one_row(self, reports_path):
        """Verify that top_features.csv contains at least one data row."""
        file_path = reports_path / "top_features.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) >= 1, "top_features.csv has no data rows."

    def test_feature_type_is_valid(self, reports_path):
        """Verify that feature_type column contains only valid values."""
        file_path = reports_path / "top_features.csv"
        valid_types = {"SNP", "metabolite"}
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ftype = row.get("feature_type", "").strip().lower()
                assert ftype in {t.lower() for t in valid_types}, (
                    f"Invalid feature_type '{row.get('feature_type')}' in row. "
                    f"Valid types: {valid_types}"
                )

    def test_rank_column_is_monotonic(self, reports_path):
        """Verify that the rank column is strictly increasing integers starting from 1."""
        file_path = reports_path / "top_features.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ranks = []
            for row in reader:
                try:
                    rank_val = int(row["rank"])
                    ranks.append(rank_val)
                except (ValueError, KeyError):
                    pytest.fail("Rank column contains non-integer or missing values.")

        assert ranks == list(range(1, len(ranks) + 1)), (
            f"Rank column is not strictly increasing from 1. "
            f"Found: {ranks[:10]}..."
        )

    def test_p_values_are_numeric(self, reports_path):
        """Verify that p_value and adj_p_value columns contain numeric values."""
        file_path = reports_path / "top_features.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    float(row["p_value"])
                    float(row["adj_p_value"])
                except (ValueError, KeyError) as e:
                    pytest.fail(f"p_value or adj_p_value is not numeric: {e}")

    def test_effect_size_is_numeric(self, reports_path):
        """Verify that effect_size column contains numeric values."""
        file_path = reports_path / "top_features.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    float(row["effect_size"])
                except (ValueError, KeyError) as e:
                    pytest.fail(f"effect_size is not numeric: {e}")


class TestMetricsJsonSchema:
    """Contract tests for artifacts/reports/metrics.json schema."""

    @pytest.fixture
    def reports_path(self):
        """Provide the path to the reports directory."""
        return get_reports_path()

    def test_metrics_file_exists(self, reports_path):
        """Verify that metrics.json exists in the reports directory."""
        file_path = reports_path / "metrics.json"
        assert file_path.exists(), f"File not found: {file_path}"

    def test_metrics_file_is_valid_json(self, reports_path):
        """Verify that metrics.json is a valid JSON file."""
        file_path = reports_path / "metrics.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON format: {e}")

    def test_metrics_has_required_keys(self, reports_path):
        """Verify that metrics.json contains all required top-level keys."""
        file_path = reports_path / "metrics.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        missing_keys = REQUIRED_METRICS_JSON_KEYS - set(data.keys())
        assert not missing_keys, (
            f"Missing required keys in metrics.json: {missing_keys}. "
            f"Expected: {REQUIRED_METRICS_JSON_KEYS}, Found: {set(data.keys())}"
        )

    def test_metrics_numeric_values_are_floats(self, reports_path):
        """Verify that numeric metric values are floats."""
        file_path = reports_path / "metrics.json"
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        numeric_keys = [
            "cv_accuracy", "auc_roc", "r_squared",
            "null_model_accuracy", "null_model_auc", "null_model_r2",
            "permutation_p_value"
        ]
        for key in numeric_keys:
            if key in data:
                assert isinstance(data[key], (int, float)), (
                    f"Key '{key}' should be numeric, got {type(data[key])}"
                )


class TestSelectionFrequencySchema:
    """Contract tests for artifacts/reports/selection_frequency.csv schema."""

    @pytest.fixture
    def reports_path(self):
        """Provide the path to the reports directory."""
        return get_reports_path()

    def test_selection_frequency_file_exists(self, reports_path):
        """Verify that selection_frequency.csv exists in the reports directory."""
        file_path = reports_path / "selection_frequency.csv"
        assert file_path.exists(), f"File not found: {file_path}"

    def test_selection_frequency_has_required_columns(self, reports_path):
        """Verify that selection_frequency.csv contains all required columns."""
        file_path = reports_path / "selection_frequency.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = set(reader.fieldnames) if reader.fieldnames else set()

        missing_columns = REQUIRED_SELECTION_FREQUENCY_COLUMNS - header
        assert not missing_columns, (
            f"Missing required columns in selection_frequency.csv: {missing_columns}. "
            f"Expected: {REQUIRED_SELECTION_FREQUENCY_COLUMNS}, Found: {header}"
        )

    def test_frequency_values_are_between_0_and_1(self, reports_path):
        """Verify that frequency column values are between 0 and 1."""
        file_path = reports_path / "selection_frequency.csv"
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    freq = float(row["frequency"])
                    assert 0.0 <= freq <= 1.0, (
                        f"Frequency value {freq} is outside [0, 1] range."
                    )
                except (ValueError, KeyError) as e:
                    pytest.fail(f"Frequency is not numeric: {e}")

    def test_threshold_values_are_valid(self, reports_path):
        """Verify that threshold column contains expected threshold values."""
        file_path = reports_path / "selection_frequency.csv"
        valid_thresholds = {"0.01", "0.05", "0.1"}
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                threshold = row.get("threshold", "").strip()
                assert threshold in valid_thresholds, (
                    f"Invalid threshold '{threshold}'. Expected one of: {valid_thresholds}"
                )