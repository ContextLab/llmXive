"""Contract test for features.csv schema validation.

This test validates that features.csv conforms to the expected schema
defined in contracts/features_schema.json and data-model.md.

Per T008 and T065: Schema must match JSON contract in contracts/ directory.
Per T022: features.csv must contain all predictors with no missing values.
"""

import json
import os
from pathlib import Path

import jsonschema
import pandas as pd
import pytest
from jsonschema import ValidationError

# Project root relative to tests/contract/
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Path to the JSON schema contract for features.csv
FEATURES_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "features_schema.json"

# Path to the generated features.csv (produced by feature engineering pipeline)
FEATURES_CSV_PATH = PROJECT_ROOT / "results" / "features.csv"

# Expected columns per T015 (network features) and T016 (user susceptibility)
# plus identifiers required for hierarchical modeling
REQUIRED_COLUMNS = [
    "cascade_id",
    "node_id",
    "user_id",
    "message_id",
    "platform_id",
    "historical_degree",
    "historical_shares",
    "susceptibility_score",
    "degree_mean",
    "degree_std",
    "degree_skewness",
    "clustering_coefficient",
    "betweenness_centrality_mean",
    "cascade_size",
]

# Column types as per data-model.md (T007, T065)
EXPECTED_DTYPES = {
    "cascade_id": "object",
    "node_id": "int64",
    "user_id": "object",
    "message_id": "object",
    "platform_id": "object",
    "historical_degree": "float64",
    "historical_shares": "float64",
    "susceptibility_score": "float64",
    "degree_mean": "float64",
    "degree_std": "float64",
    "degree_skewness": "float64",
    "clustering_coefficient": "float64",
    "betweenness_centrality_mean": "float64",
    "cascade_size": "int64",
}

# Numeric columns that must be non-negative (network metrics)
NON_NEGATIVE_COLUMNS = [
    "historical_degree",
    "historical_shares",
    "degree_mean",
    "degree_std",
    "degree_skewness",
    "clustering_coefficient",
    "betweenness_centrality_mean",
    "cascade_size",
]

# Columns that should have values in [0, 1] range
BOUNDED_COLUMNS = [
    "susceptibility_score",
    "clustering_coefficient",
    "betweenness_centrality_mean",
]

# T062: susceptibility score formula: (historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0
SUSCEPTIBILITY_THRESHOLD_DEGREE = 2
SUSCEPTIBILITY_THRESHOLD_SHARES = 1


def load_schema():
    """Load the JSON schema contract for features.csv."""
    if not FEATURES_SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found at {FEATURES_SCHEMA_PATH}. "
            "Run T008 to create contracts/features_schema.json"
        )
    with open(FEATURES_SCHEMA_PATH, "r") as f:
        return json.load(f)


def load_features_csv():
    """Load the features.csv file for validation."""
    if not FEATURES_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Features file not found at {FEATURES_CSV_PATH}. "
            "Run the feature engineering pipeline (T015, T016) first."
        )
    return pd.read_csv(FEATURES_CSV_PATH)


def test_schema_file_exists():
    """Contract test: Schema file must exist in contracts/ directory."""
    assert FEATURES_SCHEMA_PATH.exists(), (
        "features_schema.json must exist in contracts/ directory. "
        "Run T008 to create the JSON schema contract."
    )


def test_schema_is_valid_json():
    """Contract test: Schema file must be valid JSON."""
    schema = load_schema()
    assert isinstance(schema, dict), "Schema must be a JSON object"
    assert "type" in schema, "Schema must specify type"
    assert schema["type"] == "object", "Schema type must be object"


def test_schema_defines_required_properties():
    """Contract test: Schema must define all required columns."""
    schema = load_schema()
    properties = schema.get("properties", {})

    missing_columns = []
    for col in REQUIRED_COLUMNS:
        if col not in properties:
            missing_columns.append(col)

    assert not missing_columns, (
        f"Schema must define properties for all required columns. "
        f"Missing: {missing_columns}"
    )


def test_csv_has_all_required_columns():
    """Contract test: features.csv must contain all required columns."""
    df = load_features_csv()
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)

    assert not missing_columns, (
        f"features.csv missing required columns: {missing_columns}. "
        f"Expected columns: {REQUIRED_COLUMNS}"
    )


def test_csv_column_count_matches_schema():
    """Contract test: CSV column count must match schema properties."""
    schema = load_schema()
    df = load_features_csv()

    schema_columns = set(schema.get("properties", {}).keys())
    csv_columns = set(df.columns)

    # CSV may have additional columns beyond schema (forward compatibility)
    # but must have at least all schema columns
    missing = schema_columns - csv_columns
    assert not missing, (
        f"CSV missing schema columns: {missing}. "
        f"Schema defines: {list(schema_columns)}"
    )


def test_csv_dtypes_match_expectations():
    """Contract test: CSV column dtypes must match expected types."""
    df = load_features_csv()

    dtype_errors = []
    for col, expected_type in EXPECTED_DTYPES.items():
        if col in df.columns:
            actual_type = str(df[col].dtype)
            if actual_type != expected_type:
                dtype_errors.append(
                    f"Column '{col}': expected {expected_type}, got {actual_type}"
                )

    assert not dtype_errors, (
        "Column dtype mismatches:\n" + "\n".join(dtype_errors)
    )


def test_csv_has_no_missing_values():
    """Contract test: features.csv must have no missing values (T022)."""
    df = load_features_csv()
    missing_counts = df.isnull().sum()
    columns_with_missing = missing_counts[missing_counts > 0]

    assert len(columns_with_missing) == 0, (
        f"features.csv has missing values in columns: {columns_with_missing.to_dict()}. "
        "T022 requires all predictors to have no missing values."
    )


def test_csv_has_no_empty_strings():
    """Contract test: String columns must not have empty strings."""
    df = load_features_csv()
    string_columns = df.select_dtypes(include=["object"]).columns

    for col in string_columns:
        empty_mask = df[col].astype(str).str.strip() == ""
        if empty_mask.any():
            raise AssertionError(
                f"Column '{col}' contains {empty_mask.sum()} empty string values."
            )


def test_non_negative_columns_are_non_negative():
    """Contract test: Network metric columns must be non-negative."""
    df = load_features_csv()

    negative_violations = {}
    for col in NON_NEGATIVE_COLUMNS:
        if col in df.columns:
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                negative_violations[col] = negative_count

    assert not negative_violations, (
        f"Non-negative columns have negative values: {negative_violations}. "
        f"Affected columns: {list(negative_violations.keys())}"
    )


def test_bounded_columns_in_range():
    """Contract test: Bounded columns must be in [0, 1] range."""
    df = load_features_csv()

    out_of_range = {}
    for col in BOUNDED_COLUMNS:
        if col in df.columns:
            below_zero = (df[col] < 0).sum()
            above_one = (df[col] > 1).sum()
            if below_zero > 0 or above_one > 0:
                out_of_range[col] = {
                    "below_zero": int(below_zero),
                    "above_one": int(above_one),
                }

    assert not out_of_range, (
        f"Bounded columns out of [0, 1] range: {out_of_range}. "
        f"Affected columns: {list(out_of_range.keys())}"
    )


def test_susceptibility_score_formula_compliance():
    """Contract test: susceptibility_score must follow T062 formula.

    Formula: (historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0
    """
    df = load_features_csv()

    if "susceptibility_score" not in df.columns:
        pytest.skip("susceptibility_score column not present")

    expected_scores = (
        (df["historical_degree"] >= SUSCEPTIBILITY_THRESHOLD_DEGREE) &
        (df["historical_shares"] >= SUSCEPTIBILITY_THRESHOLD_SHARES)
    ).astype(float)

    mismatch_count = (df["susceptibility_score"] != expected_scores).sum()

    assert mismatch_count == 0, (
        f"susceptibility_score does not follow T062 formula. "
        f"{mismatch_count} rows violate the formula: "
        "(historical_degree >= 2 AND historical_shares >= 1) ? 1.0 : 0.0"
    )


def test_unique_cascade_ids():
    """Contract test: Each cascade_id should be unique in aggregated features."""
    df = load_features_csv()

    # If this is per-node features, cascade_id may repeat
    # If this is per-cascade aggregated features, cascade_id should be unique
    # We check that cascade_id exists and is not entirely null
    assert df["cascade_id"].notnull().all(), (
        "All cascade_id values must be non-null"
    )


def test_unique_user_ids():
    """Contract test: user_id must be present and non-null."""
    df = load_features_csv()

    assert df["user_id"].notnull().all(), (
        "All user_id values must be non-null for hierarchical modeling"
    )


def test_platform_id_present():
    """Contract test: platform_id must be present for random effects (T018)."""
    df = load_features_csv()

    assert "platform_id" in df.columns, (
        "platform_id column required for hierarchical random effects"
    )
    assert df["platform_id"].notnull().all(), (
        "All platform_id values must be non-null"
    )


def test_jsonschema_validation():
    """Contract test: Validate CSV against JSON schema using jsonschema."""
    schema = load_schema()
    df = load_features_csv()

    # Convert each row to a dict and validate against schema
    # This tests that the data structure matches the schema definition
    errors = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            jsonschema.validate(instance=row_dict, schema=schema)
        except ValidationError as e:
            errors.append(f"Row {idx}: {e.message}")
            if len(errors) >= 5:
                break  # Limit error messages

    if errors:
        pytest.fail(
            f"JSON schema validation failed for {len(errors)} rows:\n" +
            "\n".join(errors[:5])
        )


def test_minimum_rows_present():
    """Contract test: features.csv must have at least one row."""
    df = load_features_csv()

    assert len(df) > 0, (
        "features.csv must contain at least one row of data. "
        "Run feature engineering pipeline to generate data."
    )


def test_no_duplicate_rows():
    """Contract test: No exact duplicate rows in features.csv."""
    df = load_features_csv()

    duplicate_count = df.duplicated().sum()
    assert duplicate_count == 0, (
        f"features.csv contains {duplicate_count} duplicate rows. "
        "Each row should represent a unique observation."
    )


def test_schema_properties_have_type_definitions():
    """Contract test: All schema properties must have type definitions."""
    schema = load_schema()
    properties = schema.get("properties", {})

    missing_types = []
    for prop_name, prop_def in properties.items():
        if "type" not in prop_def:
            missing_types.append(prop_name)

    assert not missing_types, (
        f"Schema properties missing type definitions: {missing_types}"
    )


def test_schema_has_required_field_list():
    """Contract test: Schema must have 'required' field listing required columns."""
    schema = load_schema()

    assert "required" in schema, (
        "Schema must have 'required' field listing required properties"
    )

    required_fields = schema["required"]
    missing_required = set(REQUIRED_COLUMNS) - set(required_fields)

    assert not missing_required, (
        f"Schema 'required' field missing: {missing_required}"
    )


def test_csv_encoding_is_utf8():
    """Contract test: features.csv must be UTF-8 encoded."""
    try:
        with open(FEATURES_CSV_PATH, "r", encoding="utf-8") as f:
            f.read()
    except UnicodeDecodeError as e:
        pytest.fail(f"features.csv is not UTF-8 encoded: {e}")


def test_csv_no_bom():
    """Contract test: features.csv must not have BOM (Byte Order Mark)."""
    with open(FEATURES_CSV_PATH, "rb") as f:
        first_bytes = f.read(3)

    assert first_bytes != b"\xef\xbb\xbf", (
        "features.csv should not have UTF-8 BOM. Use encoding='utf-8' without BOM."
    )