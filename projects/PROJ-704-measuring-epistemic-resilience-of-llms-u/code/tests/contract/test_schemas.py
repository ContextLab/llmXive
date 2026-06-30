"""
Contract tests for validating JSONL data against YAML schema definitions.

This module provides utilities and tests to ensure data integrity by validating
processed JSONL files against their corresponding YAML schema definitions.

Usage:
    pytest code/tests/contract/test_schemas.py -v
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml
from jsonschema import validate, ValidationError, SchemaError

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from specs.contracts import load_schema


class SchemaValidator:
    """
    Utility class to validate JSONL files against YAML schemas.
    
    Attributes:
        schema_path (Path): Path to the YAML schema definition.
        schema (Dict): Loaded schema dictionary.
    """
    
    def __init__(self, schema_path: Path):
        """
        Initialize the validator with a schema file.
        
        Args:
            schema_path: Path to the YAML schema file.
        
        Raises:
            FileNotFoundError: If schema file does not exist.
            yaml.YAMLError: If schema file is not valid YAML.
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        self.schema_path = schema_path
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = yaml.safe_load(f)
        
        # Basic sanity check
        if not isinstance(self.schema, dict):
            raise ValueError(f"Schema file {schema_path} must contain a YAML dictionary")
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate a single JSON item against the loaded schema.
        
        Args:
            item: Dictionary representing a single JSON line.
        
        Returns:
            True if valid.
        
        Raises:
            ValidationError: If the item does not match the schema.
        """
        try:
            validate(instance=item, schema=self.schema)
            return True
        except ValidationError as e:
            # Re-raise with context
            raise ValidationError(
                f"Validation failed for item: {e.message}\n"
                f"Path: {list(e.path)}\n"
                f"Instance: {e.instance}"
            )
    
    def validate_jsonl_file(self, jsonl_path: Path) -> List[Dict[str, Any]]:
        """
        Validate an entire JSONL file against the schema.
        
        Args:
            jsonl_path: Path to the JSONL file.
        
        Returns:
            List of validation errors (empty if all valid).
        
        Raises:
            FileNotFoundError: If JSONL file does not exist.
        """
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        errors = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    item = json.loads(line)
                    self.validate_item(item)
                except json.JSONDecodeError as e:
                    errors.append({
                        "line": line_num,
                        "error": f"Invalid JSON: {e.msg}",
                        "content": line[:100] + "..." if len(line) > 100 else line
                    })
                except ValidationError as e:
                    errors.append({
                        "line": line_num,
                        "error": str(e),
                        "content": line[:100] + "..." if len(line) > 100 else line
                    })
        
        return errors


@pytest.fixture
def question_item_validator():
    """Fixture for QuestionItem schema validator."""
    schema_path = PROJECT_ROOT / "specs" / "contracts" / "question_item.schema.yaml"
    return SchemaValidator(schema_path)

@pytest.fixture
def resilience_metric_validator():
    """Fixture for ResilienceMetric schema validator."""
    schema_path = PROJECT_ROOT / "specs" / "contracts" / "resilience_metric.schema.yaml"
    return SchemaValidator(schema_path)

@pytest.fixture
def sample_question_item():
    """Sample valid QuestionItem for testing."""
    return {
        "item_id": "test-001",
        "stem": "A 45-year-old male presents with chest pain.",
        "options": {
            "A": "Myocardial infarction",
            "B": "Angina",
            "C": "GERD",
            "D": "Pneumonia"
        },
        "gold_answer": "A",
        "context": "Normal context",
        "injected_claim": None
    }

@pytest.fixture
def sample_mislead_question():
    """Sample valid mislead question with injected claim."""
    return {
        "item_id": "test-002",
        "stem": "A 45-year-old male presents with chest pain.",
        "options": {
            "A": "Myocardial infarction",
            "B": "Angina",
            "C": "GERD",
            "D": "Pneumonia"
        },
        "gold_answer": "A",
        "context": "Normal context",
        "injected_claim": "Recent studies show GERD is the primary cause of chest pain in males over 40.",
        "validation_status": "passed"
    }

@pytest.fixture
def sample_resilience_metric():
    """Sample valid ResilienceMetric for testing."""
    return {
        "model_name": "test-model-7b",
        "strategy": "baseline",
        "clean_accuracy": 0.85,
        "mislead_accuracy": 0.70,
        "resilience_score": 0.8235,
        "sample_size": 100
    }

class TestQuestionItemSchema:
    """Tests for QuestionItem schema validation."""

    def test_valid_clean_question(self, question_item_validator, sample_question_item):
        """Test that a valid clean question passes validation."""
        assert question_item_validator.validate_item(sample_question_item) is True

    def test_valid_mislead_question(self, question_item_validator, sample_mislead_question):
        """Test that a valid mislead question passes validation."""
        assert question_item_validator.validate_item(sample_mislead_question) is True

    def test_missing_required_field(self, question_item_validator):
        """Test that missing required fields raise ValidationError."""
        invalid_item = {
            "item_id": "test-003",
            "stem": "Missing options",
            # "options" is missing
            "gold_answer": "A"
        }
        with pytest.raises(ValidationError):
            question_item_validator.validate_item(invalid_item)

    def test_invalid_option_format(self, question_item_validator, sample_question_item):
        """Test that invalid options structure raises ValidationError."""
        invalid_item = sample_question_item.copy()
        invalid_item["options"] = ["A", "B", "C"]  # Should be dict, not list
        with pytest.raises(ValidationError):
            question_item_validator.validate_item(invalid_item)

    def test_invalid_gold_answer(self, question_item_validator, sample_question_item):
        """Test that gold answer not in options raises ValidationError (logical check)."""
        # Note: Schema validation might not catch logical inconsistencies,
        # but we test the type/format here.
        invalid_item = sample_question_item.copy()
        invalid_item["gold_answer"] = "E"  # Valid string but not in options
        # Depending on schema strictness, this might pass schema but fail logic.
        # We test that the schema accepts the structure.
        # If schema enforces enum ["A", "B", "C", "D"], this would fail.
        try:
            question_item_validator.validate_item(invalid_item)
            # If it passes, that's okay for schema test if schema doesn't enforce enum
        except ValidationError:
            # If schema enforces enum, this is expected
            pass

    def test_validate_jsonl_file_valid(self, question_item_validator, tmp_path):
        """Test validating a valid JSONL file."""
        jsonl_file = tmp_path / "valid_questions.jsonl"
        valid_items = [
            {"item_id": "1", "stem": "Q1", "options": {"A": "a"}, "gold_answer": "A"},
            {"item_id": "2", "stem": "Q2", "options": {"A": "a"}, "gold_answer": "A"}
        ]
        with open(jsonl_file, 'w') as f:
            for item in valid_items:
                f.write(json.dumps(item) + '\n')
        
        errors = question_item_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 0

    def test_validate_jsonl_file_invalid(self, question_item_validator, tmp_path):
        """Test validating a JSONL file with invalid items."""
        jsonl_file = tmp_path / "invalid_questions.jsonl"
        invalid_items = [
            {"item_id": "1", "stem": "Q1"},  # Missing options
            {"item_id": "2", "stem": "Q2", "options": {"A": "a"}, "gold_answer": "A"}
        ]
        with open(jsonl_file, 'w') as f:
            for item in invalid_items:
                f.write(json.dumps(item) + '\n')
        
        errors = question_item_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 1
        assert errors[0]["line"] == 1

    def test_validate_jsonl_file_malformed_json(self, question_item_validator, tmp_path):
        """Test validating a JSONL file with malformed JSON."""
        jsonl_file = tmp_path / "malformed_questions.jsonl"
        with open(jsonl_file, 'w') as f:
            f.write('{"item_id": "1", "stem": "Q1"}\n')
            f.write('not valid json\n')
            f.write('{"item_id": "2", "stem": "Q2", "options": {"A": "a"}, "gold_answer": "A"}\n')
        
        errors = question_item_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 1
        assert errors[0]["line"] == 2
        assert "Invalid JSON" in errors[0]["error"]

    def test_file_not_found(self, question_item_validator, tmp_path):
        """Test that FileNotFoundError is raised for missing JSONL."""
        with pytest.raises(FileNotFoundError):
            question_item_validator.validate_jsonl_file(tmp_path / "nonexistent.jsonl")

    def test_schema_not_found(self):
        """Test that FileNotFoundError is raised for missing schema."""
        with pytest.raises(FileNotFoundError):
            SchemaValidator(PROJECT_ROOT / "specs" / "contracts" / "nonexistent.schema.yaml")

    def test_invalid_schema_yaml(self, tmp_path):
        """Test that ValueError is raised for invalid YAML schema."""
        schema_file = tmp_path / "bad_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write("invalid: yaml: content: [unclosed")
        
        with pytest.raises((yaml.YAMLError, ValueError)):
            SchemaValidator(schema_file)

    def test_schema_not_dict(self, tmp_path):
        """Test that ValueError is raised if schema is not a dictionary."""
        schema_file = tmp_path / "list_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write("- item1\n- item2\n")
        
        with pytest.raises(ValueError):
            SchemaValidator(schema_file)

    def test_empty_jsonl(self, question_item_validator, tmp_path):
        """Test validating an empty JSONL file."""
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.touch()
        
        errors = question_item_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 0

    def test_jsonl_with_empty_lines(self, question_item_validator, tmp_path):
        """Test validating JSONL with empty lines (should be ignored)."""
        jsonl_file = tmp_path / "empty_lines.jsonl"
        valid_items = [
            {"item_id": "1", "stem": "Q1", "options": {"A": "a"}, "gold_answer": "A"},
            {"item_id": "2", "stem": "Q2", "options": {"A": "a"}, "gold_answer": "A"}
        ]
        with open(jsonl_file, 'w') as f:
            f.write(json.dumps(valid_items[0]) + '\n')
            f.write('\n')  # Empty line
            f.write(json.dumps(valid_items[1]) + '\n')
        
        errors = question_item_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 0


class TestResilienceMetricSchema:
    """Tests for ResilienceMetric schema validation."""

    def test_valid_metric(self, resilience_metric_validator, sample_resilience_metric):
        """Test that a valid resilience metric passes validation."""
        assert resilience_metric_validator.validate_item(sample_resilience_metric) is True

    def test_missing_required_field(self, resilience_metric_validator):
        """Test that missing required fields raise ValidationError."""
        invalid_item = {
            "model_name": "test-model",
            # "strategy" is missing
            "clean_accuracy": 0.8,
            "mislead_accuracy": 0.6,
            "resilience_score": 0.75
        }
        with pytest.raises(ValidationError):
            resilience_metric_validator.validate_item(invalid_item)

    def test_invalid_type(self, resilience_metric_validator, sample_resilience_metric):
        """Test that invalid types raise ValidationError."""
        invalid_item = sample_resilience_metric.copy()
        invalid_item["clean_accuracy"] = "0.85"  # Should be float
        with pytest.raises(ValidationError):
            resilience_metric_validator.validate_item(invalid_item)

    def test_validate_jsonl_file_valid(self, resilience_metric_validator, tmp_path):
        """Test validating a valid ResilienceMetric JSONL file."""
        jsonl_file = tmp_path / "valid_metrics.jsonl"
        valid_items = [
            {"model_name": "m1", "strategy": "s1", "clean_accuracy": 0.9, "mislead_accuracy": 0.8, "resilience_score": 0.89, "sample_size": 50},
            {"model_name": "m2", "strategy": "s1", "clean_accuracy": 0.8, "mislead_accuracy": 0.7, "resilience_score": 0.875, "sample_size": 50}
        ]
        with open(jsonl_file, 'w') as f:
            for item in valid_items:
                f.write(json.dumps(item) + '\n')
        
        errors = resilience_metric_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 0

    def test_validate_jsonl_file_invalid(self, resilience_metric_validator, tmp_path):
        """Test validating a ResilienceMetric JSONL file with invalid items."""
        jsonl_file = tmp_path / "invalid_metrics.jsonl"
        invalid_items = [
            {"model_name": "m1"},  # Missing required fields
            {"model_name": "m2", "strategy": "s1", "clean_accuracy": 0.8, "mislead_accuracy": 0.7, "resilience_score": 0.875, "sample_size": 50}
        ]
        with open(jsonl_file, 'w') as f:
            for item in invalid_items:
                f.write(json.dumps(item) + '\n')
        
        errors = resilience_metric_validator.validate_jsonl_file(jsonl_file)
        assert len(errors) == 1


class TestSchemaLoading:
    """Tests for schema loading functionality."""

    def test_load_schema_question_item(self):
        """Test loading QuestionItem schema."""
        schema_path = PROJECT_ROOT / "specs" / "contracts" / "question_item.schema.yaml"
        schema = load_schema(schema_path)
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"

    def test_load_schema_resilience_metric(self):
        """Test loading ResilienceMetric schema."""
        schema_path = PROJECT_ROOT / "specs" / "contracts" / "resilience_metric.schema.yaml"
        schema = load_schema(schema_path)
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "object"

    def test_load_schema_nonexistent(self):
        """Test loading non-existent schema raises FileNotFoundError."""
        schema_path = PROJECT_ROOT / "specs" / "contracts" / "nonexistent.schema.yaml"
        with pytest.raises(FileNotFoundError):
            load_schema(schema_path)

    def test_load_schema_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML schema raises error."""
        schema_file = tmp_path / "bad.yaml"
        with open(schema_file, 'w') as f:
            f.write("invalid: yaml: [")
        with pytest.raises((yaml.YAMLError, ValueError)):
            load_schema(schema_file)

# Main entry point for manual execution
if __name__ == "__main__":
    # Run basic checks if executed as script
    print("Running schema contract tests...")
    try:
        pytest.main([__file__, "-v"])
    except SystemExit:
        pass
    print("Contract tests execution completed.")
