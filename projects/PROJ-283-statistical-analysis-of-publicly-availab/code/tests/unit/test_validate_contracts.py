"""
Unit tests for the contract validation module.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path

from src.validation.validate_contracts import (
    SchemaValidationError,
    load_schema,
    validate_column_exists,
    validate_column_type,
    validate_no_nulls,
    validate_column_range,
    validate_schema,
    validate_dataframe_against_contract,
    validate_all_contracts
)


@pytest.fixture
def sample_schema():
    return {
        "name": "test_schema",
        "columns": [
            {"name": "id", "type": "int", "nullable": False},
            {"name": "name", "type": "str", "nullable": False},
            {"name": "score", "type": "float", "nullable": True, "min": 0.0, "max": 100.0}
        ]
    }


@pytest.fixture
def valid_df():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [95.5, 88.0, 72.3]
    })


@pytest.fixture
def invalid_df_nulls():
    return pd.DataFrame({
        "id": [1, 2, None],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [95.5, 88.0, 72.3]
    })


@pytest.fixture
def invalid_df_missing_col():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"]
    })


@pytest.fixture
def invalid_df_wrong_type():
    return pd.DataFrame({
        "id": ["1", "2", "3"],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [95.5, 88.0, 72.3]
    })


@pytest.fixture
def invalid_df_range():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "score": [95.5, 150.0, 72.3]
    })


def test_validate_column_exists_valid(valid_df, sample_schema):
    validate_column_exists(valid_df, "id", "test_schema")
    validate_column_exists(valid_df, "name", "test_schema")


def test_validate_column_exists_missing(invalid_df_missing_col):
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_column_exists(invalid_df_missing_col, "score", "test_schema")
    assert "score" in str(exc_info.value)


def test_validate_column_type_valid(valid_df, sample_schema):
    validate_column_type(valid_df, "id", "int", "test_schema")
    validate_column_type(valid_df, "name", "str", "test_schema")


def test_validate_column_type_invalid(invalid_df_wrong_type):
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_column_type(invalid_df_wrong_type, "id", "int", "test_schema")
    assert "int" in str(exc_info.value)


def test_validate_no_nulls_valid(valid_df):
    validate_no_nulls(valid_df, "id", "test_schema")


def test_validate_no_nulls_invalid(invalid_df_nulls):
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_no_nulls(invalid_df_nulls, "id", "test_schema")
    assert "null" in str(exc_info.value).lower()


def test_validate_column_range_valid(valid_df):
    validate_column_range(valid_df, "score", min_val=0.0, max_val=100.0, schema_name="test_schema")


def test_validate_column_range_invalid(invalid_df_range):
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_column_range(invalid_df_range, "score", min_val=0.0, max_val=100.0, schema_name="test_schema")
    assert "100.0" in str(exc_info.value)


def test_validate_schema_valid(valid_df, sample_schema):
    validate_schema(valid_df, sample_schema)


def test_validate_schema_invalid_nulls(invalid_df_nulls, sample_schema):
    with pytest.raises(SchemaValidationError):
        validate_schema(invalid_df_nulls, sample_schema)


def test_validate_schema_invalid_missing_col(invalid_df_missing_col, sample_schema):
    with pytest.raises(SchemaValidationError):
        validate_schema(invalid_df_missing_col, sample_schema)


def test_validate_dataframe_against_contract_valid(valid_df, tmp_path):
    # Create a temporary schema file
    schema_content = """
    name: test_contract
    columns:
      - name: id
        type: int
        nullable: false
      - name: name
        type: str
        nullable: false
    """
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    schema_file = contracts_dir / "test_contract.yaml"
    schema_file.write_text(schema_content)

    validate_dataframe_against_contract(valid_df, "test_contract", str(contracts_dir))


def test_validate_all_contracts_valid(valid_df, tmp_path):
    schema_content = """
    name: test_contract_1
    columns:
      - name: id
        type: int
        nullable: false
      - name: name
        type: str
        nullable: false
    """
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    schema_file = contracts_dir / "test_contract_1.yaml"
    schema_file.write_text(schema_content)

    passed = validate_all_contracts(valid_df, str(contracts_dir))
    assert "test_contract_1" in passed