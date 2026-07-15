"""
Contract test for visual metrics intermediate output (data/processed/visual_metrics_intermediate.csv).
Validates structure and types against the dataset schema.
"""
import os
import csv
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(PROJECT_ROOT, "data/processed/visual_metrics_intermediate.csv")

REQUIRED_COLUMNS = {
    "participant_id": "string",
    "image_path": "string",
    "edge_density": "float",
    "color_entropy": "float",
    "object_count": "integer"
}


def load_data():
    """Load the visual metrics CSV."""
    if not os.path.exists(DATA_PATH):
        pytest.skip(f"Data file not found at {DATA_PATH}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_columns_present():
    """Verify all required columns exist."""
    data = load_data()
    if not data:
        pytest.skip("No data rows to validate")

    actual_cols = set(data[0].keys())
    missing_cols = set(REQUIRED_COLUMNS.keys()) - actual_cols

    assert not missing_cols, f"Missing required columns: {missing_cols}"


def test_edge_density_range():
    """Verify edge_density is normalized between 0 and 1."""
    data = load_data()
    for row in data:
        try:
            val = float(row["edge_density"])
            assert 0.0 <= val <= 1.0, f"Edge density out of range: {val}"
        except ValueError:
            pytest.fail(f"Invalid edge_density value: {row['edge_density']}")


def test_color_entropy_non_negative():
    """Verify color_entropy is non-negative."""
    data = load_data()
    for row in data:
        try:
            val = float(row["color_entropy"])
            assert val >= 0.0, f"Color entropy is negative: {val}"
        except ValueError:
            pytest.fail(f"Invalid color_entropy value: {row['color_entropy']}")


def test_object_count_non_negative():
    """Verify object_count is non-negative integer."""
    data = load_data()
    for row in data:
        try:
            val = int(row["object_count"])
            assert val >= 0, f"Object count is negative: {val}"
        except ValueError:
            # Allow NaN or empty for failures if handled by pipeline
            if row["object_count"] not in ("", "nan", "NaN", "null"):
                pytest.fail(f"Invalid object_count value: {row['object_count']}")