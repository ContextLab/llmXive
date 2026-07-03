"""
Contract tests for data schemas in the llmXive pipeline.

This module validates that data artifacts produced by the pipeline
conform to the expected JSON schemas defined in the contracts/ directory.

Tests are designed to fail fast if schema violations occur, ensuring
data integrity throughout the research pipeline.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Schema paths
SCHEMAS_DIR = PROJECT_ROOT / "contracts"

# Lazy schema loading to avoid import errors in test discovery
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON/YAML schema from the contracts directory."""
    if schema_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_name]
    
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        if schema_path.suffix in (".yaml", ".yml"):
            schema = yaml.safe_load(f)
        else:
            schema = json.load(f)
    
    _SCHEMA_CACHE[schema_name] = schema
    return schema

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Basic JSON Schema validation (lightweight, no external validator dependency).
    
    Returns a list of validation error messages. Empty list means valid.
    This implementation covers the specific requirements of our schemas:
    - type checking
    - required fields
    - pattern matching for strings
    - numeric range checks
    - array item validation
    """
    errors = []
    
    def check_type(value: Any, expected_type: str, path: str) -> bool:
        """Check if value matches expected JSON Schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            errors.append(f"{path}: Unknown type '{expected_type}'")
            return False
        
        if not isinstance(value, expected_python_type):
            # Special case: integer is also a number
            if expected_type == "number" and isinstance(value, int):
                return True
            errors.append(f"{path}: Expected {expected_type}, got {type(value).__name__}")
            return False
        return True
    
    def validate_object(obj: Dict[str, Any], schema: Dict[str, Any], path: str = ""):
        """Validate an object against a schema."""
        if not check_type(obj, "object", path):
            return
        
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in obj:
                errors.append(f"{path or 'root'}: Missing required field '{field}'")
        
        # Validate properties
        properties = schema.get("properties", {})
        for key, value in obj.items():
            field_path = f"{path}.{key}" if path else key
            
            if key in properties:
                field_schema = properties[key]
                validate_value(value, field_schema, field_path)
            elif not schema.get("additionalProperties", True):
                errors.append(f"{field_path}: Additional property not allowed")
    
    def validate_array(arr: List[Any], schema: Dict[str, Any], path: str):
        """Validate an array against a schema."""
        if not check_type(arr, "array", path):
            return
        
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(arr):
                item_path = f"{path}[{i}]"
                validate_value(item, items_schema, item_path)
    
    def validate_string(value: str, schema: Dict[str, Any], path: str):
        """Validate string-specific constraints."""
        pattern = schema.get("pattern")
        if pattern:
            import re
            if not re.match(pattern, value):
                errors.append(f"{path}: Value '{value}' does not match pattern '{pattern}'")
    
    def validate_numeric(value: float, schema: Dict[str, Any], path: str):
        """Validate numeric constraints."""
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: Value {value} is less than minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: Value {value} is greater than maximum {schema['maximum']}")
        if "minLength" in schema and isinstance(value, str) and len(value) < schema["minLength"]:
            errors.append(f"{path}: String length {len(value)} is less than minLength {schema['minLength']}")
        if "maxLength" in schema and isinstance(value, str) and len(value) > schema["maxLength"]:
            errors.append(f"{path}: String length {len(value)} is greater than maxLength {schema['maxLength']}")
    
    def validate_value(value: Any, schema: Dict[str, Any], path: str):
        """Dispatch validation based on schema type."""
        schema_type = schema.get("type")
        
        if schema_type == "object":
            validate_object(value, schema, path)
        elif schema_type == "array":
            validate_array(value, schema, path)
        elif schema_type == "string":
            check_type(value, "string", path)
            validate_string(value, schema, path)
        elif schema_type in ("integer", "number"):
            check_type(value, schema_type, path)
            validate_numeric(value, schema, path)
        elif schema_type == "boolean":
            check_type(value, "boolean", path)
        elif schema_type == "null":
            check_type(value, "null", path)
    
    validate_object(data, schema, path or "root")
    return errors


class AtomicGraphSchemaTest(unittest.TestCase):
    """Contract test for AtomicGraph schema."""
    
    def setUp(self):
        """Load the AtomicGraph schema."""
        self.schema = load_schema("atomic_graph.schema.yaml")
    
    def test_schema_exists(self):
        """Verify the AtomicGraph schema file exists and is valid YAML."""
        self.assertIsNotNone(self.schema)
        self.assertIn("title", self.schema)
        self.assertEqual(self.schema["title"], "AtomicGraph")
    
    def test_required_fields(self):
        """Verify all required fields are present in the schema."""
        required = self.schema.get("required", [])
        expected_required = [
            "graph_id", "atom_count", "edges", "node_features",
            "bond_cutoff", "source_file", "checksum"
        ]
        for field in expected_required:
            self.assertIn(field, required, f"Required field '{field}' missing from schema")
    
    def test_valid_sample(self):
        """Test a valid AtomicGraph sample against the schema."""
        valid_sample = {
            "graph_id": "atomic_graph_12345678",
            "atom_count": 64,
            "edges": [
                {"source": 0, "target": 1, "distance": 2.35},
                {"source": 0, "target": 2, "distance": 2.38}
            ],
            "node_features": {
                "0": {
                    "position": [0.0, 0.0, 0.0],
                    "degree": 4
                },
                "1": {
                    "position": [2.35, 0.0, 0.0],
                    "degree": 3
                }
            },
            "bond_cutoff": 3.0,
            "source_file": "data/raw/si_sample_001.xyz",
            "checksum": "a" * 64
        }
        
        errors = validate_against_schema(valid_sample, self.schema)
        self.assertEqual(errors, [], f"Valid sample failed validation: {errors}")
    
    def test_missing_required_field(self):
        """Test that missing required fields are caught."""
        invalid_sample = {
            "graph_id": "atomic_graph_12345678",
            "atom_count": 64,
            # Missing edges, node_features, etc.
        }
        
        errors = validate_against_schema(invalid_sample, self.schema)
        self.assertTrue(len(errors) > 0, "Should have detected missing required fields")
        self.assertTrue(any("Missing required field" in e for e in errors))
    
    def test_invalid_graph_id_pattern(self):
        """Test that invalid graph_id format is caught."""
        invalid_sample = {
            "graph_id": "invalid_id_format",
            "atom_count": 64,
            "edges": [],
            "node_features": {},
            "bond_cutoff": 3.0,
            "source_file": "test.xyz",
            "checksum": "a" * 64
        }
        
        errors = validate_against_schema(invalid_sample, self.schema)
        self.assertTrue(any("does not match pattern" in e for e in errors),
                      "Should detect invalid graph_id pattern")
    
    def test_checksum_format(self):
        """Test that invalid checksum format is caught."""
        invalid_sample = {
            "graph_id": "atomic_graph_12345678",
            "atom_count": 64,
            "edges": [],
            "node_features": {},
            "bond_cutoff": 3.0,
            "source_file": "test.xyz",
            "checksum": "short"
        }
        
        errors = validate_against_schema(invalid_sample, self.schema)
        self.assertTrue(any("does not match pattern" in e for e in errors),
                      "Should detect invalid checksum pattern")
    
    def test_atom_count_minimum(self):
        """Test that atom_count < 1 is caught."""
        invalid_sample = {
            "graph_id": "atomic_graph_12345678",
            "atom_count": 0,
            "edges": [],
            "node_features": {},
            "bond_cutoff": 3.0,
            "source_file": "test.xyz",
            "checksum": "a" * 64
        }
        
        errors = validate_against_schema(invalid_sample, self.schema)
        self.assertTrue(any("less than minimum" in e for e in errors),
                      "Should detect atom_count < 1")
    
    def test_edge_structure(self):
        """Test edge structure validation."""
        invalid_edge_sample = {
            "graph_id": "atomic_graph_12345678",
            "atom_count": 64,
            "edges": [
                {"source": 0, "distance": 2.35}  # Missing 'target'
            ],
            "node_features": {},
            "bond_cutoff": 3.0,
            "source_file": "test.xyz",
            "checksum": "a" * 64
        }
        
        errors = validate_against_schema(invalid_edge_sample, self.schema)
        # This should catch missing required field in edge items
        self.assertTrue(len(errors) > 0, "Should detect missing edge fields")

class ThermalSampleSchemaTest(unittest.TestCase):
    """Contract test for ThermalSample schema."""
    
    def setUp(self):
        """Load the ThermalSample schema."""
        self.schema = load_schema("thermal_sample.schema.yaml")
    
    def test_schema_exists(self):
        """Verify the ThermalSample schema file exists."""
        self.assertIsNotNone(self.schema)
        self.assertEqual(self.schema["title"], "ThermalSample")
    
    def test_required_fields(self):
        """Verify required fields in ThermalSample schema."""
        required = self.schema.get("required", [])
        expected = ["sample_id", "graph_id", "thermal_conductivity", "metadata"]
        for field in expected:
            self.assertIn(field, required)

class GNNOutputSchemaTest(unittest.TestCase):
    """Contract test for GNNOutput schema."""
    
    def setUp(self):
        """Load the GNNOutput schema."""
        self.schema = load_schema("gnn_output.schema.yaml")
    
    def test_schema_exists(self):
        """Verify the GNNOutput schema file exists."""
        self.assertIsNotNone(self.schema)
        self.assertEqual(self.schema["title"], "GNNOutput")
    
    def test_required_fields(self):
        """Verify required fields in GNNOutput schema."""
        required = self.schema.get("required", [])
        expected = ["run_id", "model_checkpoint", "predictions", "loss_history"]
        for field in expected:
            self.assertIn(field, required)

def run_all_tests():
    """Run all contract tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(AtomicGraphSchemaTest))
    suite.addTests(loader.loadTestsFromTestCase(ThermalSampleSchemaTest))
    suite.addTests(loader.loadTestsFromTestCase(GNNOutputSchemaTest))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)