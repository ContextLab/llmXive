"""
Contract tests for project schemas.
Validates that data artifacts conform to the JSON Schema definitions in contracts/.
"""
import json
import logging
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Add project root to path for imports if running as script
if __package__ is None:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema not installed. Contract tests will be skipped.")

# Constants
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
TEST_DATA_DIR = Path(__file__).parent.parent / "contract_data"

logger = logging.getLogger(__name__)


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_atomic_graph(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Contract test for AtomicGraph schema.
    Verifies structure, types, and constraints.
    """
    if not HAS_JSONSCHEMA:
        logger.warning("Skipping validation due to missing jsonschema library.")
        return

    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info("AtomicGraph schema validation passed.")
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"AtomicGraph schema validation failed: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        raise AssertionError(f"AtomicGraph contract test failed: {e.message}") from e


class TestAtomicGraphSchema(unittest.TestCase):
    """Contract tests for the AtomicGraph schema."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema("atomic_graph")
        # Ensure test data directory exists (created by ingestion tasks)
        if not TEST_DATA_DIR.exists():
            TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def test_schema_structure(self):
        """Verify the schema itself is valid JSON Schema."""
        self.assertIn("type", self.schema)
        self.assertEqual(self.schema["type"], "object")
        self.assertIn("required", self.schema)
        self.assertIn("properties", self.schema)

    def test_valid_atomic_graph(self):
        """Test a minimal valid AtomicGraph instance."""
        valid_graph = {
            "graph_id": "test_001",
            "node_count": 2,
            "edge_count": 1,
            "bond_cutoff": 3.0,
            "nodes": [
                {
                    "node_id": 0,
                    "element": "Si",
                    "position": [0.0, 0.0, 0.0],
                    "degree": 1
                },
                {
                    "node_id": 1,
                    "element": "Si",
                    "position": [2.35, 0.0, 0.0],
                    "degree": 1
                }
            ],
            "edges": [
                {
                    "source": 0,
                    "target": 1,
                    "distance": 2.35
                }
            ],
            "metadata": {
                "source_file": "test.xyz",
                "timestamp": "2023-01-01T00:00:00Z",
                "software": "ase"
            }
        }
        validate_atomic_graph(valid_graph, self.schema)

    def test_missing_required_field(self):
        """Test that missing required fields fail validation."""
        invalid_graph = {
            "graph_id": "test_002",
            # Missing node_count, edges, etc.
        }
        with self.assertRaises(AssertionError):
            validate_atomic_graph(invalid_graph, self.schema)

    def test_invalid_element(self):
        """Test that non-Si elements fail validation."""
        graph = {
            "graph_id": "test_003",
            "node_count": 1,
            "edge_count": 0,
            "bond_cutoff": 3.0,
            "nodes": [
                {
                    "node_id": 0,
                    "element": "C",  # Invalid
                    "position": [0.0, 0.0, 0.0],
                    "degree": 0
                }
            ],
            "edges": [],
            "metadata": {}
        }
        with self.assertRaises(AssertionError):
            validate_atomic_graph(graph, self.schema)

    def test_negative_distance(self):
        """Test that negative edge distance fails validation."""
        graph = {
            "graph_id": "test_004",
            "node_count": 2,
            "edge_count": 1,
            "bond_cutoff": 3.0,
            "nodes": [
                {"node_id": 0, "element": "Si", "position": [0.0, 0.0, 0.0], "degree": 1},
                {"node_id": 1, "element": "Si", "position": [1.0, 0.0, 0.0], "degree": 1}
            ],
            "edges": [
                {"source": 0, "target": 1, "distance": -1.0}  # Invalid
            ],
            "metadata": {}
        }
        with self.assertRaises(AssertionError):
            validate_atomic_graph(graph, self.schema)

    def test_malformed_position(self):
        """Test that malformed position array fails validation."""
        graph = {
            "graph_id": "test_005",
            "node_count": 1,
            "edge_count": 0,
            "bond_cutoff": 3.0,
            "nodes": [
                {"node_id": 0, "element": "Si", "position": [0.0, 0.0], "degree": 0}  # Missing Z
            ],
            "edges": [],
            "metadata": {}
        }
        with self.assertRaises(AssertionError):
            validate_atomic_graph(graph, self.schema)


def run_tests():
    """Run all contract tests."""
    if not HAS_JSONSCHEMA:
        print("ERROR: jsonschema library is required for contract tests.")
        print("Install it via: pip install jsonschema")
        return False

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestAtomicGraphSchema))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = run_tests()
    sys.exit(0 if success else 1)