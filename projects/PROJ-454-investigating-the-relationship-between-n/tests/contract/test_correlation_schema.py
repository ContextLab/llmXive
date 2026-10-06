"""
Contract test for correlation_results.schema.yaml validation.

This test ensures that the regression analysis output file
(data/processed/correlation_results_fdr.csv) conforms to the
defined JSON schema.
"""
import os
import sys
import json
import csv
import logging
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path to import utils if needed, though this is a standalone contract test
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import jsonschema
from jsonschema import validate, ValidationError

# Setup logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SCHEMA_PATH = project_root / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts" / "correlation_results.schema.yaml"
# We expect the output to be a CSV that we will convert to a dict structure for validation
# Or if the task produces a JSON, we validate directly. 
# Based on T021, the output is correlation_results_fdr.csv.
# We will construct a representative JSON structure from a CSV row to validate against the schema.
# However, the schema is for the *entire* result object (list of results + metadata).
# So we need to either:
# 1. Validate the CSV structure against a CSV schema (if one exists, but T018 asks for this JSON schema)
# 2. Create a synthetic valid JSON instance to prove the schema works (Contract Test)
# 3. Load the real CSV, transform to JSON, and validate.

# Given the task is "Contract test for correlation_results.schema.yaml", 
# we must ensure the schema exists and can validate a valid instance.
# We will generate a valid instance based on the schema definition and validate it.
# Then we will attempt to load the real file if it exists and validate that too.

def load_schema():
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    # Simple YAML loader for this specific file (no external dependencies like pyyaml if not needed, 
    # but the project has pyyaml in requirements.txt per T001)
    try:
        import yaml
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    except ImportError:
        # Fallback if pyyaml is not installed in the test environment, though it should be
        logger.warning("PyYAML not found. Attempting manual parsing or failing.")
        # In a real CI, we assume pyyaml is present.
        raise

def generate_valid_instance():
    """Generate a valid instance of the correlation results structure."""
    return {
        "results": [
            {
                "predictor": "sample_entropy_theta",
                "band": "theta",
                "metric": "sample_entropy",
                "coef": 0.45,
                "std_err": 0.12,
                "p_value": 0.002,
                "p_value_fdr": 0.008,
                "vif": 1.2,
                "partial_r": 0.35,
                "effect_size_class": "medium",
                "significant": True
            },
            {
                "predictor": "age",
                "band": "N/A",
                "metric": "N/A",
                "coef": -0.02,
                "std_err": 0.01,
                "p_value": 0.04,
                "p_value_fdr": 0.06,
                "vif": 1.5,
                "partial_r": -0.15,
                "effect_size_class": "small",
                "significant": False
            }
        ],
        "metadata": {
            "model_formula": "wcst_perseverative_errors ~ sample_entropy_theta + sample_entropy_alpha + age + education",
            "n_observations": 42,
            "n_predictors": 4,
            "fdr_method": "benjamini_hochberg",
            "vif_threshold": 5.0,
            "ap_en_dropped": False,
            "timestamp": datetime.now().isoformat()
        }
    }

def test_schema_exists():
    """Test that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"
    logger.info("Schema file exists.")

def test_schema_is_valid_json():
    """Test that the schema file is valid YAML/JSON."""
    schema = load_schema()
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "type" in schema, "Schema must have a 'type' field"
    assert schema["type"] == "object", "Schema root must be an object"
    logger.info("Schema is valid YAML/JSON.")

def test_schema_validates_correct_instance():
    """Test that a correctly formed instance passes validation."""
    schema = load_schema()
    instance = generate_valid_instance()
    
    try:
        validate(instance=instance, schema=schema)
        logger.info("Valid instance passed schema validation.")
    except ValidationError as e:
        logger.error(f"Valid instance failed validation: {e.message}")
        raise AssertionError(f"Valid instance failed schema validation: {e.message}")

def test_schema_rejects_invalid_instance():
    """Test that an invalid instance fails validation."""
    schema = load_schema()
    # Missing required field 'results'
    invalid_instance = {
        "metadata": {
            "model_formula": "...",
            "n_observations": 10,
            "n_predictors": 2,
            "fdr_method": "benjamini_hochberg",
            "vif_threshold": 5.0,
            "ap_en_dropped": False,
            "timestamp": "2023-01-01T00:00:00"
        }
    }
    
    try:
        validate(instance=invalid_instance, schema=schema)
        raise AssertionError("Invalid instance should have failed validation")
    except ValidationError:
        logger.info("Invalid instance correctly rejected by schema.")

def test_csv_conversion_if_exists():
    """
    If the real output file exists, convert it to the expected JSON structure and validate.
    This is an integration check within the contract test.
    """
    output_csv = project_root / "data" / "processed" / "correlation_results_fdr.csv"
    if not output_csv.exists():
        logger.warning(f"Output CSV not found at {output_csv}. Skipping conversion validation.")
        return

    # We need to construct the JSON structure that matches the schema from the CSV.
    # The CSV likely has columns: predictor, band, metric, coef, std_err, p_value, p_value_fdr, vif, partial_r, effect_size_class
    # We need to aggregate metadata from somewhere or assume defaults for this test.
    # Since the schema requires a 'metadata' object, and a CSV row doesn't contain it,
    # we will construct a minimal metadata object for the validation.
    
    schema = load_schema()
    
    results = []
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types
            try:
                entry = {
                    "predictor": row['predictor'],
                    "band": row['band'],
                    "metric": row['metric'],
                    "coef": float(row['coef']),
                    "std_err": float(row['std_err']),
                    "p_value": float(row['p_value']),
                    "p_value_fdr": float(row['p_value_fdr']),
                    "vif": float(row['vif']),
                    "partial_r": float(row['partial_r']),
                    "effect_size_class": row['effect_size_class'],
                    "significant": float(row['p_value_fdr']) < 0.05
                }
                results.append(entry)
            except (KeyError, ValueError) as e:
                logger.error(f"Error parsing CSV row: {row}. Error: {e}")
                raise

    if not results:
        logger.warning("No results found in CSV file.")
        return

    instance = {
        "results": results,
        "metadata": {
            "model_formula": "Derived from CSV context or default",
            "n_observations": len(results), # Approximate
            "n_predictors": len(results),
            "fdr_method": "benjamini_hochberg",
            "vif_threshold": 5.0,
            "ap_en_dropped": False,
            "timestamp": datetime.now().isoformat()
        }
    }

    try:
        validate(instance=instance, schema=schema)
        logger.info(f"Real CSV data ({len(results)} rows) validated against schema.")
    except ValidationError as e:
        logger.error(f"Real CSV data failed schema validation: {e.message}")
        # This is a hard failure if the real data doesn't match the contract
        raise AssertionError(f"Real data validation failed: {e.message}")

def run_all_tests():
    """Run all contract tests."""
    logger.info("Starting Contract Tests for correlation_results.schema.yaml")
    test_schema_exists()
    test_schema_is_valid_json()
    test_schema_validates_correct_instance()
    test_schema_rejects_invalid_instance()
    test_csv_conversion_if_exists()
    logger.info("All Contract Tests Passed.")

if __name__ == "__main__":
    run_all_tests()