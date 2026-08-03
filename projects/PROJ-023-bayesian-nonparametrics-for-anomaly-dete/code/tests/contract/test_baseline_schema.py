"""
Contract tests for baseline anomaly detection outputs.

Validates that Shewhart, CUSUM, and VAE baseline scripts produce outputs
matching the schemas defined in contracts/baseline.schema.yaml.

These tests verify:
- Required columns exist (timestamp, value, anomaly_score, anomaly_flag)
- Data types are correct (floats for scores, integers for flags)
- Value ranges are valid (flags are 0 or 1)
- No missing values in critical columns
"""
import pytest
import yaml
import pandas as pd
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Baseline output files to test
BASELINE_FILES = {
    "shewhart": RESULTS_DIR / "shewhart_predictions.csv",
    "cusum": RESULTS_DIR / "cusum_predictions.csv",
    "vae": RESULTS_DIR / "vae_predictions.csv"
}

def load_schema(schema_name: str = "baseline") -> Dict[str, Any]:
    """Load the baseline prediction schema from contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_predictions(file_path: Path) -> pd.DataFrame:
    """Load predictions from CSV file with type validation."""
    if not file_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    # Ensure required columns exist
    required_cols = ['timestamp', 'value', 'anomaly_score', 'anomaly_flag']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

class TestBaselinePredictionSchema:
    """Test suite for validating baseline prediction output schemas."""

    @pytest.fixture(scope="class")
    def schema(self) -> Dict[str, Any]:
        """Load the baseline schema for all tests in this class."""
        return load_schema("baseline")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_required_columns_exist(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that all required columns are present in baseline outputs."""
        try:
            df = load_predictions(file_path)
            required_cols = schema.get("required_columns", [])
            
            for col in required_cols:
                assert col in df.columns, f"Missing column '{col}' in {baseline_name} predictions"
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_column_data_types(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that column data types match the schema."""
        try:
            df = load_predictions(file_path)
            type_schema = schema.get("column_types", {})
            
            for col, expected_type in type_schema.items():
                if col in df.columns:
                    if expected_type == "float":
                        assert pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_numeric_dtype(df[col]), \
                            f"Column '{col}' should be numeric in {baseline_name}"
                    elif expected_type == "integer":
                        assert pd.api.types.is_integer_dtype(df[col]) or pd.api.types.is_numeric_dtype(df[col]), \
                            f"Column '{col}' should be numeric in {baseline_name}"
                    elif expected_type == "datetime":
                        assert pd.api.types.is_datetime64_any_dtype(df[col]) or df[col].dtype == 'object', \
                            f"Column '{col}' should be datetime or object in {baseline_name}"
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_anomaly_flag_values(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that anomaly_flag contains only valid values (0 or 1)."""
        try:
            df = load_predictions(file_path)
            flag_col = schema.get("anomaly_flag_column", "anomaly_flag")
            
            if flag_col in df.columns:
                unique_values = set(df[flag_col].dropna().unique())
                valid_values = {0, 1, 0.0, 1.0}
                invalid_values = unique_values - valid_values
                
                assert len(invalid_values) == 0, \
                    f"Invalid anomaly flag values {invalid_values} in {baseline_name}. Expected only 0 or 1."
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_no_missing_critical_values(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that critical columns have no missing values."""
        try:
            df = load_predictions(file_path)
            critical_cols = schema.get("critical_columns", ["timestamp", "anomaly_score", "anomaly_flag"])
            
            for col in critical_cols:
                if col in df.columns:
                    missing_count = df[col].isna().sum()
                    assert missing_count == 0, \
                        f"Column '{col}' has {missing_count} missing values in {baseline_name}"
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_anomaly_score_range(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that anomaly scores are within expected ranges."""
        try:
            df = load_predictions(file_path)
            score_col = schema.get("anomaly_score_column", "anomaly_score")
            
            if score_col in df.columns:
                # For most methods, scores should be non-negative
                assert (df[score_col] >= 0).all(), \
                    f"Negative anomaly scores found in {baseline_name}"
                
                # Check for reasonable upper bounds (avoiding NaN/Inf)
                if df[score_col].dtype in [np.float64, np.float32]:
                    assert not np.isinf(df[score_col]).any(), \
                        f"Infinite anomaly scores found in {baseline_name}"
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_file_size_reasonable(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that output files have a reasonable number of rows."""
        try:
            df = load_predictions(file_path)
            min_rows = schema.get("min_rows", 10)
            max_rows = schema.get("max_rows", 1000000)
            
            assert len(df) >= min_rows, \
                f"{baseline_name} predictions have too few rows ({len(df)} < {min_rows})"
            assert len(df) <= max_rows, \
                f"{baseline_name} predictions have too many rows ({len(df)} > {max_rows})"
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_consistency_with_ground_truth(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Test that baseline predictions align with ground truth timestamps."""
        try:
            df = load_predictions(file_path)
            gt_path = PROJECT_ROOT / "data" / "processed" / "ground_truth.csv"
            
            if not gt_path.exists():
                pytest.skip(f"Ground truth file not found: {gt_path}")
            
            gt_df = pd.read_csv(gt_path)
            
            # Check timestamp alignment
            if 'timestamp' in df.columns and 'timestamp' in gt_df.columns:
                pred_timestamps = set(df['timestamp'].unique())
                gt_timestamps = set(gt_df['timestamp'].unique())
                
                # All prediction timestamps should exist in ground truth
                extra_timestamps = pred_timestamps - gt_timestamps
                assert len(extra_timestamps) == 0, \
                    f"{baseline_name} has {len(extra_timestamps)} timestamps not in ground truth"
        except FileNotFoundError:
            pytest.skip(f"Required files not found. Run data processing scripts first.")

    @pytest.mark.parametrize("baseline_name,file_path", BASELINE_FILES.items())
    def test_schema_compliance(self, baseline_name: str, file_path: Path, schema: Dict[str, Any]):
        """Comprehensive schema compliance test."""
        try:
            df = load_predictions(file_path)
            
            # Run all individual checks
            self.test_required_columns_exist(baseline_name, file_path, schema)
            self.test_column_data_types(baseline_name, file_path, schema)
            self.test_anomaly_flag_values(baseline_name, file_path, schema)
            self.test_no_missing_critical_values(baseline_name, file_path, schema)
            self.test_anomaly_score_range(baseline_name, file_path, schema)
            
            assert True, f"{baseline_name} predictions fully comply with schema"
        except FileNotFoundError:
            pytest.skip(f"File not found: {file_path}. Run baseline scripts first.")
        except AssertionError as e:
            pytest.fail(f"{baseline_name} schema compliance failed: {str(e)}")