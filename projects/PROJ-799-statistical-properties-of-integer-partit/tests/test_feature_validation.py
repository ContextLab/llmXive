"""
Test suite for T016b: Validate data/processed/features.csv.

This test verifies that the feature engineering pipeline (T016a) has produced
a valid CSV file containing the required columns:
1. 'distance_to_nearest_prime'
2. 'sin_log_n' (oscillatory term)
3. 'cos_log_n' (oscillatory term)

It also verifies that these columns contain no null/NaN values for the rows
that were processed.
"""
import os
import csv
import math
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FEATURES_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "features.csv")

REQUIRED_COLUMNS = [
    "distance_to_nearest_prime",
    "sin_log_n",
    "cos_log_n"
]

@pytest.fixture
def features_data():
    """Load the features CSV if it exists."""
    if not os.path.exists(FEATURES_PATH):
        pytest.skip(f"Feature file {FEATURES_PATH} not found. Run T016a first.")
    
    rows = []
    with open(FEATURES_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    if not rows:
        pytest.fail("Feature file is empty.")
    
    return rows

def test_features_file_exists():
    """Verify that the features file exists at the expected path."""
    assert os.path.exists(FEATURES_PATH), f"Features file {FEATURES_PATH} does not exist."

def test_required_columns_present(features_data):
    """Verify all required columns are present in the CSV header."""
    if not features_data:
        pytest.fail("No data to check columns.")
    
    header = features_data[0].keys()
    for col in REQUIRED_COLUMNS:
        assert col in header, f"Missing required column: {col}"

def test_distance_to_nearest_prime_non_null(features_data):
    """Verify 'distance_to_nearest_prime' has no null/NaN values."""
    col = "distance_to_nearest_prime"
    for i, row in enumerate(features_data):
        val = row.get(col)
        if val is None or val == '':
            pytest.fail(f"Row {i}: {col} is null or empty.")
        try:
            float_val = float(val)
            if math.isnan(float_val):
                pytest.fail(f"Row {i}: {col} is NaN.")
        except ValueError:
            pytest.fail(f"Row {i}: {col} is not a valid number: {val}")

def test_oscillatory_terms_non_null(features_data):
    """Verify 'sin_log_n' and 'cos_log_n' have no null/NaN values."""
    for col in ["sin_log_n", "cos_log_n"]:
        for i, row in enumerate(features_data):
            val = row.get(col)
            if val is None or val == '':
                pytest.fail(f"Row {i}: {col} is null or empty.")
            try:
                float_val = float(val)
                if math.isnan(float_val):
                    pytest.fail(f"Row {i}: {col} is NaN.")
            except ValueError:
                pytest.fail(f"Row {i}: {col} is not a valid number: {val}")

def test_oscillatory_terms_range(features_data):
    """Verify oscillatory terms are within valid range [-1, 1]."""
    for col in ["sin_log_n", "cos_log_n"]:
        for i, row in enumerate(features_data):
            val = float(row[col])
            if val < -1.0 - 1e-9 or val > 1.0 + 1e-9:
                pytest.fail(f"Row {i}: {col} is out of range [-1, 1]: {val}")

def test_distance_is_non_negative(features_data):
    """Verify 'distance_to_nearest_prime' is non-negative."""
    for i, row in enumerate(features_data):
        val = float(row["distance_to_nearest_prime"])
        if val < 0:
            pytest.fail(f"Row {i}: distance_to_nearest_prime is negative: {val}")