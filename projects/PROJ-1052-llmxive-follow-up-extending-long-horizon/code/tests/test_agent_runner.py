"""
Contract tests for the agent_runner execution log schema.

This module validates the schema contract defined in T005
(specs/001-reward-fidelity-error-recovery/contracts/execution_log.schema.yaml)
by verifying that malformed execution logs raise appropriate ValidationErrors.

Depends on: T005 (Schema definitions)
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    raise ImportError(
        "The 'jsonschema' package is required for contract tests. "
        "Install it via: pip install jsonschema"
    )

from code.utils.logging_handler import load_config

class TestExecutionLogSchema(unittest.TestCase):
    """
    Contract tests for the execution log schema.
    
    These tests validate that the schema contract defined in T005
    correctly enforces required fields and data types.
    """

    @classmethod
    def setUpClass(cls):
        """Load the schema once for all tests."""
        # Determine schema path relative to project root
        schema_path = (
            PROJECT_ROOT / 
            "specs" / 
            "001-reward-fidelity-error-recovery" / 
            "contracts" / 
            "execution_log.schema.yaml"
        )
        
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found at {schema_path}. "
                "Ensure T005 has been completed and the schema file exists."
            )
        
        # Load schema - note: we need to handle YAML loading
        try:
            import yaml
            with open(schema_path, 'r') as f:
                cls.schema = yaml.safe_load(f)
        except ImportError:
            raise ImportError(
                "The 'pyyaml' package is required to load the schema. "
                "Install it via: pip install pyyaml"
            )
        
        # Ensure schema is valid JSON schema
        Draft7Validator.check_schema(cls.schema)

    def test_execution_log_schema_validates_task_id_field(self):
        """
        Verify that a malformed execution log (missing `task_id`) raises `ValidationError`.
        
        This test validates the schema contract defined in T005.
        The schema should require 'task_id' as a mandatory field.
        """
        # Create a valid execution log entry with all required fields
        valid_log = {
            "task_id": "agentbench_db_001",
            "success": True,
            "trajectory": [
                {"step": 1, "observation": "Database connected", "action": "connect", "reward": 1.0},
                {"step": 2, "observation": "Query executed", "action": "query", "reward": 1.0}
            ],
            "recovery_segment_id": "seg_001",
            "reward_fidelity_level": "dense"
        }
        
        # Create a malformed log missing the required task_id field
        malformed_log = valid_log.copy()
        del malformed_log["task_id"]
        
        # Verify that validation of the malformed log raises ValidationError
        with self.assertRaises(ValidationError) as context:
            validate(instance=malformed_log, schema=self.schema)
        
        # Verify the error message mentions the missing field
        error_message = str(context.exception)
        self.assertIn("task_id", error_message)
        self.assertIn("is a required property", error_message)

    def test_execution_log_schema_validates_success_field(self):
        """
        Verify that a malformed execution log (missing `success`) raises `ValidationError`.
        """
        valid_log = {
            "task_id": "agentbench_db_001",
            "success": True,
            "trajectory": [
                {"step": 1, "observation": "Database connected", "action": "connect", "reward": 1.0}
            ],
            "recovery_segment_id": "seg_001",
            "reward_fidelity_level": "dense"
        }
        
        malformed_log = valid_log.copy()
        del malformed_log["success"]
        
        with self.assertRaises(ValidationError) as context:
            validate(instance=malformed_log, schema=self.schema)
        
        error_message = str(context.exception)
        self.assertIn("success", error_message)

    def test_execution_log_schema_validates_trajectory_field(self):
        """
        Verify that a malformed execution log (missing `trajectory`) raises `ValidationError`.
        """
        valid_log = {
            "task_id": "agentbench_db_001",
            "success": True,
            "trajectory": [
                {"step": 1, "observation": "Database connected", "action": "connect", "reward": 1.0}
            ],
            "recovery_segment_id": "seg_001",
            "reward_fidelity_level": "dense"
        }
        
        malformed_log = valid_log.copy()
        del malformed_log["trajectory"]
        
        with self.assertRaises(ValidationError) as context:
            validate(instance=malformed_log, schema=self.schema)
        
        error_message = str(context.exception)
        self.assertIn("trajectory", error_message)

    def test_valid_execution_log_passes_validation(self):
        """
        Verify that a properly formed execution log passes schema validation.
        """
        valid_log = {
            "task_id": "agentbench_db_001",
            "success": True,
            "trajectory": [
                {"step": 1, "observation": "Database connected", "action": "connect", "reward": 1.0},
                {"step": 2, "observation": "Query executed", "action": "query", "reward": 1.0}
            ],
            "recovery_segment_id": "seg_001",
            "reward_fidelity_level": "dense"
        }
        
        # This should not raise any exception
        try:
            validate(instance=valid_log, schema=self.schema)
        except ValidationError as e:
            self.fail(f"Valid execution log should not raise ValidationError: {e}")

if __name__ == "__main__":
    unittest.main()