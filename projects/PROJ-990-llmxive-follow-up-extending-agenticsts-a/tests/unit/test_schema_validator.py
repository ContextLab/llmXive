import pytest
import pandas as pd
import json
import os
from pathlib import Path
import tempfile
import shutil

from schema_validator import (
    validate_dataframe_schema,
    SCHEMAS,
    Schema,
    SchemaField,
    validate_schema_file,
    validate_all_processed_files
)

@pytest.fixture
def sample_df_utility_labels():
    return pd.DataFrame({
        "layer_id": [1, 2, 3],
        "utility_score": [0.8, 0.5, 0.9],
        "turn_id": [10, 11, 12],
        "entropy": [1.2, 1.5, 1.1]
    })

@pytest.fixture
def sample_df_missing_column():
    return pd.DataFrame({
        "layer_id": [1, 2, 3],
        "utility_score": [0.8, 0.5, 0.9],
        "turn_id": [10, 11, 12]
        # Missing 'entropy'
    })

@pytest.fixture
def sample_df_wrong_dtype():
    return pd.DataFrame({
        "layer_id": ["a", "b", "c"],  # Should be int64
        "utility_score": [0.8, 0.5, 0.9],
        "turn_id": [10, 11, 12],
        "entropy": [1.2, 1.5, 1.1]
    })

@pytest.fixture
def sample_df_with_nulls():
    return pd.DataFrame({
        "layer_id": [1, 2, 3],
        "utility_score": [0.8, 0.5, None],  # utility_score is not nullable
        "turn_id": [10, 11, 12],
        "entropy": [1.2, 1.5, 1.1]
    })

class TestValidateDataFrameSchema:
    def test_valid_schema(self, sample_df_utility_labels):
        schema = SCHEMAS["utility_labels"]
        result = validate_dataframe_schema(sample_df_utility_labels, schema, "test.csv")
        assert result is True

    def test_missing_columns(self, sample_df_missing_column):
        schema = SCHEMAS["utility_labels"]
        result = validate_dataframe_schema(sample_df_missing_column, schema, "test.csv")
        assert result is False

    def test_wrong_dtype(self, sample_df_wrong_dtype):
        schema = SCHEMAS["utility_labels"]
        result = validate_dataframe_schema(sample_df_wrong_dtype, schema, "test.csv")
        assert result is False

    def test_non_nullable_nulls(self, sample_df_with_nulls):
        schema = SCHEMAS["utility_labels"]
        result = validate_dataframe_schema(sample_df_with_nulls, schema, "test.csv")
        assert result is False

class TestValidateSchemaFile:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_valid_csv_file(self, sample_df_utility_labels):
        # Create a valid CSV file
        file_path = Path(self.temp_dir) / "test.csv"
        sample_df_utility_labels.to_csv(file_path, index=False)
        
        result = validate_schema_file(file_path, "utility_labels")
        assert result is True

    def test_invalid_csv_file(self, sample_df_missing_column):
        # Create an invalid CSV file
        file_path = Path(self.temp_dir) / "test.csv"
        sample_df_missing_column.to_csv(file_path, index=False)
        
        result = validate_schema_file(file_path, "utility_labels")
        assert result is False

    def test_nonexistent_file(self):
        file_path = Path(self.temp_dir) / "nonexistent.csv"
        
        result = validate_schema_file(file_path, "utility_labels")
        assert result is False

    def test_unknown_schema(self, sample_df_utility_labels):
        file_path = Path(self.temp_dir) / "test.csv"
        sample_df_utility_labels.to_csv(file_path, index=False)
        
        result = validate_schema_file(file_path, "unknown_schema")
        assert result is False

    def test_valid_json_file(self):
        # Create a valid JSON file
        file_path = Path(self.temp_dir) / "test.json"
        data = [
            {"layer_id": 1, "utility_score": 0.8, "turn_id": 10, "entropy": 1.2},
            {"layer_id": 2, "utility_score": 0.5, "turn_id": 11, "entropy": 1.5}
        ]
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = validate_schema_file(file_path, "utility_labels")
        assert result is True

class TestValidateAllProcessedFiles:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create data/processed directory
        Path("data/processed").mkdir(parents=True)

    def teardown_method(self):
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def test_empty_directory(self):
        result = validate_all_processed_files()
        # Should pass since no files exist yet (expected in early pipeline)
        assert result is True

    def test_with_valid_file(self):
        # Create a valid file
        file_path = Path("data/processed/utility_labels.csv")
        df = pd.DataFrame({
            "layer_id": [1, 2],
            "utility_score": [0.8, 0.5],
            "turn_id": [10, 11],
            "entropy": [1.2, 1.5]
        })
        df.to_csv(file_path, index=False)
        
        result = validate_all_processed_files()
        assert result is True

    def test_with_invalid_file(self):
        # Create an invalid file (missing columns)
        file_path = Path("data/processed/utility_labels.csv")
        df = pd.DataFrame({
            "layer_id": [1, 2],
            "utility_score": [0.8, 0.5],
            "turn_id": [10, 11]
            # Missing 'entropy'
        })
        df.to_csv(file_path, index=False)
        
        result = validate_all_processed_files()
        assert result is False
