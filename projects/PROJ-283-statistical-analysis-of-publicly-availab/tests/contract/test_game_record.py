"""
Contract test for GameRecord schema validation.
Ensures that the GameRecord DataFrame matches the schema defined in specs/contracts/game_record.schema.yaml
"""
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import yaml

from src.validation.validate_contracts import (
    SchemaValidationError,
    validate_dataframe_against_contract,
    load_schema,
)

@pytest.fixture
def game_record_schema():
    """Load the GameRecord schema."""
    schema_path = Path("specs/contracts/game_record.schema.yaml")
    if not schema_path.exists():
        pytest.skip("GameRecord schema not yet created (T006)")
    return load_schema(schema_path)

@pytest.fixture
def valid_game_record_df(game_record_schema):
    """Create a valid GameRecord DataFrame based on schema requirements."""
    required_cols = game_record_schema.get("required_columns", [])
    
    # Create dummy data for each required column
    data = {}
    for col in required_cols:
        if col == "game_id":
            data[col] = ["game_001", "game_002", "game_003"]
        elif col == "white_rating":
            data[col] = [1500, 1600, 1700]
        elif col == "black_rating":
            data[col] = [1450, 1550, 1650]
        elif col == "eco_code":
            data[col] = ["B01", "C50", "E00"]
        elif col == "avg_move_time_white":
            data[col] = [15.5, 12.3, 18.7]
        elif col == "avg_move_time_black":
            data[col] = [14.2, 13.1, 16.5]
        elif col == "material_imbalance_move5":
            data[col] = [0.0, 1.0, -0.5]
        elif col == "outcome":
            data[col] = [1, 0, 0.5]
        elif col == "elo_expected_prob":
            data[col] = [0.57, 0.51, 0.49]
        elif col == "outcome_deviation":
            data[col] = [0.43, -0.51, 0.01]
        else:
            data[col] = [None, None, None]
    
    return pd.DataFrame(data)

def test_game_record_schema_exists(game_record_schema):
    """Verify that the GameRecord schema is defined."""
    assert game_record_schema is not None
    assert "required_columns" in game_record_schema
    assert len(game_record_schema["required_columns"]) > 0

def test_game_record_validation_passes(valid_game_record_df, game_record_schema):
    """Verify that a valid GameRecord DataFrame passes schema validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "game_record.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(game_record_schema, f)
        
        # This should not raise an exception
        result = validate_dataframe_against_contract(valid_game_record_df, schema_path)
        assert result is True

def test_game_record_validation_fails_with_missing_columns(valid_game_record_df, game_record_schema):
    """Verify that validation fails when required columns are missing."""
    # Remove a required column
    missing_col = game_record_schema["required_columns"][0]
    invalid_df = valid_game_record_df.drop(columns=[missing_col])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "game_record.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(game_record_schema, f)
        
        with pytest.raises(SchemaValidationError):
            validate_dataframe_against_contract(invalid_df, schema_path)

def test_game_record_validation_fails_with_nulls(valid_game_record_df, game_record_schema):
    """Verify that validation fails when required columns contain nulls."""
    # Introduce a null in a required column
    required_cols = game_record_schema["required_columns"]
    test_col = required_cols[0]
    invalid_df = valid_game_record_df.copy()
    invalid_df.loc[0, test_col] = None
    
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "game_record.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(game_record_schema, f)
        
        with pytest.raises(SchemaValidationError):
            validate_dataframe_against_contract(invalid_df, schema_path)

def test_game_record_validation_fails_with_wrong_types(valid_game_record_df, game_record_schema):
    """Verify that validation fails when column types are incorrect."""
    col_types = game_record_schema.get("column_types", {})
    
    if not col_types:
        pytest.skip("No column type constraints defined in schema")
    
    # Pick a column with a type constraint and change its type
    test_col = list(col_types.keys())[0]
    if test_col not in valid_game_record_df.columns:
        pytest.skip(f"Column {test_col} not in test DataFrame")
    
    invalid_df = valid_game_record_df.copy()
    # Convert to a wrong type (e.g., int to string)
    invalid_df[test_col] = invalid_df[test_col].astype(str)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        schema_path = Path(tmpdir) / "game_record.schema.yaml"
        with open(schema_path, 'w') as f:
            yaml.dump(game_record_schema, f)
        
        with pytest.raises(SchemaValidationError):
            validate_dataframe_against_contract(invalid_df, schema_path)
