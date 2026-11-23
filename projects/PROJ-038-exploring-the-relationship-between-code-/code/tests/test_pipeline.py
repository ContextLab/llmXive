import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the validation logic from the ingest module as per API surface
from src.ingest import validate_features

class TestPipelineShape:
    """
    Integration test for T012a: test_pipeline_shape.
    Verifies that the pipeline produces a features.csv with the correct shape and content
    as defined in User Story 1 (T017, T018).
    """

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory structure mimicking the project data layout."""
        temp_root = tempfile.mkdtemp()
        processed_dir = os.path.join(temp_root, "data", "processed")
        os.makedirs(processed_dir, exist_ok=True)
        yield temp_root
        shutil.rmtree(temp_root)

    @pytest.fixture
    def valid_features_csv(self, temp_data_dir):
        """Generate a valid features.csv file that meets T017/T018 requirements."""
        csv_path = os.path.join(temp_data_dir, "data", "processed", "features.csv")
        
        # Create a dataframe with the exact schema required:
        # file_path, cc, halstead, loc, is_buggy
        # Ensuring no NaN values in numeric columns (T018 requirement)
        data = {
            "file_path": [
                "/project/src/Main.java",
                "/project/src/Utils.java",
                "/project/src/Helper.java",
                "/project/src/BuggyClass.java"
            ],
            "cc": [5, 12, 3, 25],  # Cyclomatic Complexity (int)
            "halstead": [100.5, 450.2, 30.1, 890.0],  # Halstead Volume (float)
            "loc": [150, 400, 50, 900],  # Lines of Code (int)
            "is_buggy": [0, 0, 0, 1]  # Binary label (int)
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def invalid_nan_csv(self, temp_data_dir):
        """Generate a features.csv with NaN values to test T018 validation logic."""
        csv_path = os.path.join(temp_data_dir, "data", "processed", "features.csv")
        data = {
            "file_path": ["/project/src/Bad.java"],
            "cc": [5],
            "halstead": [float('nan')],  # Invalid NaN
            "loc": [100],
            "is_buggy": [0]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def invalid_schema_csv(self, temp_data_dir):
        """Generate a features.csv missing required columns."""
        csv_path = os.path.join(temp_data_dir, "data", "processed", "features.csv")
        data = {
            "file_path": ["/project/src/Incomplete.java"],
            "cc": [5],
            # Missing halstead, loc, is_buggy
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        return csv_path

    def test_pipeline_shape_correct_schema(self, valid_features_csv, temp_data_dir):
        """
        Verify that features.csv has the correct columns and no NaNs in metric columns.
        This validates the output of T017 and T018.
        """
        # Run the validation logic
        # Note: validate_features expects a path to the CSV
        # We mock the log file path to avoid permission issues in temp dirs
        with patch('src.ingest.LOGGER'):
            result_df = validate_features(valid_features_csv)
        
        # Assert shape
        assert result_df is not None, "Validation should return the dataframe"
        assert len(result_df) == 4, "Should have 4 rows (no rows dropped as no NaNs)"
        assert len(result_df.columns) == 5, "Should have 5 columns"
        
        # Assert column names
        expected_cols = ["file_path", "cc", "halstead", "loc", "is_buggy"]
        assert list(result_df.columns) == expected_cols, f"Columns mismatch: {list(result_df.columns)}"

    def test_pipeline_shape_drops_nan_rows(self, invalid_nan_csv, temp_data_dir):
        """
        Verify that rows with NaN in metric columns are dropped (T018 logic).
        """
        with patch('src.ingest.LOGGER'):
            result_df = validate_features(invalid_nan_csv)
        
        # The row with NaN should be dropped
        assert result_df is not None
        assert len(result_df) == 0, "Row with NaN should be dropped, resulting in empty dataframe"

    def test_pipeline_shape_raises_on_empty(self, invalid_nan_csv, temp_data_dir):
        """
        Verify that if validation results in an empty dataset, a DataIntegrityError is raised (T018).
        """
        from src.ingest import DataIntegrityError
        
        with patch('src.ingest.LOGGER'):
            with pytest.raises(DataIntegrityError, match="resulting dataset is empty"):
                validate_features(invalid_nan_csv)

    def test_pipeline_shape_validates_schema(self, invalid_schema_csv, temp_data_dir):
        """
        Verify that missing columns trigger a validation error.
        """
        from src.ingest import DataIntegrityError
        
        with patch('src.ingest.LOGGER'):
            with pytest.raises((DataIntegrityError, ValueError), match="missing required columns"):
                validate_features(invalid_schema_csv)

    def test_pipeline_shape_content_values(self, valid_features_csv, temp_data_dir):
        """
        Verify that the content values are of the correct type and range.
        """
        with patch('src.ingest.LOGGER'):
            result_df = validate_features(valid_features_csv)
        
        # Check types
        assert result_df['cc'].dtype in [int, 'int64', 'int32'], "cc should be integer"
        assert result_df['halstead'].dtype in [float, 'float64', 'float32'], "halstead should be float"
        assert result_df['loc'].dtype in [int, 'int64', 'int32'], "loc should be integer"
        assert result_df['is_buggy'].dtype in [int, 'int64', 'int32', bool], "is_buggy should be binary"
        
        # Check range of is_buggy
        assert result_df['is_buggy'].isin([0, 1]).all(), "is_buggy must be 0 or 1"

    def test_pipeline_shape_integration_with_mocked_ingest(self, valid_features_csv, temp_data_dir):
        """
        Integration test simulating the full pipeline flow:
        1. Ingest generates raw data (mocked)
        2. Metrics calculated (mocked)
        3. Labeling applied (mocked)
        4. Validation runs (actual)
        5. Final shape verified.
        """
        # We assume the file exists as created by the fixture.
        # In a real CI run, this would be the output of T017.
        # Here we verify that T018 (validate_features) correctly processes the T017 output.
        
        expected_path = valid_features_csv
        assert os.path.exists(expected_path), "Input CSV must exist for integration test"
        
        with patch('src.ingest.LOGGER'):
            final_df = validate_features(expected_path)
        
        # Final assertion on the "Pipeline Shape"
        assert final_df.shape[0] > 0, "Pipeline must produce at least one valid row"
        assert final_df.shape[1] == 5, "Pipeline must produce exactly 5 columns"
        assert 'is_buggy' in final_df.columns, "Pipeline must include the bug label"