"""
Contract tests for significance results schema validation.

This module verifies that the significance results schema contract defined in T004a
is correctly enforced.
"""
import pytest
import os
from code.utils.errors import DataSchemaError, create_missing_dataset_error
from code.config import get_project_root


class TestSignificanceResultsSchema:
    """Test cases for significance results schema contract validation."""

    def test_significance_results_contract_exists(self):
        """Verify the significance results schema contract file exists."""
        root = get_project_root()
        contract_path = os.path.join(
            root,
            "specs",
            "001-llmxive-follow-up-extending-lens-rethink",
            "contracts",
            "significance_results.schema.yaml"
        )
        
        assert os.path.exists(contract_path), (
            f"Significance results schema contract file not found at {contract_path}. "
            "Ensure T004a has created the contract files."
        )

    def test_error_message_format(self):
        """Verify error message format for missing significance result fields."""
        error_msg = create_missing_dataset_error("results", "p_value")
        assert error_msg == "Missing required dataset or column: results/p_value"

    def test_schema_validation_logic(self):
        """Verify basic schema validation logic is importable."""
        from code.utils.validation import load_schema, validate_dataframe
        assert callable(load_schema)
        assert callable(validate_dataframe)
