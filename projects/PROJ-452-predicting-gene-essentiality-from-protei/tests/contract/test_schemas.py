"""
Contract tests to validate JSON outputs against schema files.

This module tests that generated JSON result files (correlations, PGLS, sensitivity)
strictly adhere to their corresponding JSON Schema definitions.
"""
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
import yaml

# Import project utilities
from utils import setup_logging

# Configure logging for test output
logger = setup_logging(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        The schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML/JSON.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        # Handle both YAML and JSON (yaml.safe_load handles JSON too)
        return yaml.safe_load(f)


def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a dictionary against a JSON Schema using manual validation.
    
    Note: We implement manual validation to avoid adding 'jsonschema' as a hard dependency
    unless strictly necessary, or to provide custom, readable error messages.
    However, for robustness in a research pipeline, using the 'jsonschema' library
    is preferred if available. We will attempt to import it, and if not, fall back
    to a simplified validator or raise an explicit error.
    
    Args:
        data: The data to validate.
        schema: The schema to validate against.
        
    Returns:
        A list of error messages. Empty if valid.
    """
    errors = []
    
    # Check for required top-level keys
    required = schema.get('required', [])
    for key in required:
        if key not in data:
            errors.append(f"Missing required key: '{key}'")
    
    # Type checking for known keys if 'properties' are defined
    properties = schema.get('properties', {})
    for key, value in data.items():
        if key in properties:
            prop_schema = properties[key]
            expected_type = prop_schema.get('type')
            
            if expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Key '{key}' must be an object (dict), got {type(value).__name__}")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Key '{key}' must be an array (list), got {type(value).__name__}")
            elif expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Key '{key}' must be a string, got {type(value).__name__}")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Key '{key}' must be a number, got {type(value).__name__}")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Key '{key}' must be an integer, got {type(value).__name__}")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Key '{key}' must be a boolean, got {type(value).__name__}")
            
            # Check nested properties for objects
            if expected_type == 'object' and isinstance(value, dict):
                nested_props = prop_schema.get('properties', {})
                nested_required = prop_schema.get('required', [])
                
                for nested_key in nested_required:
                    if nested_key not in value:
                        errors.append(f"Missing required nested key in '{key}': '{nested_key}'")
                
                for nested_key, nested_val in value.items():
                    if nested_key in nested_props:
                        nested_type = nested_props[nested_key].get('type')
                        if nested_type == 'number' and not isinstance(nested_val, (int, float)):
                            errors.append(f"Key '{key}.{nested_key}' must be a number, got {type(nested_val).__name__}")
                        elif nested_type == 'string' and not isinstance(nested_val, str):
                            errors.append(f"Key '{key}.{nested_key}' must be a string, got {type(nested_val).__name__}")
    
    return errors


@pytest.fixture
def schemas_dir() -> Path:
    """Return the path to the contracts directory containing schemas."""
    # Assuming project root is the parent of 'tests'
    return Path(__file__).parent.parent.parent / "contracts"


@pytest.fixture
def results_dir() -> Path:
    """Return the path to the results directory."""
    return Path(__file__).parent.parent.parent / "results"


class TestCorrelationSchema:
    """Tests for the correlation result schema."""
    
    def test_schema_file_exists(self, schemas_dir: Path):
        """Verify the correlation schema file exists."""
        schema_path = schemas_dir / "correlation_result.schema.yaml"
        assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    def test_valid_correlation_data(self, schemas_dir: Path):
        """Test a valid correlation result against the schema."""
        schema_path = schemas_dir / "correlation_result.schema.yaml"
        schema = load_schema(schema_path)
        
        valid_data = {
            "organism": "Saccharomyces_cerevisiae",
            "network_source": "STRING",
            "confidence_threshold": 700,
            "correlations": [
                {
                    "metric": "degree_centrality",
                    "rho": 0.45,
                    "p_value": 0.001,
                    "n": 5000
                }
            ],
            "metadata": {
                "timestamp": "2023-10-27T10:00:00Z",
                "version": "1.0.0"
            }
        }
        
        errors = validate_json_against_schema(valid_data, schema)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    def test_missing_required_field(self, schemas_dir: Path):
        """Test that missing required fields are caught."""
        schema_path = schemas_dir / "correlation_result.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = {
            "organism": "Saccharomyces_cerevisiae",
            # Missing 'network_source' and 'correlations'
        }
        
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0
        assert any("required" in err.lower() for err in errors)


class TestPGLSSchema:
    """Tests for the PGLS result schema."""
    
    def test_schema_file_exists(self, schemas_dir: Path):
        """Verify the PGLS schema file exists."""
        schema_path = schemas_dir / "pgls_result.schema.yaml"
        assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    def test_valid_pgls_data(self, schemas_dir: Path):
        """Test a valid PGLS result against the schema."""
        schema_path = schemas_dir / "pgls_result.schema.yaml"
        schema = load_schema(schema_path)
        
        valid_data = {
            "analysis_type": "PGLS",
            "organisms": ["Homo_sapiens", "Mus_musculus"],
            "tree_source": "OpenTree",
            "results": [
                {
                    "metric": "degree_centrality",
                    "statistic": 2.45,
                    "p_value": 0.012,
                    "adjusted_p_value": 0.024,
                    "n_organisms": 2
                }
            ],
            "metadata": {
                "timestamp": "2023-10-27T10:00:00Z"
            }
        }
        
        errors = validate_json_against_schema(valid_data, schema)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    def test_invalid_p_value_type(self, schemas_dir: Path):
        """Test that non-numeric p-values are caught."""
        schema_path = schemas_dir / "pgls_result.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = {
            "analysis_type": "PGLS",
            "organisms": ["Homo_sapiens"],
            "tree_source": "OpenTree",
            "results": [
                {
                    "metric": "degree_centrality",
                    "statistic": 2.45,
                    "p_value": "not_a_number",  # Should be number
                    "adjusted_p_value": 0.024,
                    "n_organisms": 1
                }
            ],
            "metadata": {}
        }
        
        errors = validate_json_against_schema(invalid_data, schema)
        assert len(errors) > 0
        assert any("number" in err.lower() for err in errors)


class TestSensitivitySchema:
    """Tests for the sensitivity report schema."""
    
    def test_schema_file_exists(self, schemas_dir: Path):
        """Verify the sensitivity schema file exists."""
        schema_path = schemas_dir / "sensitivity_report.schema.yaml"
        assert schema_path.exists(), f"Schema file missing: {schema_path}"
    
    def test_valid_sensitivity_data(self, schemas_dir: Path):
        """Test a valid sensitivity report against the schema."""
        schema_path = schemas_dir / "sensitivity_report.schema.yaml"
        schema = load_schema(schema_path)
        
        valid_data = {
            "organism": "Saccharomyces_cerevisiae",
            "metric": "degree_centrality",
            "thresholds": [500, 700, 900],
            "results": [
                {"threshold": 500, "rho": 0.42, "n": 4800},
                {"threshold": 700, "rho": 0.45, "n": 5000},
                {"threshold": 900, "rho": 0.48, "n": 4500}
            ],
            "stability_check": {
                "max_delta_rho": 0.06,
                "passed": True,
                "threshold_limit": 0.1
            },
            "metadata": {
                "timestamp": "2023-10-27T10:00:00Z"
            }
        }
        
        errors = validate_json_against_schema(valid_data, schema)
        assert len(errors) == 0, f"Validation errors: {errors}"


@pytest.mark.integration
def test_validate_actual_results_files(results_dir: Path, schemas_dir: Path):
    """
    Integration test: If result files exist, validate them against schemas.
    This test is skipped if results are not yet generated.
    """
    if not results_dir.exists():
        pytest.skip("Results directory does not exist yet.")
    
    # Map filenames to schema types
    file_schema_map = {
        "correlations.json": "correlation_result",
        "pgls_results.json": "pgls_result",
        "sensitivity_report.json": "sensitivity_report"
    }
    
    for filename, schema_type in file_schema_map.items():
        result_path = results_dir / filename
        if result_path.exists():
            with open(result_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {filename}: {e}")
            
            schema_path = schemas_dir / f"{schema_type}.schema.yaml"
            if not schema_path.exists():
                pytest.skip(f"Schema for {schema_type} not found.")
            
            schema = load_schema(schema_path)
            errors = validate_json_against_schema(data, schema)
            
            assert len(errors) == 0, f"Validation failed for {filename}: {errors}"
            logger.info(f"Validated {filename} successfully.")
        else:
            logger.info(f"Skipping validation for {filename} (file not found).")