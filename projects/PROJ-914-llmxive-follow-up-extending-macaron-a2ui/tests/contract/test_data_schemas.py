"""
Contract test for data schema validation.

Validates that the annotated data and hold-out set conform to the 
schemas defined in specs/001-llmxive-a2ui-latency-study/contracts/.

This test ensures:
1. The raw CSV schema matches `simulation_input.schema.yaml` expectations.
2. The annotated CSV schema matches the required output format.
3. The hold-out set schema matches the validation requirements.
"""
import os
import sys
import pytest
import pandas as pd
import yaml
from pathlib import Path

# Add code root to path for imports if running from tests/
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from utils.logging import get_experiment_logger

logger = get_experiment_logger("contract_tests")

# Constants for paths relative to project root
PROJECT_ROOT = code_root.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-a2ui-latency-study" / "contracts"
DATA_DIR = PROJECT_ROOT / "data"

# Expected paths for generated data (based on T012, T012b, T015)
RAW_CSV_PATH = DATA_DIR / "raw_a2ui_bench.csv"
ANNOTATED_CSV_PATH = DATA_DIR / "annotated_turns.csv"
HOLDOUT_CSV_PATH = DATA_DIR / "holdout_annotation_set.csv"

# Schema file names
SCHEMA_INPUT = CONTRACTS_DIR / "simulation_input.schema.yaml"
SCHEMA_OUTPUT = CONTRACTS_DIR / "simulation_output.schema.yaml"

def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_columns(df: pd.DataFrame, required_columns: list, source_name: str):
    """Validate that a DataFrame contains all required columns."""
    missing = set(required_columns) - set(df.columns)
    if missing:
        pytest.fail(f"Schema validation failed for {source_name}: missing columns {missing}")
    
    # Check for unexpected columns if strict mode is needed (optional)
    # extra = set(df.columns) - set(required_columns)
    # if extra:
    #     logger.warning(f"Extra columns found in {source_name}: {extra}")

def validate_data_types(df: pd.DataFrame, type_map: dict, source_name: str):
    """Validate basic data types of columns."""
    for col, expected_type in type_map.items():
        if col not in df.columns:
            continue # Handled by column validation
        
        if expected_type == "string":
            if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_object_dtype(df[col]):
                pytest.fail(f"Type mismatch for {col} in {source_name}: expected string, got {df[col].dtype}")
        elif expected_type == "integer":
            if not pd.api.types.is_integer_dtype(df[col]):
                pytest.fail(f"Type mismatch for {col} in {source_name}: expected integer, got {df[col].dtype}")
        elif expected_type == "float":
            if not pd.api.types.is_float_dtype(df[col]):
                pytest.fail(f"Type mismatch for {col} in {source_name}: expected float, got {df[col].dtype}")
        elif expected_type == "boolean":
            if not pd.api.types.is_bool_dtype(df[col]):
                pytest.fail(f"Type mismatch for {col} in {source_name}: expected boolean, got {df[col].dtype}")

@pytest.fixture(scope="module")
def raw_data():
    """Load raw data if it exists."""
    if not RAW_CSV_PATH.exists():
        pytest.skip(f"Raw data file not found at {RAW_CSV_PATH}. Run T012 first.")
    return pd.read_csv(RAW_CSV_PATH)

@pytest.fixture(scope="module")
def annotated_data():
    """Load annotated data if it exists."""
    if not ANNOTATED_CSV_PATH.exists():
        pytest.skip(f"Annotated data file not found at {ANNOTATED_CSV_PATH}. Run T012b first.")
    return pd.read_csv(ANNOTATED_CSV_PATH)

@pytest.fixture(scope="module")
def holdout_data():
    """Load holdout data if it exists."""
    if not HOLDOUT_CSV_PATH.exists():
        pytest.skip(f"Holdout data file not found at {HOLDOUT_CSV_PATH}. Run T015 first.")
    return pd.read_csv(HOLDOUT_CSV_PATH)

class TestRawDataSchema:
    """Tests for the raw input data schema (T012 output)."""
    
    def test_raw_schema_exists(self):
        """Verify the input schema definition exists."""
        assert SCHEMA_INPUT.exists(), f"Input schema file missing: {SCHEMA_INPUT}"

    def test_raw_columns(self, raw_data):
        """Verify raw data has required columns from simulation_input.schema.yaml."""
        schema = load_schema(SCHEMA_INPUT)
        required_cols = schema.get("required_fields", [])
        validate_columns(raw_data, required_cols, "raw_a2ui_bench.csv")

    def test_raw_types(self, raw_data):
        """Verify raw data types match schema expectations."""
        schema = load_schema(SCHEMA_INPUT)
        type_map = schema.get("type_map", {})
        if type_map:
            validate_data_types(raw_data, type_map, "raw_a2ui_bench.csv")

class TestAnnotatedDataSchema:
    """Tests for the annotated data schema (T012b output)."""
    
    def test_annotated_schema_exists(self):
        """Verify the output schema definition exists."""
        assert SCHEMA_OUTPUT.exists(), f"Output schema file missing: {SCHEMA_OUTPUT}"

    def test_annotated_columns(self, annotated_data):
        """Verify annotated data has required columns from simulation_output.schema.yaml."""
        schema = load_schema(SCHEMA_OUTPUT)
        required_cols = schema.get("required_fields", [])
        # Ensure specific columns mentioned in tasks are present
        required_cols.extend(["query", "ground_truth_intent", "complexity_score"])
        required_cols = list(set(required_cols)) # Deduplicate
        validate_columns(annotated_data, required_cols, "annotated_turns.csv")

    def test_annotated_types(self, annotated_data):
        """Verify annotated data types."""
        schema = load_schema(SCHEMA_OUTPUT)
        type_map = schema.get("type_map", {})
        # Add specific type expectations for annotation fields
        type_map["ground_truth_intent"] = "string"
        type_map["complexity_score"] = "integer"
        if type_map:
            validate_data_types(annotated_data, type_map, "annotated_turns.csv")

    def test_annotated_label_validity(self, annotated_data):
        """Verify that labels are valid (High-Confidence or Ambiguous)."""
        valid_labels = {"High-Confidence", "Ambiguous"}
        if "label" in annotated_data.columns:
            invalid_labels = set(annotated_data["label"].unique()) - valid_labels
            assert len(invalid_labels) == 0, f"Invalid labels found: {invalid_labels}"

class TestHoldoutDataSchema:
    """Tests for the holdout set schema (T015 output)."""
    
    def test_holdout_columns(self, holdout_data):
        """Verify holdout data has required columns."""
        required_cols = ["query", "ground_truth_intent", "complexity_score", "human_label"]
        validate_columns(holdout_data, required_cols, "holdout_annotation_set.csv")

    def test_holdout_size(self, holdout_data):
        """Verify holdout set has exactly N=50 rows."""
        assert len(holdout_data) == 50, f"Holdout set size is {len(holdout_data)}, expected 50"

    def test_holdout_no_duplicates(self, holdout_data):
        """Verify holdout set has no duplicate queries."""
        if "query" in holdout_data.columns:
            duplicates = holdout_data[holdout_data.duplicated(subset=["query"], keep=False)]
            assert len(duplicates) == 0, f"Found duplicate queries in holdout set: {duplicates['query'].tolist()}"

    def test_holdout_label_validity(self, holdout_data):
        """Verify holdout labels are valid."""
        valid_labels = {"High-Confidence", "Ambiguous"}
        if "human_label" in holdout_data.columns:
            invalid_labels = set(holdout_data["human_label"].unique()) - valid_labels
            assert len(invalid_labels) == 0, f"Invalid labels found in holdout: {invalid_labels}"