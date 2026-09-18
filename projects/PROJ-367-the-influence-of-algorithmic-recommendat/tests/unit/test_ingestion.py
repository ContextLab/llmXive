import pytest
import pandas as pd
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import DataSchemaError, validate_schema

class TestSchemaValidation:
    """
    Tests for the schema validation logic in code/ingestion.py.
    Specifically verifies T004b requirements.
    """

    def test_validate_schema_missing_columns_raises_data_schema_error(self):
        """
        T004b Verification:
        Write a unit test that triggers this exception and asserts the exact message.
        Expected Message: "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
        """
        # Create a DataFrame missing the required columns
        df_missing = pd.DataFrame({
            'user_id': [1, 2, 3],
            'session_id': ['A', 'B', 'C']
            # Note: 'recommended_categories' and 'enrolled_categories' are missing
        })

        # Assert that the specific exception is raised
        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df_missing)

        # Assert the exact error message
        expected_message = "Required columns [recommended_categories, enrolled_categories] missing. Dataset does not support the specified experimental design."
        assert str(exc_info.value) == expected_message, f"Expected message:\n{expected_message}\n\nGot:\n{str(exc_info.value)}"

    def test_validate_schema_partial_missing_columns(self):
        """
        Test that if only one column is missing, it is correctly identified in the error message.
        """
        df_partial = pd.DataFrame({
            'user_id': [1, 2, 3],
            'recommended_categories': [['Math'], ['Sci']]
            # 'enrolled_categories' is missing
        })

        with pytest.raises(DataSchemaError) as exc_info:
            validate_schema(df_partial)

        # The list should contain only the missing column
        assert "enrolled_categories" in str(exc_info.value)
        assert "recommended_categories" not in str(exc_info.value) # Should not list present ones

    def test_validate_schema_all_columns_present(self):
        """
        Test that validation passes when all required columns are present.
        """
        df_valid = pd.DataFrame({
            'user_id': [1, 2, 3],
            'recommended_categories': [['Math'], ['Sci'], ['Art']],
            'enrolled_categories': [['Math'], ['Sci'], ['Art']]
        })

        # Should not raise any exception
        try:
            validate_schema(df_valid)
        except DataSchemaError:
            pytest.fail("validate_schema raised DataSchemaError unexpectedly for valid schema.")