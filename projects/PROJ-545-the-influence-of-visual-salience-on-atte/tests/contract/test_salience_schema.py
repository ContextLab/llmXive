"""
Contract tests for Salience Enriched Dataset Schema.
Verifies that the output of the salience pipeline adheres to the expected schema.
"""
import os
import sys
import csv
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_COLUMNS = [
    "scenario_id", "salience_score", "salience_method", "image_url",
    "outcome", "species", "age", "gender", "social_status",
    "agency", "choice", "lives_saved", "lives_lost", "text_fallback_used"
]

def load_csv_as_dicts(csv_path: Path) -> List[Dict[str, Any]]:
    """Helper to load CSV into list of dicts."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def validate_row_schema(row: Dict[str, Any], row_idx: int) -> List[str]:
    """
    Validates a single row against the schema rules.
    Returns a list of error messages.
    """
    errors = []

    # Check required columns exist
    for col in REQUIRED_COLUMNS:
        if col not in row:
            errors.append(f"Row {row_idx}: Missing required column '{col}'")

    if "salience_score" in row:
        try:
            score = float(row["salience_score"])
            if not (0.0 <= score <= 1.0):
                errors.append(f"Row {row_idx}: salience_score {score} is not in [0.0, 1.0]")
        except ValueError:
            errors.append(f"Row {row_idx}: salience_score '{row['salience_score']}' is not numeric")

    if "salience_method" in row:
        valid_methods = {"itti_gvs", "text_heuristic", "fallback"}
        if row["salience_method"] not in valid_methods:
            errors.append(f"Row {row_idx}: salience_method '{row['salience_method']}' not in {valid_methods}")

    if "text_fallback_used" in row:
        val = str(row["text_fallback_used"]).lower()
        if val not in ("true", "false", "1", "0"):
            errors.append(f"Row {row_idx}: text_fallback_used '{row['text_fallback_used']}' is not boolean-like")

    return errors

def test_schema_columns_exist(sample_preprocessed_data: Path):
    """
    Contract Test: Verify all required columns exist in the header.
    """
    with open(sample_preprocessed_data, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
    
    missing = set(REQUIRED_COLUMNS) - set(header)
    assert len(missing) == 0, f"Missing required columns: {missing}"

def test_schema_numeric_range(sample_preprocessed_data: Path):
    """
    Contract Test: Verify salience_score is numeric and within [0.0, 1.0].
    """
    rows = load_csv_as_dicts(sample_preprocessed_data)
    for i, row in enumerate(rows):
        if "salience_score" in row:
            try:
                score = float(row["salience_score"])
                assert 0.0 <= score <= 1.0, f"Row {i}: salience_score {score} out of range"
            except ValueError:
                pytest.fail(f"Row {i}: salience_score is not numeric")

def test_schema_valid_methods(sample_preprocessed_data: Path):
    """
    Contract Test: Verify salience_method is one of the allowed values.
    """
    rows = load_csv_as_dicts(sample_preprocessed_data)
    valid_methods = {"itti_gvs", "text_heuristic", "fallback"}
    for i, row in enumerate(rows):
        if "salience_method" in row:
            assert row["salience_method"] in valid_methods, f"Row {i}: Invalid method {row['salience_method']}"

def test_schema_all_rows_valid(sample_preprocessed_data: Path):
    """
    Contract Test: Run full schema validation on all rows.
    """
    rows = load_csv_as_dicts(sample_preprocessed_data)
    all_errors = []
    for i, row in enumerate(rows):
        errors = validate_row_schema(row, i)
        all_errors.extend(errors)
    
    assert len(all_errors) == 0, f"Schema validation failed for {len(all_errors)} rows:\n" + "\n".join(all_errors)
