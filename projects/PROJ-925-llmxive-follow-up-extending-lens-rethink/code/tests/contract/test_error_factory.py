"""
Test scaffolding for the unified DataSchemaError factory (T004b requirement).
Verifies that the error message pattern is consistent across all validation tasks.
"""
import pytest
from code.utils.errors import DataSchemaError, create_missing_dataset_error

class TestErrorFactory:
    """Tests for the unified error message factory."""

    def test_error_message_format(self):
        """
        Verify that create_missing_dataset_error generates the exact
        required message pattern: "Missing required dataset or column: {source}/{column}"
        """
        test_cases = [
            ("pick-a-pic", "human_rating", "Missing required dataset or column: pick-a-pic/human_rating"),
            ("pick-a-pic", "clip_score", "Missing required dataset or column: pick-a-pic/clip_score"),
            ("dataset", "column", "Missing required dataset or column: dataset/column")
        ]
        
        for source, column, expected_msg in test_cases:
            error = create_missing_dataset_error(source, column)
            assert str(error) == expected_msg
            assert isinstance(error, DataSchemaError)

    def test_error_inheritance(self):
        """
        Verify that DataSchemaError is a subclass of ValueError or Exception.
        """
        error = create_missing_dataset_error("test", "test")
        assert isinstance(error, Exception)

    def test_error_uniqueness(self):
        """
        Verify that different sources/columns produce unique error messages.
        """
        error1 = create_missing_dataset_error("ds1", "col1")
        error2 = create_missing_dataset_error("ds2", "col2")
        assert str(error1) != str(error2)

    def test_error_consistency_with_contracts(self):
        """
        Verify that the error messages match the contract definitions in T004a.
        """
        # The error message must exactly match the pattern defined in the contracts
        pattern = "Missing required dataset or column: {source}/{column}"
        error = create_missing_dataset_error("pick-a-pic", "human_rating")
        assert "Missing required dataset or column: pick-a-pic/human_rating" in str(error)
        assert pattern.replace("{source}", "pick-a-pic").replace("{column}", "human_rating") == str(error)