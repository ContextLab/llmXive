"""
Contract tests for schema validation functionality.

These tests verify that the schema validator correctly validates
JSON outputs against their contract schemas.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import (
    load_schema,
    validate_json_against_schema,
    validate_output_file,
    run_validation
)


class TestSchemaLoading:
    """Tests for schema loading functionality."""
    
    def test_load_yaml_schema(self, tmp_path):
        """Test loading a YAML schema file."""
        schema_content = {
            "type": "object",
            "required": ["pairs"],
            "properties": {
                "pairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["model_a", "model_b", "cosine_similarity"],
                        "properties": {
                            "model_a": {"type": "string"},
                            "model_b": {"type": "string"},
                            "cosine_similarity": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        schema_file = tmp_path / "test.schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
        
        loaded_schema = load_schema(schema_file)
        assert loaded_schema == schema_content
        assert loaded_schema["type"] == "object"
        assert "pairs" in loaded_schema["required"]
    
    def test_load_nonexistent_schema(self, tmp_path):
        """Test that loading a nonexistent schema raises an error."""
        with pytest.raises(FileNotFoundError):
            load_schema(tmp_path / "nonexistent.schema.yaml")
    
    def test_load_invalid_schema(self, tmp_path):
        """Test that loading an invalid schema raises an error."""
        schema_file = tmp_path / "invalid.schema.yaml"
        schema_file.write_text("not: a: valid: yaml: [")
        
        with pytest.raises(ValueError):
            load_schema(schema_file)


class TestValidationLogic:
    """Tests for the validation logic."""
    
    def test_valid_object(self):
        """Test validation of a valid object."""
        data = {
            "name": "test",
            "value": 42,
            "active": True
        }
        
        schema = {
            "type": "object",
            "required": ["name", "value"],
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"},
                "active": {"type": "boolean"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_field(self):
        """Test validation with a missing required field."""
        data = {
            "name": "test"
        }
        
        schema = {
            "type": "object",
            "required": ["name", "value"],
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert len(errors) > 0
        assert any("value" in error for error in errors)
    
    def test_wrong_type(self):
        """Test validation with wrong field type."""
        data = {
            "name": 123  # Should be string
        }
        
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert len(errors) > 0
        assert any("string" in error for error in errors)
    
    def test_valid_array(self):
        """Test validation of a valid array."""
        data = {
            "items": [1, 2, 3, 4]
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_array_items(self):
        """Test validation with invalid array items."""
        data = {
            "items": [1, "two", 3]
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert len(errors) > 0
        assert any("number" in error for error in errors)


class TestSimilarityReportSchema:
    """Tests specific to the similarity report schema."""
    
    def test_valid_similarity_report(self):
        """Test validation of a valid similarity report."""
        data = {
            "pairs": [
                {
                    "model_a": "llama-3",
                    "model_b": "mistral",
                    "cosine_similarity": 0.85
                },
                {
                    "model_a": "llama-3",
                    "model_b": "bloom",
                    "cosine_similarity": 0.72
                }
            ]
        }
        
        schema = {
            "type": "object",
            "required": ["pairs"],
            "properties": {
                "pairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["model_a", "model_b", "cosine_similarity"],
                        "properties": {
                            "model_a": {"type": "string"},
                            "model_b": {"type": "string"},
                            "cosine_similarity": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_similarity_report_missing_field(self):
        """Test validation of an invalid similarity report."""
        data = {
            "pairs": [
                {
                    "model_a": "llama-3",
                    "model_b": "mistral"
                    # Missing cosine_similarity
                }
            ]
        }
        
        schema = {
            "type": "object",
            "required": ["pairs"],
            "properties": {
                "pairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["model_a", "model_b", "cosine_similarity"],
                        "properties": {
                            "model_a": {"type": "string"},
                            "model_b": {"type": "string"},
                            "cosine_similarity": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert not is_valid
        assert len(errors) > 0


class TestTokenAttributionSchema:
    """Tests specific to the token attribution schema."""
    
    def test_valid_token_attribution(self):
        """Test validation of a valid token attribution report."""
        data = {
            "language": "en",
            "top_tokens": [
                {"token": "the", "score": 0.95},
                {"token": "of", "score": 0.88},
                {"token": "and", "score": 0.82}
            ],
            "total_tokens_analyzed": 1000000
        }
        
        schema = {
            "type": "object",
            "required": ["language", "top_tokens"],
            "properties": {
                "language": {"type": "string"},
                "top_tokens": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["token", "score"],
                        "properties": {
                            "token": {"type": "string"},
                            "score": {"type": "number"}
                        }
                    }
                },
                "total_tokens_analyzed": {"type": "number"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0


class TestPermutationResultSchema:
    """Tests specific to the permutation result schema."""
    
    def test_valid_permutation_result(self):
        """Test validation of a valid permutation result."""
        data = {
            "p_value": 0.023,
            "is_significant": True,
            "iterations": 1000,
            "observed_statistic": 0.45,
            "null_distribution_mean": 0.12
        }
        
        schema = {
            "type": "object",
            "required": ["p_value", "is_significant"],
            "properties": {
                "p_value": {"type": "number"},
                "is_significant": {"type": "boolean"},
                "iterations": {"type": "number"},
                "observed_statistic": {"type": "number"},
                "null_distribution_mean": {"type": "number"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0


class TestWALSValidationSchema:
    """Tests specific to the WALS validation schema."""
    
    def test_valid_wals_validation(self):
        """Test validation of a valid WALS validation result."""
        data = {
            "correlation": 0.67,
            "p_value": 0.001,
            "method": "spearman",
            "data_available": True,
            "features_tested": ["phonology", "morphology"]
        }
        
        schema = {
            "type": "object",
            "required": ["correlation", "method"],
            "properties": {
                "correlation": {"type": "number"},
                "p_value": {"type": "number"},
                "method": {"type": "string"},
                "data_available": {"type": "boolean"},
                "features_tested": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
    
    def test_wals_data_unavailable(self):
        """Test validation when WALS data is unavailable."""
        data = {
            "correlation": None,
            "p_value": None,
            "method": "spearman",
            "data_available": False,
            "features_tested": [],
            "reason": "Data source not accessible"
        }
        
        schema = {
            "type": "object",
            "required": ["method", "data_available"],
            "properties": {
                "correlation": {"type": ["number", "null"]},
                "p_value": {"type": ["number", "null"]},
                "method": {"type": "string"},
                "data_available": {"type": "boolean"},
                "features_tested": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "reason": {"type": "string"}
            }
        }
        
        is_valid, errors = validate_json_against_schema(data, schema)
        assert is_valid
        assert len(errors) == 0
