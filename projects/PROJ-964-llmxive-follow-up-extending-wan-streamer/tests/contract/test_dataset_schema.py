"""
Contract test for dataset schema (US1).

Verifies that the processed dataset produced by the data extraction pipeline
adheres to the strict schema requirements defined in the specification.

Required columns:
- timestamp: float64
- semantic_feature: float64 (or object/list depending on storage, but validated as non-null)
- prosodic_feature: float64
- latent_delta_magnitude: float64
- turn_label: string (categorical: 'interruption', 'pause', 'normal')

Constraints:
- File size <= 1 GB
- At least 10,000 sampled frames
- No null values in required columns
- Valid event types for turn_label
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to allow imports if needed, though this is a pure contract test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import validators from the existing API surface
from utils.validators import ValidationError, validate_dataset_schema

# Define the expected schema based on T013/T014 requirements
EXPECTED_SCHEMA = {
    "columns": {
        "timestamp": {"dtype": "float64", "nullable": False},
        "semantic_feature": {"dtype": "float64", "nullable": False},
        "prosodic_feature": {"dtype": "float64", "nullable": False},
        "latent_delta_magnitude": {"dtype": "float64", "nullable": False},
        "turn_label": {"dtype": "string", "nullable": False, "allowed_values": ["interruption", "pause", "normal"]}
    },
    "min_rows": 10000,
    "max_size_mb": 1024
}

# Path to the expected output file from the preprocessing pipeline
# This path matches the convention in tasks.md (data/processed/)
# The test expects the file to exist after T014 runs.
# We use a relative path from the project root context if running from tests,
# but typically the test is run against the generated artifact.
ARTIFACT_PATH = Path(__file__).parent.parent.parent / "data" / "processed" / "processed_latents.parquet"

# Fallback for testing environment where file might be generated in a temp location or specific run
# If the standard path doesn't exist, we check for a generic "processed" parquet in data/processed
def find_processed_dataset():
    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / "data" / "processed"
    
    if processed_dir.exists():
        # Look for the specific expected file first
        target = processed_dir / "processed_latents.parquet"
        if target.exists():
            return target
        
        # Fallback: find any parquet file in that directory
        parquet_files = list(processed_dir.glob("*.parquet"))
        if parquet_files:
            # Sort by modification time to get the latest one if multiple exist
            return sorted(parquet_files, key=os.path.getmtime)[-1]
    
    return None

def load_dataset():
    path = find_processed_dataset()
    if path is None:
        raise FileNotFoundError(
            "Processed dataset not found. "
            "Ensure T014 (preprocess.py) has been executed and output "
            "data/processed/processed_latents.parquet exists."
        )
    
    return pd.read_parquet(path), path

class TestDatasetSchemaContract:
    
    def test_file_exists_and_size_constraint(self):
        """Test that the file exists and is within the 1 GB limit."""
        df, path = load_dataset()
        file_size_mb = path.stat().st_size / (1024 * 1024)
        
        assert file_size_mb <= EXPECTED_SCHEMA["max_size_mb"], (
            f"Dataset size {file_size_mb:.2f} MB exceeds limit of "
            f"{EXPECTED_SCHEMA['max_size_mb']} MB."
        )
        
    def test_minimum_row_count(self):
        """Test that the dataset has at least 10,000 sampled frames."""
        df, _ = load_dataset()
        
        assert len(df) >= EXPECTED_SCHEMA["min_rows"], (
            f"Dataset has {len(df)} rows, which is less than the "
            f"required minimum of {EXPECTED_SCHEMA['min_rows']}."
        )
        
    def test_required_columns_present(self):
        """Test that all required columns exist in the dataframe."""
        df, _ = load_dataset()
        required_cols = EXPECTED_SCHEMA["columns"].keys()
        
        missing_cols = set(required_cols) - set(df.columns)
        assert not missing_cols, f"Missing required columns: {missing_cols}"
        
    def test_schema_validation(self):
        """
        Test that the dataframe adheres to the strict schema definition
        using the project's validator utility.
        """
        df, _ = load_dataset()
        
        try:
            validate_dataset_schema(df, EXPECTED_SCHEMA)
        except ValidationError as e:
            pytest.fail(f"Dataset schema validation failed: {e}")
            
    def test_turn_label_distribution(self):
        """
        Test that turn_label contains valid values and has a distribution
        that suggests stratified sampling was applied (non-trivial counts for all classes).
        """
        df, _ = load_dataset()
        
        allowed = EXPECTED_SCHEMA["columns"]["turn_label"]["allowed_values"]
        actual_labels = set(df["turn_label"].unique())
        
        invalid_labels = actual_labels - set(allowed)
        assert not invalid_labels, f"Found invalid turn_label values: {invalid_labels}"
        
        # Check that all expected labels are present (stratification check)
        for label in allowed:
            count = (df["turn_label"] == label).sum()
            assert count > 0, f"Turn label '{label}' is missing from the dataset."
            
    def test_no_nulls_in_required_fields(self):
        """Test that no required column contains null values."""
        df, _ = load_dataset()
        
        for col_name, constraints in EXPECTED_SCHEMA["columns"].items():
            if not constraints["nullable"]:
                null_count = df[col_name].isnull().sum()
                assert null_count == 0, (
                    f"Column '{col_name}' contains {null_count} null values, "
                    "but it is marked as non-nullable."
                )
                
    def test_numeric_columns_are_numeric(self):
        """Test that numeric columns are actually numeric types."""
        df, _ = load_dataset()
        
        numeric_cols = [
            "timestamp", "semantic_feature", "prosodic_feature", "latent_delta_magnitude"
        ]
        
        for col in numeric_cols:
            if not np.issubdtype(df[col].dtype, np.number):
                pytest.fail(f"Column '{col}' is not numeric. Found dtype: {df[col].dtype}")
