"""
Contract tests for schema validation of training configuration and evaluation results.
Validates that JSON/YAML data conforms to the defined schemas using jsonschema.
"""
import json
import os
import unittest
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Determine project root relative to this file (tests/contract/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SPECS_DIR = PROJECT_ROOT / "specs" / "001-dream-state-learning-implementing-rem-li"

class TestTrainingConfigSchema(unittest.TestCase):
    """Tests for training_config.schema.yaml validation."""

    def setUp(self):
        """Load the training config schema."""
        schema_path = SPECS_DIR / "training_config.schema.yaml"
        if not schema_path.exists():
            self.skipTest(f"Schema file not found: {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = yaml.safe_load(f)
        
        # Ensure schema is valid Draft7
        Draft7Validator.check_schema(self.schema)

    def test_valid_config(self):
        """Test a valid training configuration."""
        valid_config = {
            "model_name": "distilbert-base-uncased",
            "learning_rate": 5e-5,
            "batch_size": 8,
            "num_epochs": 3,
            "warmup_steps": 10,
            "dream_ratio": 0.25,
            "entropy_threshold": 0.5,
            "max_retries": 3,
            "seed": 42,
            "output_dir": "data/results"
        }
        validate(instance=valid_config, schema=self.schema)

    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        invalid_config = {
            "model_name": "distilbert-base-uncased",
            "learning_rate": 5e-5
            # Missing required: batch_size
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_config, schema=self.schema)

    def test_invalid_type(self):
        """Test that invalid types raise ValidationError."""
        invalid_config = {
            "model_name": "distilbert-base-uncased",
            "learning_rate": "fivee-5",  # Should be number, not string
            "batch_size": 8,
            "num_epochs": 3,
            "warmup_steps": 10,
            "dream_ratio": 0.25,
            "entropy_threshold": 0.5,
            "max_retries": 3,
            "seed": 42,
            "output_dir": "data/results"
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_config, schema=self.schema)

    def test_out_of_range_value(self):
        """Test that values outside allowed range raise ValidationError."""
        invalid_config = {
            "model_name": "distilbert-base-uncased",
            "learning_rate": 5e-5,
            "batch_size": 8,
            "num_epochs": 3,
            "warmup_steps": 10,
            "dream_ratio": 1.5,  # Must be between 0 and 1
            "entropy_threshold": 0.5,
            "max_retries": 3,
            "seed": 42,
            "output_dir": "data/results"
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_config, schema=self.schema)


class TestEvaluationResultSchema(unittest.TestCase):
    """Tests for evaluation_result.schema.yaml validation."""

    def setUp(self):
        """Load the evaluation result schema."""
        schema_path = SPECS_DIR / "evaluation_result.schema.yaml"
        if not schema_path.exists():
            self.skipTest(f"Schema file not found: {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = yaml.safe_load(f)
        
        # Ensure schema is valid Draft7
        Draft7Validator.check_schema(self.schema)

    def test_valid_result(self):
        """Test a valid evaluation result."""
        valid_result = {
            "experiment_id": "exp_001",
            "seed": 42,
            "model_name": "distilbert-base-uncased",
            "dataset": "glue-mrpc",
            "accuracy": 0.85,
            "loss": 0.32,
            "training_steps": 1000,
            "wall_clock_hours": 2.5,
            "phase_breakdown": {
                "wake_steps": 750,
                "dream_steps": 250
            },
            "entropy_metrics": {
                "mean": 0.75,
                "min": 0.2,
                "max": 1.2
            }
        }
        validate(instance=valid_result, schema=self.schema)

    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        invalid_result = {
            "experiment_id": "exp_001",
            "seed": 42,
            "model_name": "distilbert-base-uncased",
            "dataset": "glue-mrpc",
            "accuracy": 0.85
            # Missing required: loss
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_result, schema=self.schema)

    def test_invalid_type(self):
        """Test that invalid types raise ValidationError."""
        invalid_result = {
            "experiment_id": "exp_001",
            "seed": 42,
            "model_name": "distilbert-base-uncased",
            "dataset": "glue-mrpc",
            "accuracy": "0.85",  # Should be number, not string
            "loss": 0.32,
            "training_steps": 1000,
            "wall_clock_hours": 2.5,
            "phase_breakdown": {
                "wake_steps": 750,
                "dream_steps": 250
            },
            "entropy_metrics": {
                "mean": 0.75,
                "min": 0.2,
                "max": 1.2
            }
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_result, schema=self.schema)

    def test_negative_value(self):
        """Test that negative values where not allowed raise ValidationError."""
        invalid_result = {
            "experiment_id": "exp_001",
            "seed": 42,
            "model_name": "distilbert-base-uncased",
            "dataset": "glue-mrpc",
            "accuracy": 0.85,
            "loss": 0.32,
            "training_steps": -100,  # Should be non-negative
            "wall_clock_hours": 2.5,
            "phase_breakdown": {
                "wake_steps": 750,
                "dream_steps": 250
            },
            "entropy_metrics": {
                "mean": 0.75,
                "min": 0.2,
                "max": 1.2
            }
        }
        with self.assertRaises(ValidationError):
            validate(instance=invalid_result, schema=self.schema)


if __name__ == "__main__":
    unittest.main()
