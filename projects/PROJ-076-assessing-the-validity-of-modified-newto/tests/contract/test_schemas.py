"""
Contract tests for data and fit result schemas.

This module validates that the generated contract schemas (T048, T049)
are correctly structured and that the codebase adheres to them.

Dependencies:
  - T048: contracts/dataset.schema.yaml
  - T049: contracts/fit_results.schema.yaml
"""
import os
import sys
import yaml
import json
import jsonschema
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import get_logger, ensure_directory

# Configure logging
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Paths to schema files
DATASET_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
FIT_RESULTS_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "fit_results.schema.yaml"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema at {schema_path} must be a YAML dictionary")
    
    return schema

def validate_sample_against_schema(
    sample_data: Dict[str, Any], 
    schema: Dict[str, Any], 
    schema_name: str
) -> bool:
    """
    Validate sample data against a JSON schema.
    
    Returns True if valid, raises ValidationError if invalid.
    """
    try:
        jsonschema.validate(instance=sample_data, schema=schema)
        logger.info(f"Sample data validated successfully against {schema_name}")
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation failed for {schema_name}: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        raise

def test_dataset_schema_exists() -> None:
    """Test that the dataset schema file exists."""
    assert DATASET_SCHEMA_PATH.exists(), f"Dataset schema missing: {DATASET_SCHEMA_PATH}"
    logger.info(f"Dataset schema found: {DATASET_SCHEMA_PATH}")

def test_fit_results_schema_exists() -> None:
    """Test that the fit results schema file exists."""
    assert FIT_RESULTS_SCHEMA_PATH.exists(), f"Fit results schema missing: {FIT_RESULTS_SCHEMA_PATH}"
    logger.info(f"Fit results schema found: {FIT_RESULTS_SCHEMA_PATH}")

def test_dataset_schema_structure() -> None:
    """Test that the dataset schema has valid JSON Schema structure."""
    schema = load_schema(DATASET_SCHEMA_PATH)
    
    # Basic JSON Schema checks
    assert "$schema" in schema or "type" in schema, "Schema must define type or $schema"
    assert "properties" in schema, "Schema must define properties"
    
    # Check for expected galaxy data fields based on FR-002, FR-003
    required_fields = ["galaxy_id", "radial_distance", "velocity", "velocity_uncertainty", "inclination"]
    schema_props = schema["properties"]
    
    for field in required_fields:
        assert field in schema_props, f"Required field '{field}' missing from dataset schema"
    
    logger.info("Dataset schema structure is valid and contains required fields")

def test_fit_results_schema_structure() -> None:
    """Test that the fit results schema has valid JSON Schema structure."""
    schema = load_schema(FIT_RESULTS_SCHEMA_PATH)
    
    # Basic JSON Schema checks
    assert "$schema" in schema or "type" in schema, "Schema must define type or $schema"
    assert "properties" in schema, "Schema must define properties"
    
    # Check for expected fit result fields based on FR-007, FR-009
    required_fields = ["galaxy_id", "model_type", "reduced_chi2", "aic", "bic", "parameters"]
    schema_props = schema["properties"]
    
    for field in required_fields:
        assert field in schema_props, f"Required field '{field}' missing from fit results schema"
    
    logger.info("Fit results schema structure is valid and contains required fields")

def test_dataset_schema_valid_json() -> None:
    """Test that the dataset schema is valid JSON Schema."""
    schema = load_schema(DATASET_SCHEMA_PATH)
    
    # jsonschema library will raise if schema is invalid
    # We create a dummy validator to test the schema itself
    jsonschema.Draft7Validator.check_schema(schema)
    logger.info("Dataset schema is valid JSON Schema (Draft 7)")

def test_fit_results_schema_valid_json() -> None:
    """Test that the fit results schema is valid JSON Schema."""
    schema = load_schema(FIT_RESULTS_SCHEMA_PATH)
    
    # jsonschema library will raise if schema is invalid
    jsonschema.Draft7Validator.check_schema(schema)
    logger.info("Fit results schema is valid JSON Schema (Draft 7)")

def test_dataset_schema_with_sample_data() -> None:
    """Test dataset schema against a realistic sample galaxy record."""
    schema = load_schema(DATASET_SCHEMA_PATH)
    
    sample_galaxy = {
        "galaxy_id": "UGC_0001",
        "radial_distance": [1.0, 2.0, 3.0, 4.0, 5.0],
        "velocity": [100.0, 120.0, 130.0, 135.0, 138.0],
        "velocity_uncertainty": [5.0, 5.0, 5.0, 5.0, 5.0],
        "inclination": 45.0,
        "inclination_uncertainty": 2.0,
        "notes": "Test galaxy"
    }
    
    validate_sample_against_schema(sample_galaxy, schema, "dataset.schema.yaml")

def test_fit_results_schema_with_sample_data() -> None:
    """Test fit results schema against a realistic sample fit record."""
    schema = load_schema(FIT_RESULTS_SCHEMA_PATH)
    
    sample_fit = {
        "galaxy_id": "UGC_0001",
        "model_type": "MOND_simple",
        "reduced_chi2": 1.23,
        "aic": 150.5,
        "bic": 160.2,
        "parameters": {
            "M_L": 0.8,
            "a_0": 1.2e-10
        },
        "fit_status": "success",
        "convergence_iterations": 12
    }
    
    validate_sample_against_schema(sample_fit, schema, "fit_results.schema.yaml")

def run_all_tests() -> None:
    """Run all schema validation tests."""
    logger.info("Starting schema validation tests...")
    
    tests = [
        test_dataset_schema_exists,
        test_fit_results_schema_exists,
        test_dataset_schema_structure,
        test_fit_results_schema_structure,
        test_dataset_schema_valid_json,
        test_fit_results_schema_valid_json,
        test_dataset_schema_with_sample_data,
        test_fit_results_schema_with_sample_data
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {e}")
            failed += 1
    
    logger.info(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()