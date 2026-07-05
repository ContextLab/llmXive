"""
Contract tests for model results output schema.

This module validates that the output file `data/processed/model_results.csv`
adheres to the schema defined in `contracts/output.schema.yaml`.

It ensures that:
1. The file exists at the expected path.
2. The CSV headers match the required schema columns.
3. Data types for each column are correct (numeric for stats, string for identifiers).
4. Required columns are present and non-null.
"""
import os
import csv
import pytest
import yaml
from pathlib import Path
from src.utils.config import get_project_root, get_processed_data_dir

# Expected schema definition based on contracts/output.schema.yaml
# This mirrors the expected structure for model_results.csv
EXPECTED_COLUMNS = [
    "model_id",
    "metric_name",
    "coefficient",
    "std_error",
    "t_value",
    "p_value",
    "confidence_interval_lower",
    "confidence_interval_upper",
    "effect_size",
    "fdr_corrected_p_value",
    "sample_size",
    "loso_cv_score",
    "status"
]

REQUIRED_COLUMNS = [
    "model_id",
    "metric_name",
    "coefficient",
    "p_value",
    "effect_size"
]

NUMERIC_COLUMNS = [
    "coefficient",
    "std_error",
    "t_value",
    "p_value",
    "confidence_interval_lower",
    "confidence_interval_upper",
    "effect_size",
    "fdr_corrected_p_value",
    "sample_size",
    "loso_cv_score"
]

class TestModelResultsSchema:
    """Contract tests for data/processed/model_results.csv"""

    @pytest.fixture
    def results_path(self):
        """Get the path to the model results file."""
        processed_dir = get_processed_data_dir()
        return processed_dir / "model_results.csv"

    def test_file_exists(self, results_path):
        """Contract: The model results file must exist."""
        assert results_path.exists(), f"Output file not found: {results_path}"

    def test_csv_headers_match_schema(self, results_path):
        """Contract: CSV headers must match the expected schema columns."""
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
        
        # Check that all required columns are present
        missing_required = set(REQUIRED_COLUMNS) - set(headers)
        assert not missing_required, (
            f"Missing required columns in {results_path}: {missing_required}"
        )
        
        # Check that all expected columns are present (allowing for extra columns if needed, 
        # but strictly checking for the defined schema set)
        missing_expected = set(EXPECTED_COLUMNS) - set(headers)
        if missing_expected:
            # Log a warning or fail depending on strictness. 
            # For contract tests, we usually fail if the schema contract is broken.
            pytest.fail(f"Schema mismatch: Missing expected columns: {missing_expected}. Found: {headers}")

    def test_numeric_columns_are_valid(self, results_path):
        """Contract: Numeric columns must contain valid numbers."""
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                for col in NUMERIC_COLUMNS:
                    if col not in row:
                        continue  # Handled by header check
                    
                    val = row[col]
                    if val is None or val == '':
                        # Allow empty for optional fields if schema permits, 
                        # but typically stats should be populated.
                        # For strict contract, we might require non-null.
                        # Assuming non-null for calculated stats.
                        if col in ["coefficient", "p_value", "effect_size"]:
                            pytest.fail(f"Row {row_idx}: Column '{col}' is empty but required.")
                        continue
                    
                    try:
                        float(val)
                    except ValueError:
                        pytest.fail(f"Row {row_idx}: Column '{col}' has non-numeric value '{val}'")

    def test_required_columns_non_null(self, results_path):
        """Contract: Required columns must not be null or empty."""
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                for col in REQUIRED_COLUMNS:
                    if col not in row or row[col] is None or row[col].strip() == '':
                        pytest.fail(f"Row {row_idx}: Required column '{col}' is null or empty.")

    def test_p_value_range(self, results_path):
        """Contract: P-values must be between 0 and 1."""
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                if "p_value" in row and row["p_value"]:
                    try:
                        p_val = float(row["p_value"])
                        assert 0.0 <= p_val <= 1.0, (
                            f"Row {row_idx}: p_value {p_val} is out of range [0, 1]"
                        )
                    except ValueError:
                        pass # Handled by numeric check

    def test_schema_definition_exists(self):
        """Contract: The schema definition file must exist."""
        project_root = get_project_root()
        schema_path = project_root / "contracts" / "output.schema.yaml"
        assert schema_path.exists(), f"Schema definition file missing: {schema_path}"

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Basic validation that the schema is a dict
        assert isinstance(schema, dict), "Schema file must contain a valid YAML dictionary"