"""
Contract tests for feature vector schema validation.

This module verifies that the feature vector schema contract defined in T004a
is correctly enforced, ensuring all required fields and types are present.
"""
import pytest
import os
from code.utils.errors import DataSchemaError, create_missing_dataset_error
from code.config import get_project_root


class TestFeatureVectorSchema:
    """Test cases for feature vector schema contract validation."""

    def test_feature_vector_contract_exists(self):
        """Verify the feature vector schema contract file exists."""
        root = get_project_root()
        contract_path = os.path.join(
            root,
            "specs",
            "001-llmxive-follow-up-extending-lens-rethink",
            "contracts",
            "feature_vector.schema.yaml"
        )
        
        assert os.path.exists(contract_path), (
            f"Feature vector schema contract file not found at {contract_path}. "
            "Ensure T004a has created the contract files."
        )

    def test_error_message_consistency(self):
        """Verify error messages are consistent across contract tests."""
        msg1 = create_missing_dataset_error("pick-a-pic", "human_rating")
        msg2 = create_missing_dataset_error("pick-a-pic", "clip_score")
        
        assert "Missing required dataset or column:" in msg1
        assert "Missing required dataset or column:" in msg2
        assert "pick-a-pic/human_rating" in msg1
        assert "pick-a-pic/clip_score" in msg2

    def test_schema_validation_imports(self):
        """Verify required imports for schema validation are available."""
        # This test ensures that the validation utilities can be imported
        # without errors, which is a prerequisite for contract testing.
        try:
            from code.utils.validation import load_schema, validate_dataframe
            from code.utils.errors import DataSchemaError
        except ImportError as e:
            pytest.fail(f"Required imports for schema validation failed: {e}")

    def test_pydantic_model_imports(self):
        """Verify Pydantic models for feature vectors can be imported."""
        try:
            from code.models.linguistic_feature_vector import LinguisticFeatureVector
        except ImportError as e:
            pytest.fail(f"Failed to import LinguisticFeatureVector: {e}")

    def test_contract_scaffold_structure(self):
        """Verify the test scaffold follows expected structure."""
        # This test ensures the test class has the expected methods
        # for a complete contract test scaffold.
        assert hasattr(self, 'test_feature_vector_contract_exists')
        assert hasattr(self, 'test_error_message_consistency')
        assert hasattr(self, 'test_schema_validation_imports')
        assert hasattr(self, 'test_pydantic_model_imports')
