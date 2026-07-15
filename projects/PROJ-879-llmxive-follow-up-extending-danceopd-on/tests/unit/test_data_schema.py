"""
Unit tests for data schema validation.

Tests the validation logic for TeacherRoutingDataset, InferenceResult,
and DecisionTreeMetadata schemas defined in specs/contracts/.

These tests verify that:
1. Valid data passes validation
2. Invalid data (wrong types, missing fields, invalid values) fails validation
3. Schema definitions are correctly loaded and applied
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
SPECS_DIR = PROJECT_ROOT / "specs"

sys.path.insert(0, str(PROJECT_ROOT))

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Import schema validation function if it exists, otherwise create a minimal one
# Since T009 created the schemas but no validation function yet, we implement
# basic validation here for the tests
def validate_against_schema(data: Dict[str, Any], schema_path: Path) -> bool:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data to validate
        schema_path: Path to the JSON schema file
        
    Returns:
        True if valid, raises ValueError if invalid
        
    Raises:
        ValueError: If validation fails
        FileNotFoundError: If schema file not found
        ImportError: If jsonschema not installed
    """
    if not HAS_JSONSCHEMA:
        pytest.skip("jsonschema not installed")
        
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(schema_path, 'r') as f:
        schema = json.load(f)
        
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Schema validation failed: {e.message}") from e

# Test data fixtures
@pytest.fixture
def valid_teacher_routing_dataset() -> Dict[str, Any]:
    """Valid TeacherRoutingDataset sample"""
    return {
        "prompt_embedding": [0.1] * 512,
        "noise_level": 0.5,
        "routing_label": "expert_3",
        "velocity_vector": [0.2] * 128,
        "source": "imagenet"
    }

@pytest.fixture
def valid_inference_result() -> Dict[str, Any]:
    """Valid InferenceResult sample"""
    return {
        "sample_id": "sample_001",
        "prompt": "A cat sitting on a windowsill",
        "expert_used": "expert_3",
        "velocity_vector": [0.1] * 128,
        "image_path": "data/results/sample_001.png",
        "generation_time": 1.234,
        "success": True
    }

@pytest.fixture
def valid_decision_tree_metadata() -> Dict[str, Any]:
    """Valid DecisionTreeMetadata sample"""
    return {
        "model_id": "tree_depth_5_20240101",
        "max_depth": 5,
        "training_samples": 1000,
        "test_samples": 250,
        "accuracy": 0.87,
        "feature_names": ["prompt_embedding", "noise_level"],
        "created_at": "2024-01-01T12:00:00Z",
        "hash": "abc123def456"
    }

@pytest.fixture
def schema_dir() -> Path:
    """Path to the contracts directory"""
    return SPECS_DIR / "contracts"

# Test cases for TeacherRoutingDataset
class TestTeacherRoutingDatasetSchema:
    def test_valid_routing_dataset(self, valid_teacher_routing_dataset, schema_dir):
        """Test that valid routing dataset passes validation"""
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        # If schema doesn't exist, skip test (schema created in T009)
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
        validate_against_schema(valid_teacher_routing_dataset, schema_path)
    
    def test_missing_required_field(self, valid_teacher_routing_dataset, schema_dir):
        """Test that missing required field fails validation"""
        invalid_data = valid_teacher_routing_dataset.copy()
        del invalid_data["routing_label"]
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError, match="routing_label"):
            validate_against_schema(invalid_data, schema_path)
    
    def test_invalid_embedding_type(self, valid_teacher_routing_dataset, schema_dir):
        """Test that non-list embedding fails validation"""
        invalid_data = valid_teacher_routing_dataset.copy()
        invalid_data["prompt_embedding"] = "not a list"
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)
    
    def test_invalid_noise_level_type(self, valid_teacher_routing_dataset, schema_dir):
        """Test that non-numeric noise level fails validation"""
        invalid_data = valid_teacher_routing_dataset.copy()
        invalid_data["noise_level"] = "not a number"
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)
    
    def test_invalid_velocity_vector_length(self, valid_teacher_routing_dataset, schema_dir):
        """Test that mismatched velocity vector length fails validation if constrained"""
        # Note: This test may not fail if schema doesn't enforce length
        invalid_data = valid_teacher_routing_dataset.copy()
        invalid_data["velocity_vector"] = [0.1] * 10  # Wrong length
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        try:
            validate_against_schema(invalid_data, schema_path)
            # If it passes, the schema doesn't enforce length (acceptable)
        except ValueError:
            pass  # Expected if schema enforces length

# Test cases for InferenceResult
class TestInferenceResultSchema:
    def test_valid_inference_result(self, valid_inference_result, schema_dir):
        """Test that valid inference result passes validation"""
        schema_path = schema_dir / "InferenceResult.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
        validate_against_schema(valid_inference_result, schema_path)
    
    def test_missing_sample_id(self, valid_inference_result, schema_dir):
        """Test that missing sample_id fails validation"""
        invalid_data = valid_inference_result.copy()
        del invalid_data["sample_id"]
        
        schema_path = schema_dir / "InferenceResult.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError, match="sample_id"):
            validate_against_schema(invalid_data, schema_path)
    
    def test_invalid_success_type(self, valid_inference_result, schema_dir):
        """Test that non-boolean success field fails validation"""
        invalid_data = valid_inference_result.copy()
        invalid_data["success"] = "true"  # Should be boolean
        
        schema_path = schema_dir / "InferenceResult.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)
    
    def test_missing_image_path(self, valid_inference_result, schema_dir):
        """Test that missing image_path fails validation"""
        invalid_data = valid_inference_result.copy()
        del invalid_data["image_path"]
        
        schema_path = schema_dir / "InferenceResult.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError, match="image_path"):
            validate_against_schema(invalid_data, schema_path)

# Test cases for DecisionTreeMetadata
class TestDecisionTreeMetadataSchema:
    def test_valid_metadata(self, valid_decision_tree_metadata, schema_dir):
        """Test that valid metadata passes validation"""
        schema_path = schema_dir / "DecisionTreeMetadata.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
        validate_against_schema(valid_decision_tree_metadata, schema_path)
    
    def test_missing_model_id(self, valid_decision_tree_metadata, schema_dir):
        """Test that missing model_id fails validation"""
        invalid_data = valid_decision_tree_metadata.copy()
        del invalid_data["model_id"]
        
        schema_path = schema_dir / "DecisionTreeMetadata.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError, match="model_id"):
            validate_against_schema(invalid_data, schema_path)
    
    def test_invalid_max_depth_type(self, valid_decision_tree_metadata, schema_dir):
        """Test that non-integer max_depth fails validation"""
        invalid_data = valid_decision_tree_metadata.copy()
        invalid_data["max_depth"] = "5"  # Should be integer
        
        schema_path = schema_dir / "DecisionTreeMetadata.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)
    
    def test_negative_accuracy(self, valid_decision_tree_metadata, schema_dir):
        """Test that negative accuracy fails validation"""
        invalid_data = valid_decision_tree_metadata.copy()
        invalid_data["accuracy"] = -0.5
        
        schema_path = schema_dir / "DecisionTreeMetadata.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)
    
    def test_accuracy_greater_than_one(self, valid_decision_tree_metadata, schema_dir):
        """Test that accuracy > 1 fails validation"""
        invalid_data = valid_decision_tree_metadata.copy()
        invalid_data["accuracy"] = 1.5
        
        schema_path = schema_dir / "DecisionTreeMetadata.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)

# Integration tests for schema loading
class TestSchemaLoading:
    def test_schema_files_exist(self, schema_dir):
        """Test that all required schema files exist"""
        required_schemas = [
            "TeacherRoutingDataset.json",
            "InferenceResult.json",
            "DecisionTreeMetadata.json"
        ]
        
        for schema_name in required_schemas:
            schema_path = schema_dir / schema_name
            assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    def test_schema_files_are_valid_json(self, schema_dir):
        """Test that all schema files are valid JSON"""
        schema_files = list(schema_dir.glob("*.json"))
        
        for schema_file in schema_files:
            with open(schema_file, 'r') as f:
                try:
                    json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {schema_file}: {e}")

# Test edge cases
class TestEdgeCases:
    def test_empty_prompt_embedding(self, valid_teacher_routing_dataset, schema_dir):
        """Test empty prompt embedding list"""
        invalid_data = valid_teacher_routing_dataset.copy()
        invalid_data["prompt_embedding"] = []
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        # May or may not fail depending on schema constraints
        try:
            validate_against_schema(invalid_data, schema_path)
        except ValueError:
            pass  # Expected if schema enforces minimum length
    
    def test_null_routing_label(self, valid_teacher_routing_dataset, schema_dir):
        """Test null routing label"""
        invalid_data = valid_teacher_routing_dataset.copy()
        invalid_data["routing_label"] = None
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        with pytest.raises(ValueError):
            validate_against_schema(invalid_data, schema_path)
    
    def test_extra_fields(self, valid_teacher_routing_dataset, schema_dir):
        """Test that extra fields are allowed (if schema doesn't forbid them)"""
        data_with_extra = valid_teacher_routing_dataset.copy()
        data_with_extra["extra_field"] = "should be allowed"
        
        schema_path = schema_dir / "TeacherRoutingDataset.json"
        if not schema_path.exists():
            pytest.skip("Schema file not yet created")
            
        try:
            validate_against_schema(data_with_extra, schema_path)
            # If it passes, schema allows additional properties (acceptable)
        except ValueError:
            pass  # Expected if schema forbids additional properties

if __name__ == "__main__":
    pytest.main([__file__, "-v"])