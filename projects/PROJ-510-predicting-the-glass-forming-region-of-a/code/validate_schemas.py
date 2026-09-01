"""
Schema Validation Module for Glass Forming Region Prediction Pipeline.

This module validates that all generated data artifacts match the defined
JSON Schema contracts in the contracts/ directory.
"""

import yaml
import json
import jsonschema
import os
import sys
import logging
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACTS_DIR = os.path.join(PROJECT_ROOT, 'contracts')
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'data', 'models')


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.

    Args:
        schema_name: Name of the schema file (e.g., 'dataset.schema.yaml')

    Returns:
        Dictionary containing the schema definition
    """
    schema_path = os.path.join(CONTRACTS_DIR, schema_name)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            return json.load(f)


def validate_json_against_schema(
    data_path: str,
    schema: Dict[str, Any],
    schema_name: str
) -> Tuple[bool, List[str]]:
    """
    Validate a JSON file against a schema.

    Args:
        data_path: Path to the JSON file to validate
        schema: The schema dictionary to validate against
        schema_name: Name of the schema for logging purposes

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if not os.path.exists(data_path):
        errors.append(f"Data file not found: {data_path}")
        return False, errors

    try:
        with open(data_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {data_path}: {str(e)}")
        return False, errors

    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info(f"✓ {os.path.basename(data_path)} validates against {schema_name}")
        return True, []
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"Schema validation error in {data_path}: {e.message}")
        errors.append(f"  Path: {list(e.path)}")
        return False, errors


def validate_csv_against_schema(
    data_path: str,
    schema: Dict[str, Any],
    schema_name: str
) -> Tuple[bool, List[str]]:
    """
    Validate a CSV file against a schema (checks column names and types).

    Args:
        data_path: Path to the CSV file to validate
        schema: The schema dictionary to validate against
        schema_name: Name of the schema for logging purposes

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    import pandas as pd
    errors = []

    if not os.path.exists(data_path):
        errors.append(f"Data file not found: {data_path}")
        return False, errors

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        errors.append(f"Error reading CSV {data_path}: {str(e)}")
        return False, errors

    # Get required properties from schema
    if 'properties' not in schema:
        logger.warning(f"No properties defined in schema {schema_name}, skipping column validation")
        return True, []

    required_columns = set(schema['properties'].keys())
    actual_columns = set(df.columns)

    # Check for missing columns
    missing_cols = required_columns - actual_columns
    if missing_cols:
        errors.append(f"Missing columns in {data_path}: {missing_cols}")

    # Check for unexpected columns (optional, depending on schema)
    # extra_cols = actual_columns - required_columns
    # if extra_cols:
    #     logger.warning(f"Extra columns in {data_path}: {extra_cols}")

    # Validate data types for each column
    for col_name, col_schema in schema['properties'].items():
        if col_name not in df.columns:
            continue  # Already reported above

        expected_type = col_schema.get('type')
        actual_dtype = df[col_name].dtype

        type_mapping = {
            'string': 'object',
            'integer': 'int64',
            'number': 'float64',
            'boolean': 'bool'
        }

        expected_dtype = type_mapping.get(expected_type)
        if expected_dtype and actual_dtype != expected_dtype:
            # Allow some flexibility (e.g., int32 vs int64)
            if expected_type == 'integer' and 'int' in str(actual_dtype):
                continue
            if expected_type == 'number' and 'float' in str(actual_dtype):
                continue
            if expected_type == 'string' and actual_dtype == 'object':
                continue

            errors.append(
                f"Type mismatch in {data_path}, column '{col_name}': "
                f"expected {expected_type} ({expected_dtype}), got {actual_dtype}"
            )

    if not errors:
        logger.info(f"✓ {os.path.basename(data_path)} validates against {schema_name}")

    return len(errors) == 0, errors


def validate_schemas() -> bool:
    """
    Main validation function. Checks all data artifacts against their schemas.

    Returns:
        True if all validations pass, False otherwise
    """
    logger.info("Starting schema validation...")

    all_valid = True
    validation_results = []

    # Define validations to perform
    validations = [
        {
            'name': 'Processed Alloys (Raw)',
            'data_path': os.path.join(PROCESSED_DATA_DIR, 'processed_alloys_raw.csv'),
            'schema_name': 'dataset.schema.yaml',
            'validator': validate_csv_against_schema
        },
        {
            'name': 'Processed Alloys (Final)',
            'data_path': os.path.join(PROCESSED_DATA_DIR, 'processed_alloys.csv'),
            'schema_name': 'dataset.schema.yaml',
            'validator': validate_csv_against_schema
        },
        {
            'name': 'CV Metrics',
            'data_path': os.path.join(MODELS_DIR, 'cv_metrics.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        },
        {
            'name': 'Null Model RMSE',
            'data_path': os.path.join(MODELS_DIR, 'null_model_rmse.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        },
        {
            'name': 'Statistical Comparison',
            'data_path': os.path.join(MODELS_DIR, 'statistical_comparison.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        },
        {
            'name': 'Feature Importance',
            'data_path': os.path.join(PROCESSED_DATA_DIR, 'feature_importance.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        },
        {
            'name': 'Sensitivity Status',
            'data_path': os.path.join(PROCESSED_DATA_DIR, 'sensitivity_status.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        },
        {
            'name': 'Collinearity Decision',
            'data_path': os.path.join(PROCESSED_DATA_DIR, 'collinearity_decision.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        },
        {
            'name': 'Collinearity Report',
            'data_path': os.path.join(PROCESSED_DATA_DIR, 'collinearity_report.json'),
            'schema_name': 'model_output.schema.yaml',
            'validator': validate_json_against_schema
        }
    ]

    # Load schemas
    try:
        dataset_schema = load_schema('dataset.schema.yaml')
        model_output_schema = load_schema('model_output.schema.yaml')
    except Exception as e:
        logger.error(f"Failed to load schemas: {str(e)}")
        return False

    # Run validations
    for validation in validations:
        schema_to_use = dataset_schema if 'processed_alloys' in validation['data_path'] else model_output_schema

        is_valid, errors = validation['validator'](
            validation['data_path'],
            schema_to_use,
            validation['schema_name']
        )

        validation_results.append({
            'name': validation['name'],
            'valid': is_valid,
            'errors': errors
        })

        if not is_valid:
            all_valid = False
            logger.error(f"✗ {validation['name']} FAILED:")
            for error in errors:
                logger.error(f"  - {error}")
        else:
            logger.info(f"✓ {validation['name']} PASSED")

    # Summary
    logger.info("\n" + "="*50)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*50)

    passed = sum(1 for v in validation_results if v['valid'])
    total = len(validation_results)

    logger.info(f"Passed: {passed}/{total}")

    if all_valid:
        logger.info("✓ ALL VALIDATIONS PASSED")
        return True
    else:
        logger.error("✗ SOME VALIDATIONS FAILED")
        failed_items = [v['name'] for v in validation_results if not v['valid']]
        logger.error(f"Failed items: {failed_items}")
        return False


if __name__ == '__main__':
    success = validate_schemas()
    sys.exit(0 if success else 1)