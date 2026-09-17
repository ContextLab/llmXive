"""
Contract tests for dataset schema validation.

This module verifies that the dataset schema contract defined in T004a
is correctly enforced, specifically checking for the presence of required
datasets and columns (e.g., 'pick-a-pic/human_rating').
"""
import pytest
from code.utils.errors import DataSchemaError, create_missing_dataset_error


class TestDatasetSchema:
    """Test cases for dataset schema contract validation."""

    def test_create_missing_dataset_error_format(self):
        """Verify the error message format matches the contract specification."""
        source = "pick-a-pic"
        column = "human_rating"
        error_msg = create_missing_dataset_error(source, column)
        
        expected_pattern = f"Missing required dataset or column: {source}/{column}"
        assert error_msg == expected_pattern, (
            f"Error message '{error_msg}' does not match expected pattern '{expected_pattern}'"
        )

    def test_create_missing_dataset_error_specific_case(self):
        """Verify the specific error message for pick-a-pic/human_rating."""
        error_msg = create_missing_dataset_error("pick-a-pic", "human_rating")
        assert error_msg == "Missing required dataset or column: pick-a-pic/human_rating"

    def test_data_schema_error_inheritance(self):
        """Verify DataSchemaError is a proper exception type."""
        assert issubclass(DataSchemaError, Exception)

    def test_data_schema_error_raising(self):
        """Verify DataSchemaError can be raised and caught."""
        with pytest.raises(DataSchemaError) as exc_info:
            raise create_missing_dataset_error("test-source", "test-column")
        
        assert "Missing required dataset or column: test-source/test-column" in str(exc_info.value)

    def test_schema_contract_exists(self):
        """Verify the dataset schema contract file exists."""
        import os
        from code.config import get_project_root
        
        root = get_project_root()
        contract_path = os.path.join(
            root,
            "specs",
            "001-llmxive-follow-up-extending-lens-rethink",
            "contracts",
            "dataset.schema.yaml"
        )
        
        assert os.path.exists(contract_path), (
            f"Dataset schema contract file not found at {contract_path}. "
            "Ensure T004a has created the contract files."
        )
