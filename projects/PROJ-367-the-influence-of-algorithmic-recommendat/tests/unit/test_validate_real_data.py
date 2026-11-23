"""
Unit tests for code/validate_real_data.py

Specifically tests the schema validation logic (FR-007) using a mock file
that is missing the required columns.
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion import DataSchemaError
from validate_real_data import validate_real_dataset_schema

class TestValidateRealDataSchema:
    """Tests for the schema validation logic."""

    def test_schema_error_on_missing_columns(self):
        """
        Test that DataSchemaError is raised with the exact message when
        required columns are missing.
        """
        # Create a temporary CSV with missing columns
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            mock_file = tmp_path / "mock_missing_columns.csv"

            # Create a dataframe with WRONG columns
            df = pd.DataFrame({
                "user_id": [1, 2, 3],
                "wrong_column_1": ["A", "B", "C"],
                "wrong_column_2": ["X", "Y", "Z"]
            })
            df.to_csv(mock_file, index=False)

            # Temporarily override the config path logic by patching the function
            # or by creating a test that mimics the logic directly.
            # Since validate_real_dataset_schema relies on ProjectConfig,
            # we will test the logic by directly invoking the validation
            # on a dataframe-like scenario or by mocking the config.
            # However, the task asks to verify the script behavior.
            # Let's test the core logic: check_columns.

            # We will mock the config to point to our temp file
            # But since validate_real_dataset_schema is tightly coupled to config,
            # let's verify the error message format by importing the error class
            # and ensuring the logic matches the requirement.

            # To strictly test the script's behavior as requested:
            # We will patch the ProjectConfig to return our temp path.
            from unittest.mock import patch
            from config import ProjectConfig

            original_init = ProjectConfig.__init__

            def mock_init(self, *args, **kwargs):
                # Call original to setup attributes
                # But we need to ensure data_raw_dir is our temp dir
                # We can't easily override just one attr without full init
                # Let's use a simpler approach: test the validation logic directly
                pass

            # Actually, the cleanest way to test this specific requirement
            # is to verify the error message string construction.
            # The requirement is: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."

            # Let's create a test that simulates the missing columns check
            required = {"recommended_categories", "enrolled_categories"}
            available = {"user_id", "wrong_col"}
            missing = required - available

            expected_msg = (
                f"Required columns {sorted(missing)} missing. "
                "Dataset does not support the specified experimental design."
            )

            # Verify the message format matches the requirement
            assert "Required columns" in expected_msg
            assert "missing" in expected_msg
            assert "Dataset does not support" in expected_msg
            assert "recommended_categories" in expected_msg
            assert "enrolled_categories" in expected_msg

            # Now, let's test the actual function with a mock config
            # We need to make sure the function raises DataSchemaError
            with patch('validate_real_data.ProjectConfig') as MockConfig:
                mock_instance = MockConfig.return_value
                mock_instance.data_raw_dir = tmp_path

                with pytest.raises(DataSchemaError) as exc_info:
                    validate_real_dataset_schema()

                assert str(exc_info.value) == expected_msg

    def test_schema_pass_on_valid_columns(self):
        """
        Test that validation passes when required columns are present.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            mock_file = tmp_path / "valid_mock.csv"

            df = pd.DataFrame({
                "user_id": [1, 2],
                "recommended_categories": [["A"], ["B"]],
                "enrolled_categories": [["C"], ["D"]]
            })
            df.to_csv(mock_file, index=False)

            from unittest.mock import patch
            from config import ProjectConfig

            with patch('validate_real_data.ProjectConfig') as MockConfig:
                mock_instance = MockConfig.return_value
                mock_instance.data_raw_dir = tmp_path

                # Should not raise
                result = validate_real_dataset_schema()
                assert result is True