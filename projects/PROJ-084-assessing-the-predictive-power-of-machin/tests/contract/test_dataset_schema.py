"""
Contract test for the dataset schema validation.
Ensures that the processed dataset adheres to the defined schema in
specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import yaml

# Import the validator from the project utilities
from utils.schema_validator import (
    load_schema,
    validate_column_schema,
    validate_fingerprint_dimensions,
    validate_record_content,
    validate_dataset
)

SCHEMA_PATH = Path("specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml")
SAMPLE_DATA_PATH = Path("data/processed/cleaned_reactions.parquet")


@pytest.fixture
def schema():
    """Load the dataset schema."""
    return load_schema(SCHEMA_PATH)


@pytest.fixture
def sample_df():
    """Create a minimal valid dataframe for testing schema validation."""
    # This is a synthetic sample ONLY for schema validation testing.
    # It does not represent real data but validates the schema structure.
    data = {
        "reaction_id": ["R001", "R002"],
        "reactants_smiles": ["CCO", "CC(=O)O"],
        "reagents_smiles": ["H2O", None],
        "product_smiles": ["CCO", "CC(=O)O"],
        "reaction_class": ["Addition", "Substitution"],
        "yield_percent": [85.5, 72.0],
        "ecfp4_fingerprint": [
            np.zeros(2048, dtype=np.uint8),
            np.zeros(2048, dtype=np.uint8)
        ],
        "maccs_fingerprint": [
            np.zeros(167, dtype=np.uint8),
            np.zeros(167, dtype=np.uint8)
        ],
        "scaffold_id": ["S1", "S2"],
        "split_group": ["train", "val"]
    }
    return pd.DataFrame(data)


def test_schema_loads(schema):
    """Test that the schema file loads correctly."""
    assert schema is not None
    assert "columns" in schema
    assert "schema_version" in schema


def test_validate_column_schema(schema, sample_df):
    """Test that column names and types match the schema."""
    # This should pass if the sample_df matches the schema
    result = validate_column_schema(sample_df, schema)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_fingerprint_dimensions(schema, sample_df):
    """Test that fingerprint dimensions are correct."""
    result = validate_fingerprint_dimensions(sample_df, schema)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_validate_record_content(schema, sample_df):
    """Test that record content (e.g., allowed values) is valid."""
    result = validate_record_content(sample_df, schema)
    assert result["valid"] is True
    assert len(result["errors"]) == 0


def test_full_dataset_validation(schema, sample_df):
    """Test the full validation pipeline on a sample dataset."""
    result = validate_dataset(sample_df, schema)
    assert result["valid"] is True
    assert result["total_records"] == 2
    assert len(result["errors"]) == 0


def test_validation_fails_on_missing_column(schema, sample_df):
    """Test that validation fails when a required column is missing."""
    df_missing = sample_df.drop(columns=["reaction_id"])
    result = validate_dataset(df_missing, schema)
    assert result["valid"] is False
    assert any("reaction_id" in err for err in result["errors"])


def test_validation_fails_on_wrong_fingerprint_size(schema, sample_df):
    """Test that validation fails when fingerprint size is incorrect."""
    # Modify ECFP4 to wrong size
    df_wrong = sample_df.copy()
    df_wrong["ecfp4_fingerprint"] = [np.zeros(1000) for _ in range(2)]
    result = validate_dataset(df_wrong, schema)
    assert result["valid"] is False
    assert any("ecfp4" in err.lower() for err in result["errors"])


def test_validation_fails_on_invalid_class(schema, sample_df):
    """Test that validation fails on invalid reaction class."""
    df_wrong = sample_df.copy()
    df_wrong.loc[0, "reaction_class"] = "InvalidClass"
    result = validate_dataset(df_wrong, schema)
    assert result["valid"] is False
    assert any("reaction_class" in err for err in result["errors"])


@pytest.mark.skipif(not SAMPLE_DATA_PATH.exists(), reason="Real data not available")
def test_real_data_validation(schema):
    """
    Test validation against the real processed dataset if it exists.
    This test is skipped if the real data file is not present.
    """
    df = pd.read_parquet(SAMPLE_DATA_PATH)
    result = validate_dataset(df, schema)
    assert result["valid"] is True, f"Real data failed schema validation: {result['errors']}"
    assert len(result["errors"]) == 0