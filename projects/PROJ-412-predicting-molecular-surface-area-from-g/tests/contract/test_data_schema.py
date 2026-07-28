"""
Contract test for data schema validation.

Validates that the processed molecular data conforms to the static schema
defined in data/schemas/static_schema.yaml. This ensures input format
compliance before further processing or model training.

This test is part of User Story 1 (Data Ingestion and Preprocessing).
"""

import os
import sys
import json
import logging
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Schema validation constants
SCHEMA_PATH = project_root / "data" / "schemas" / "static_schema.yaml"

# Regex pattern for SMILES validation (from schema)
SMILES_PATTERN = re.compile(r"^[A-Za-z0-9@+\-\[\]\(\)\{\}\.,#=\\$%&/\\<>]+$")

class SchemaValidator:
    """
    Validates data records against the static schema.
    Implements the schema validation logic defined in static_schema.yaml.
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize the validator with a schema file.
        
        Args:
            schema_path: Path to the YAML schema file. Defaults to SCHEMA_PATH.
        """
        self.schema_path = schema_path or SCHEMA_PATH
        self.schema = self._load_schema()
        self.errors: List[str] = []
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load and parse the YAML schema file."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        try:
            import yaml
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            raise
    
    def validate_record(self, record: Dict[str, Any], record_id: str = "unknown") -> bool:
        """
        Validate a single data record against the schema.
        
        Args:
            record: The data record to validate.
            record_id: Identifier for the record (for error reporting).
        
        Returns:
            True if valid, False otherwise.
        """
        self.errors = []
        is_valid = True
        
        # Check required fields
        required_fields = self.schema.get('required', [])
        for field in required_fields:
            if field not in record:
                self.errors.append(f"[{record_id}] Missing required field: {field}")
                is_valid = False
        
        if not is_valid:
            return False
        
        # Validate each field according to schema
        properties = self.schema.get('properties', {})
        
        # Validate smiles
        if 'smiles' in properties and 'smiles' in record:
            if not self._validate_smiles(record['smiles'], record_id):
                is_valid = False
        
        # Validate node_features
        if 'node_features' in properties and 'node_features' in record:
            if not self._validate_node_features(record['node_features'], record_id):
                is_valid = False
        
        # Validate edge_features
        if 'edge_features' in properties and 'edge_features' in record:
            if not self._validate_edge_features(record['edge_features'], record_id):
                is_valid = False
        
        # Validate surface_area
        if 'surface_area' in properties and 'surface_area' in record:
            if not self._validate_surface_area(record['surface_area'], record_id):
                is_valid = False
        
        # Validate molecular_weight
        if 'molecular_weight' in properties and 'molecular_weight' in record:
            if not self._validate_molecular_weight(record['molecular_weight'], record_id):
                is_valid = False
        
        # Validate metadata if present
        if 'metadata' in record:
            if not self._validate_metadata(record['metadata'], record_id):
                is_valid = False
        
        return is_valid
    
    def _validate_smiles(self, smiles: Any, record_id: str) -> bool:
        """Validate SMILES string format."""
        if not isinstance(smiles, str):
            self.errors.append(f"[{record_id}] smiles must be a string, got {type(smiles)}")
            return False
        
        if len(smiles) < 1:
            self.errors.append(f"[{record_id}] smiles must have minLength 1")
            return False
        
        if not SMILES_PATTERN.match(smiles):
            self.errors.append(f"[{record_id}] SMILES format invalid: {smiles}")
            return False
        
        return True
    
    def _validate_node_features(self, features: Any, record_id: str) -> bool:
        """Validate node_features array structure."""
        if not isinstance(features, list):
            self.errors.append(f"[{record_id}] node_features must be an array")
            return False
        
        if len(features) < 1:
            self.errors.append(f"[{record_id}] node_features minItems is 1")
            return False
        
        for i, node_vec in enumerate(features):
            if not isinstance(node_vec, list):
                self.errors.append(f"[{record_id}] node_features[{i}] must be an array")
                return False
            
            if len(node_vec) < 1:
                self.errors.append(f"[{record_id}] node_features[{i}] minItems is 1")
                return False
            
            for j, val in enumerate(node_vec):
                if not isinstance(val, (int, float)):
                    self.errors.append(f"[{record_id}] node_features[{i}][{j}] must be a number")
                    return False
        
        return True
    
    def _validate_edge_features(self, features: Any, record_id: str) -> bool:
        """Validate edge_features array structure."""
        if not isinstance(features, list):
            self.errors.append(f"[{record_id}] edge_features must be an array")
            return False
        
        if len(features) < 0:
            self.errors.append(f"[{record_id}] edge_features minItems is 0")
            return False
        
        for i, edge_vec in enumerate(features):
            if not isinstance(edge_vec, list):
                self.errors.append(f"[{record_id}] edge_features[{i}] must be an array")
                return False
            
            if len(edge_vec) < 1:
                self.errors.append(f"[{record_id}] edge_features[{i}] minItems is 1")
                return False
            
            for j, val in enumerate(edge_vec):
                if not isinstance(val, (int, float)):
                    self.errors.append(f"[{record_id}] edge_features[{i}][{j}] must be a number")
                    return False
        
        return True
    
    def _validate_surface_area(self, value: Any, record_id: str) -> bool:
        """Validate surface_area numeric value."""
        if not isinstance(value, (int, float)):
            self.errors.append(f"[{record_id}] surface_area must be a number, got {type(value)}")
            return False
        
        if value < 0:
            self.errors.append(f"[{record_id}] surface_area minimum is 0, got {value}")
            return False
        
        return True
    
    def _validate_molecular_weight(self, value: Any, record_id: str) -> bool:
        """Validate molecular_weight numeric value."""
        if not isinstance(value, (int, float)):
            self.errors.append(f"[{record_id}] molecular_weight must be a number, got {type(value)}")
            return False
        
        if value < 0:
            self.errors.append(f"[{record_id}] molecular_weight minimum is 0, got {value}")
            return False
        
        return True
    
    def _validate_metadata(self, metadata: Any, record_id: str) -> bool:
        """Validate optional metadata object."""
        if not isinstance(metadata, dict):
            self.errors.append(f"[{record_id}] metadata must be an object")
            return False
        
        # Validate specific metadata fields if present
        if 'source' in metadata and not isinstance(metadata['source'], str):
            self.errors.append(f"[{record_id}] metadata.source must be a string")
            return False
        
        if 'processed_at' in metadata:
            # Basic ISO 8601 validation
            processed_at = metadata['processed_at']
            if not isinstance(processed_at, str):
                self.errors.append(f"[{record_id}] metadata.processed_at must be a string")
                return False
            
            # Check for basic date-time format
            iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
            if not iso_pattern.match(processed_at):
                self.errors.append(f"[{record_id}] metadata.processed_at must be ISO 8601 format")
                return False
        
        if 'atom_count' in metadata:
            if not isinstance(metadata['atom_count'], int) or metadata['atom_count'] < 1:
                self.errors.append(f"[{record_id}] metadata.atom_count must be integer >= 1")
                return False
        
        if 'bond_count' in metadata:
            if not isinstance(metadata['bond_count'], int) or metadata['bond_count'] < 0:
                self.errors.append(f"[{record_id}] metadata.bond_count must be integer >= 0")
                return False
        
        return True
    
    def get_errors(self) -> List[str]:
        """Return list of validation errors."""
        return self.errors.copy()


class TestDataSchema(unittest.TestCase):
    """
    Contract tests for data schema validation.
    
    Tests that the processed molecular data conforms to the expected schema
    before further processing or model training.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.validator = SchemaValidator()
        cls.test_records = cls._generate_test_records()
    
    @classmethod
    def _generate_test_records(cls) -> List[Dict[str, Any]]:
        """Generate test records for schema validation."""
        return [
            # Valid record 1 - Simple molecule
            {
                "smiles": "CCO",
                "node_features": [
                    [6.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [6.0, 3.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [8.0, 3.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                ],
                "edge_features": [
                    [1.0, 0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0, 0.0]
                ],
                "surface_area": 28.54,
                "molecular_weight": 46.07,
                "metadata": {
                    "source": "ZINC15",
                    "processed_at": "2023-10-27T10:00:00Z",
                    "rdkit_version": "2023.3.1",
                    "conformer_method": "ETKDGv3",
                    "atom_count": 3,
                    "bond_count": 2
                }
            },
            # Valid record 2 - Molecule without metadata
            {
                "smiles": "c1ccccc1",
                "node_features": [
                    [6.0, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0] for _ in range(6)
                ],
                "edge_features": [
                    [1.5, 0.0, 0.0, 1.0] for _ in range(6)
                ],
                "surface_area": 95.2,
                "molecular_weight": 78.11
            },
            # Valid record 3 - Molecule with empty edge_features
            {
                "smiles": "[He]",
                "node_features": [
                    [2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                ],
                "edge_features": [],
                "surface_area": 1.2,
                "molecular_weight": 4.00
            }
        ]
    
    def test_schema_file_exists(self):
        """Test that the schema file exists."""
        self.assertTrue(SCHEMA_PATH.exists(), f"Schema file not found: {SCHEMA_PATH}")
    
    def test_schema_is_valid_yaml(self):
        """Test that the schema file is valid YAML."""
        try:
            import yaml
            with open(SCHEMA_PATH, 'r') as f:
                schema = yaml.safe_load(f)
            self.assertIsInstance(schema, dict)
            self.assertIn('required', schema)
            self.assertIn('properties', schema)
        except Exception as e:
            self.fail(f"Failed to parse schema YAML: {e}")
    
    def test_required_fields_defined(self):
        """Test that all required fields are defined in schema."""
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_fields = schema.get('required', [])
        expected_fields = ['smiles', 'node_features', 'edge_features', 'surface_area', 'molecular_weight']
        
        for field in expected_fields:
            self.assertIn(field, required_fields, f"Required field '{field}' missing from schema")
    
    def test_validate_valid_record_1(self):
        """Test validation of a valid record with metadata."""
        record = self.test_records[0]
        is_valid = self.validator.validate_record(record, "test_1")
        
        self.assertTrue(is_valid, f"Valid record failed validation: {self.validator.get_errors()}")
        self.assertEqual(len(self.validator.get_errors()), 0)
    
    def test_validate_valid_record_2(self):
        """Test validation of a valid record without metadata."""
        record = self.test_records[1]
        is_valid = self.validator.validate_record(record, "test_2")
        
        self.assertTrue(is_valid, f"Valid record failed validation: {self.validator.get_errors()}")
        self.assertEqual(len(self.validator.get_errors()), 0)
    
    def test_validate_valid_record_3(self):
        """Test validation of a valid record with empty edge features."""
        record = self.test_records[2]
        is_valid = self.validator.validate_record(record, "test_3")
        
        self.assertTrue(is_valid, f"Valid record failed validation: {self.validator.get_errors()}")
        self.assertEqual(len(self.validator.get_errors()), 0)
    
    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        invalid_record = {
            "smiles": "CCO",
            "node_features": [[6.0]],
            "edge_features": []
            # Missing: surface_area, molecular_weight
        }
        
        is_valid = self.validator.validate_record(invalid_record, "missing_fields")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("surface_area" in e for e in errors))
        self.assertTrue(any("molecular_weight" in e for e in errors))
    
    def test_validate_invalid_smiles_type(self):
        """Test validation fails when SMILES is not a string."""
        invalid_record = {
            "smiles": 12345,
            "node_features": [[6.0]],
            "edge_features": [],
            "surface_area": 28.54,
            "molecular_weight": 46.07
        }
        
        is_valid = self.validator.validate_record(invalid_record, "invalid_smiles_type")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("smiles must be a string" in e for e in errors))
    
    def test_validate_invalid_smiles_format(self):
        """Test validation fails when SMILES format is invalid."""
        invalid_record = {
            "smiles": "C@#$invalid",
            "node_features": [[6.0]],
            "edge_features": [],
            "surface_area": 28.54,
            "molecular_weight": 46.07
        }
        
        is_valid = self.validator.validate_record(invalid_record, "invalid_smiles_format")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("SMILES format invalid" in e for e in errors))
    
    def test_validate_empty_node_features(self):
        """Test validation fails when node_features is empty."""
        invalid_record = {
            "smiles": "CCO",
            "node_features": [],
            "edge_features": [],
            "surface_area": 28.54,
            "molecular_weight": 46.07
        }
        
        is_valid = self.validator.validate_record(invalid_record, "empty_node_features")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("node_features minItems is 1" in e for e in errors))
    
    def test_validate_negative_surface_area(self):
        """Test validation fails when surface_area is negative."""
        invalid_record = {
            "smiles": "CCO",
            "node_features": [[6.0]],
            "edge_features": [],
            "surface_area": -10.0,
            "molecular_weight": 46.07
        }
        
        is_valid = self.validator.validate_record(invalid_record, "negative_surface_area")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("surface_area minimum is 0" in e for e in errors))
    
    def test_validate_negative_molecular_weight(self):
        """Test validation fails when molecular_weight is negative."""
        invalid_record = {
            "smiles": "CCO",
            "node_features": [[6.0]],
            "edge_features": [],
            "surface_area": 28.54,
            "molecular_weight": -5.0
        }
        
        is_valid = self.validator.validate_record(invalid_record, "negative_mw")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("molecular_weight minimum is 0" in e for e in errors))
    
    def test_validate_invalid_node_feature_type(self):
        """Test validation fails when node feature contains non-numeric value."""
        invalid_record = {
            "smiles": "CCO",
            "node_features": [[6.0, "invalid", 3.0]],
            "edge_features": [],
            "surface_area": 28.54,
            "molecular_weight": 46.07
        }
        
        is_valid = self.validator.validate_record(invalid_record, "invalid_node_type")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("must be a number" in e for e in errors))
    
    def test_validate_invalid_metadata_format(self):
        """Test validation fails when metadata.processed_at is not ISO 8601."""
        invalid_record = {
            "smiles": "CCO",
            "node_features": [[6.0]],
            "edge_features": [],
            "surface_area": 28.54,
            "molecular_weight": 46.07,
            "metadata": {
                "processed_at": "not-a-date"
            }
        }
        
        is_valid = self.validator.validate_record(invalid_record, "invalid_metadata")
        self.assertFalse(is_valid)
        
        errors = self.validator.get_errors()
        self.assertTrue(any("metadata.processed_at must be ISO 8601" in e for e in errors) or 
                      any("metadata.processed_at must be a string" in e for e in errors))


def main():
    """Run the contract tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting data schema contract tests...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDataSchema)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"Tests run: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
