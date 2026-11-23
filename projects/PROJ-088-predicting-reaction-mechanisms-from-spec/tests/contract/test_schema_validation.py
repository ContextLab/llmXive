"""
Contract tests for dataset and output schemas defined in specs/contracts/.
These tests validate that the data structures produced by the pipeline
conform to the defined YAML schemas.
"""
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any

# Simple schema validator implementation (no external heavy deps like jsonschema for this test)
# In a full CI, we might use `jsonschema` library, but here we validate structure manually
# to ensure the schema definitions are syntactically correct and logically sound.

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "contracts"

def load_schema(filename: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    schema_path = SCHEMAS_DIR / filename
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

class TestDatasetSchema:
    """Tests for dataset.schema.yaml"""

    @pytest.fixture
    def schema(self):
        return load_schema("dataset.schema.yaml")

    def test_schema_exists_and_valid_yaml(self, schema):
        """Ensure the schema file is valid YAML and contains required keys."""
        assert schema is not None
        assert "properties" in schema
        assert "metadata" in schema["properties"]
        assert "data" in schema["properties"]

    def test_metadata_required_fields(self, schema):
        """Check that metadata has required fields."""
        metadata_props = schema["properties"]["metadata"]["properties"]
        required = schema["properties"]["metadata"]["required"]
        
        assert "version" in metadata_props
        assert "source" in metadata_props
        assert "provenance_filter_applied" in metadata_props
        assert "created_at" in metadata_props
        assert "checksum" in metadata_props
        
        # Verify required list
        assert "version" in required
        assert "source" in required
        assert "provenance_filter_applied" in required
        assert "created_at" in required
        assert "checksum" in required

    def test_data_item_structure(self, schema):
        """Check the structure of a single data item."""
        data_items = schema["properties"]["data"]["items"]["properties"]
        required = schema["properties"]["data"]["items"]["required"]

        assert "record_id" in data_items
        assert "spectrum" in data_items
        assert "label" in data_items
        assert "provenance" in data_items
        
        # Check spectrum constraints
        spectrum_def = data_items["spectrum"]
        assert spectrum_def["type"] == "array"
        assert spectrum_def["minItems"] == 512
        assert spectrum_def["maxItems"] == 512

        # Check label enum
        label_def = data_items["label"]
        assert label_def["type"] == "string"
        assert "enum" in label_def
        assert "SN1" in label_def["enum"]
        assert "SN2" in label_def["enum"]
        assert "E1" in label_def["enum"]

    def test_provenance_enum(self, schema):
        """Ensure provenance field restricts to valid kinetic/validated sources."""
        data_items = schema["properties"]["data"]["items"]["properties"]
        provenance_def = data_items["provenance"]
        
        assert "enum" in provenance_def
        allowed = provenance_def["enum"]
        assert "kinetic_studies" in allowed
        assert "validated_intermediates" in allowed
        # Ensure 'product_structure' is NOT allowed
        assert "product_structure" not in allowed

class TestOutputSchema:
    """Tests for output.schema.yaml"""

    @pytest.fixture
    def schema(self):
        return load_schema("output.schema.yaml")

    def test_schema_exists_and_valid_yaml(self, schema):
        """Ensure the schema file is valid YAML."""
        assert schema is not None
        assert "properties" in schema
        assert "training_results" in schema["properties"]
        assert "feature_importance" in schema["properties"]

    def test_training_results_structure(self, schema):
        """Check training results structure."""
        training = schema["properties"]["training_results"]["properties"]
        required = schema["properties"]["training_results"]["required"]

        assert "cv_folds" in training
        assert "metrics" in training
        assert "cv_folds" in required
        assert "metrics" in required

    def test_metrics_structure(self, schema):
        """Check that metrics contain accuracy and F1 scores."""
        metrics = schema["properties"]["training_results"]["properties"]["metrics"]["properties"]
        
        assert "accuracy" in metrics
        assert "f1_macro" in metrics
        assert "f1_weighted" in metrics
        
        # Check accuracy substructure
        acc_props = metrics["accuracy"]["properties"]
        assert "mean" in acc_props
        assert "std" in acc_props

    def test_feature_importance_structure(self, schema):
        """Check feature importance structure."""
        importance = schema["properties"]["feature_importance"]["properties"]
        required = schema["properties"]["feature_importance"]["required"]

        assert "top_features" in importance
        assert "stability_variance" in importance
        assert "top_features" in required
        assert "stability_variance" in required

    def test_causal_language_check(self, schema):
        """
        Verify that the schema description or comments do not contain forbidden causal terms.
        This enforces FR-006 at the schema definition level.
        """
        schema_str = yaml.dump(schema)
        forbidden = ["cause", "drive", "determine", "proves", "causes"]
        
        for word in forbidden:
            assert word not in schema_str.lower(), \
                f"Forbidden causal term '{word}' found in schema definition."
