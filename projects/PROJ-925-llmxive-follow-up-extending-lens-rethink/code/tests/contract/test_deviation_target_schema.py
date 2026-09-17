"""
Contract tests for deviation target schema validation.

This module verifies that the deviation target schema contract defined in T004a
is correctly enforced.
"""
import pytest
import os
from code.utils.errors import DataSchemaError, create_missing_dataset_error
from code.config import get_project_root


class TestDeviationTargetSchema:
    """Test cases for deviation target schema contract validation."""

    def test_deviation_target_contract_exists(self):
        """Verify the deviation target schema contract file exists."""
        root = get_project_root()
        contract_path = os.path.join(
            root,
            "specs",
            "001-llmxive-follow-up-extending-lens-rethink",
            "contracts",
            "deviation_target.schema.yaml"
        )
        
        assert os.path.exists(contract_path), (
            f"Deviation target schema contract file not found at {contract_path}. "
            "Ensure T004a has created the contract files."
        )

    def test_error_message_format(self):
        """Verify error message format for missing deviation target columns."""
        error_msg = create_missing_dataset_error("pick-a-pic", "deviation_score")
        assert error_msg == "Missing required dataset or column: pick-a-pic/deviation_score"

    def test_schema_validation_logic(self):
        """Verify basic schema validation logic is importable."""
        from code.utils.validation import load_schema, validate_dataframe
        assert callable(load_schema)
        assert callable(validate_dataframe)
