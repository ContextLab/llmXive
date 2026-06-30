"""
Contract test for InferenceResult schema.

This module validates that inference results conform to the expected schema
defined in specs/contracts/inference_result.schema.yaml (or similar).
It ensures that all required fields are present and have the correct types.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.config import get_project_root, load_config, resolve_path
from tests.contract.test_schemas import SchemaValidator

# Define the expected schema structure for InferenceResult
# This should match the schema defined in specs/contracts/
INFERENCE_RESULT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "item_id",
        "model_name",
        "strategy",
        "prompt_used",
        "raw_response",
        "extracted_answer",
        "is_correct",
        "clean_accuracy",
        "timestamp"
    ],
    "properties": {
        "item_id": {"type": "string"},
        "model_name": {"type": "string"},
        "strategy": {"type": "string", "enum": ["baseline", "cot", "self_critique"]},
        "prompt_used": {"type": "string"},
        "raw_response": {"type": "string"},
        "extracted_answer": {
            "type": ["string", "null"],
            "description": "Extracted answer choice (A, B, C, D) or null if extraction failed"
        },
        "is_correct": {
            "type": ["boolean", "null"],
            "description": "True if extracted_answer matches gold answer, False if incorrect, null if extraction failed"
        },
        "clean_accuracy": {
            "type": ["number", "null"],
            "description": "Running accuracy on clean dataset for this model/strategy combination"
        },
        "timestamp": {"type": "string", "format": "date-time"},
        "timeout": {"type": "boolean", "default": False},
        "oom": {"type": "boolean", "default": False},
        "error_message": {"type": ["string", "null"]}
    },
    "additionalProperties": True
}

class InferenceResultValidator(SchemaValidator):
    """Validator for InferenceResult schema."""
    
    def __init__(self):
        super().__init__(INFERENCE_RESULT_SCHEMA)
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate a single inference result item."""
        return self.validate_schema(item)
    
    def validate_batch(self, items: List[Dict[str, Any]]) -> bool:
        """Validate a batch of inference result items."""
        for item in items:
            if not self.validate_item(item):
                return False
        return True

# Create validator instance
inference_result_validator = InferenceResultValidator()

def sample_inference_result() -> Dict[str, Any]:
    """Generate a sample valid InferenceResult for testing."""
    return {
        "item_id": "medqa_12345",
        "model_name": "meta-llama/Llama-2-13b-hf",
        "strategy": "baseline",
        "prompt_used": "Question: What is the primary treatment for hypertension? Options: A) Beta-blockers B) ACE inhibitors C) Diuretics D) Calcium channel blockers Answer:",
        "raw_response": "The correct answer is B) ACE inhibitors.",
        "extracted_answer": "B",
        "is_correct": True,
        "clean_accuracy": 0.75,
        "timestamp": "2024-01-15T10:30:00Z",
        "timeout": False,
        "oom": False,
        "error_message": None
    }

def sample_failed_inference_result() -> Dict[str, Any]:
    """Generate a sample InferenceResult with extraction failure."""
    return {
        "item_id": "medqa_67890",
        "model_name": "meta-llama/Llama-2-13b-hf",
        "strategy": "cot",
        "prompt_used": "Question: ...",
        "raw_response": "I'm not sure, but I think it might be A or B...",
        "extracted_answer": None,
        "is_correct": None,
        "clean_accuracy": 0.72,
        "timestamp": "2024-01-15T10:31:00Z",
        "timeout": False,
        "oom": False,
        "error_message": "Failed to extract answer"
    }

def sample_timeout_inference_result() -> Dict[str, Any]:
    """Generate a sample InferenceResult with timeout."""
    return {
        "item_id": "medqa_11111",
        "model_name": "meta-llama/Llama-2-70b-hf",
        "strategy": "self_critique",
        "prompt_used": "Question: ...",
        "raw_response": "",
        "extracted_answer": None,
        "is_correct": None,
        "clean_accuracy": None,
        "timestamp": "2024-01-15T10:32:00Z",
        "timeout": True,
        "oom": False,
        "error_message": "Execution timeout after 300 seconds"
    }

def sample_oom_inference_result() -> Dict[str, Any]:
    """Generate a sample InferenceResult with OOM."""
    return {
        "item_id": "medqa_22222",
        "model_name": "meta-llama/Llama-2-70b-hf",
        "strategy": "baseline",
        "prompt_used": "Question: ...",
        "raw_response": "",
        "extracted_answer": None,
        "is_correct": None,
        "clean_accuracy": None,
        "timestamp": "2024-01-15T10:33:00Z",
        "timeout": False,
        "oom": True,
        "error_message": "Out of memory error"
    }

class TestInferenceResultSchema:
    """Test suite for InferenceResult schema validation."""
    
    def test_valid_inference_result(self):
        """Test that a valid inference result passes validation."""
        result = sample_inference_result()
        assert inference_result_validator.validate_item(result)
    
    def test_failed_extraction_result(self):
        """Test that a result with failed extraction is valid (null fields)."""
        result = sample_failed_inference_result()
        assert inference_result_validator.validate_item(result)
    
    def test_timeout_result(self):
        """Test that a timeout result is valid."""
        result = sample_timeout_inference_result()
        assert inference_result_validator.validate_item(result)
    
    def test_oom_result(self):
        """Test that an OOM result is valid."""
        result = sample_oom_inference_result()
        assert inference_result_validator.validate_item(result)
    
    def test_missing_required_field(self):
        """Test that a result missing a required field fails validation."""
        result = sample_inference_result()
        del result["item_id"]
        assert not inference_result_validator.validate_item(result)
    
    def test_invalid_strategy(self):
        """Test that an invalid strategy value fails validation."""
        result = sample_inference_result()
        result["strategy"] = "invalid_strategy"
        assert not inference_result_validator.validate_item(result)
    
    def test_invalid_type_for_is_correct(self):
        """Test that an invalid type for is_correct fails validation."""
        result = sample_inference_result()
        result["is_correct"] = "true"  # Should be boolean, not string
        assert not inference_result_validator.validate_item(result)
    
    def test_batch_validation(self):
        """Test batch validation with mixed results."""
        results = [
            sample_inference_result(),
            sample_failed_inference_result(),
            sample_timeout_inference_result()
        ]
        assert inference_result_validator.validate_batch(results)
    
    def test_batch_with_invalid_item(self):
        """Test batch validation fails if any item is invalid."""
        results = [
            sample_inference_result(),
            sample_inference_result(),  # Valid
            sample_inference_result()
        ]
        del results[1]["model_name"]  # Make second item invalid
        assert not inference_result_validator.validate_batch(results)
    
    def test_load_from_jsonl(self):
        """Test loading and validating from a JSONL file."""
        # Create a temporary JSONL file
        temp_file = Path(project_root) / "data" / "processed" / "test_inference_results.jsonl"
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        
        test_data = [
            sample_inference_result(),
            sample_failed_inference_result()
        ]
        
        with open(temp_file, "w") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")
        
        # Load and validate
        loaded_results = []
        with open(temp_file, "r") as f:
            for line in f:
                if line.strip():
                    loaded_results.append(json.loads(line))
        
        assert inference_result_validator.validate_batch(loaded_results)
        
        # Cleanup
        temp_file.unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])