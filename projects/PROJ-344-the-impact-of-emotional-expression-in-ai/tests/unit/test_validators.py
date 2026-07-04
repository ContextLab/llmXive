"""
Unit tests for data validation logic in code/validators.py.
"""
import pytest
import pandas as pd
import numpy as np
import yaml
import os
import tempfile

from code.validators import (
    validate_metadata_present,
    validate_modalities,
    validate_schema_compliance,
    validate_dataset,
    validate_features,
    ValidationError,
    load_schema
)
from code.config import REQUIRED_METADATA_FIELDS


@pytest.fixture
def valid_df():
    return pd.DataFrame({
        "interaction_id": ["1", "2"],
        "participant_id": ["p1", "p2"],
        "timestamp": ["2023-01-01", "2023-01-02"],
        "modality": ["facial", "vocal"],
        "source_type": ["video", "audio"]
    })


@pytest.fixture
def valid_feature_df():
    return pd.DataFrame({
        "interaction_id": ["1", "2"],
        "timestamp": ["2023-01-01", "2023-01-02"],
        "feature_name": ["pitch", "energy"],
        "value": [12.5, 45.0]
    })


@pytest.fixture
def temp_schema_file():
    schema_content = {
        "type": "object",
        "properties": {
            "interaction_id": {"type": "string", "required": True},
            "participant_id": {"type": "string", "required": True},
            "modality": {"type": "string", "required": True}
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        yield f.name
    os.unlink(f.name)


def test_validate_metadata_present_pass(valid_df):
    is_valid, missing = validate_metadata_present(valid_df, REQUIRED_METADATA_FIELDS)
    assert is_valid is True
    assert len(missing) == 0


def test_validate_metadata_present_fail(valid_df):
    # Remove a required column
    df = valid_df.drop(columns=["participant_id"])
    is_valid, missing = validate_metadata_present(df, REQUIRED_METADATA_FIELDS)
    assert is_valid is False
    assert "participant_id" in missing


def test_validate_modalities_pass(valid_df):
    is_valid, invalid = validate_modalities(valid_df)
    assert is_valid is True
    assert len(invalid) == 0


def test_validate_modalities_fail(valid_df):
    valid_df.loc[0, "modality"] = "invalid_modality"
    is_valid, invalid = validate_modalities(valid_df)
    assert is_valid is False
    assert "invalid_modality" in invalid


def test_validate_schema_compliance_pass(valid_df, temp_schema_file):
    schema = load_schema(temp_schema_file)
    is_valid, errors = validate_schema_compliance(valid_df, schema)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_schema_compliance_fail_missing_required(valid_df, temp_schema_file):
    df = valid_df.drop(columns=["interaction_id"])
    schema = load_schema(temp_schema_file)
    is_valid, errors = validate_schema_compliance(df, schema)
    assert is_valid is False
    assert any("interaction_id" in err for err in errors)


def test_validate_dataset_full_pass(valid_df, temp_schema_file):
    # Mock the global path temporarily or pass explicit path
    # Since validate_dataset uses default arg which is the global constant,
    # we need to ensure the temp file is used.
    # We will pass the explicit path to the function call in the test.
    assert validate_dataset(valid_df, schema_path=temp_schema_file) is True


def test_validate_dataset_fail_missing_metadata(valid_df, temp_schema_file):
    df = valid_df.drop(columns=["interaction_id"])
    with pytest.raises(ValidationError) as exc_info:
        validate_dataset(df, schema_path=temp_schema_file)
    assert "Missing required metadata fields" in str(exc_info.value)


def test_validate_features_pass(valid_feature_df):
    assert validate_features(valid_feature_df) is True


def test_validate_features_fail_missing_col(valid_feature_df):
    df = valid_feature_df.drop(columns=["interaction_id"])
    with pytest.raises(ValidationError) as exc_info:
        validate_features(df)
    assert "Feature data missing required columns" in str(exc_info.value)


def test_validate_features_fail_nan(valid_feature_df):
    valid_feature_df.loc[0, "value"] = np.nan
    with pytest.raises(ValidationError) as exc_info:
        validate_features(valid_feature_df)
    assert "contains NaN values" in str(exc_info.value)