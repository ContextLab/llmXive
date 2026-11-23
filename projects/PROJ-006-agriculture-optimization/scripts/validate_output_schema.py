"""
Script to validate contracts/output.schema.yaml against pydantic/jsonschema.
Ensures the regression output schema is syntactically valid and loadable.
"""
import os
import sys
import logging
from pathlib import Path
import json
import yaml

# Attempt to import jsonschema, fallback to basic pydantic validation if missing
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema not installed. Using basic YAML/Pydantic validation only.")

# Attempt to import pydantic
try:
    from pydantic import BaseModel, Field, ValidationError
    from typing import Dict, Any, List, Optional, Union
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    logging.error("pydantic is required for validation. Please install it.")
    sys.exit(1)


class Model1Stability(BaseModel):
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    bonferroni_p_values: Dict[str, float]
    std_errors: Dict[str, float]
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    f_p_value: float


class Model2FoodSecurity(BaseModel):
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    bonferroni_p_values: Dict[str, float]
    std_errors: Dict[str, float]
    r_squared: float
    adj_r_squared: float
    f_statistic: float
    f_p_value: float


class Diagnostics(BaseModel):
    vif_scores: Dict[str, Dict[str, float]]
    collinearity_warnings: List[str]
    heteroskedasticity_test: Optional[Dict[str, Any]] = None


class SensitivityResult(BaseModel):
    threshold: float
    model: str
    coefficient_csa_index: float
    p_value: float
    std_err: float


class RegressionOutputSchema(BaseModel):
    version: str
    description: str
    metadata: Dict[str, Any]
    models: Dict[str, Any]
    diagnostics: Diagnostics
    sensitivity: List[SensitivityResult]


def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Assume project root is 2 levels up from scripts/
    return current.parent.parent


def load_yaml_schema(schema_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_with_pydantic(schema_dict: dict) -> bool:
    """
    Validate the loaded YAML schema structure against the Pydantic model.
    Since the schema file defines the *structure* of future data, we validate
    that the schema file itself contains the required keys defined in the spec.
    """
    required_top_keys = ['version', 'description', 'metadata', 'models', 'diagnostics', 'sensitivity']
    missing_keys = [k for k in required_top_keys if k not in schema_dict]
    
    if missing_keys:
        logging.error(f"Schema missing required top-level keys: {missing_keys}")
        return False

    # Validate specific nested structures expected by the Pydantic model
    if 'models' in schema_dict:
        if 'model_1_stability' not in schema_dict['models']:
            logging.error("Schema missing 'model_1_stability' definition")
            return False
        if 'model_2_food_security' not in schema_dict['models']:
            logging.error("Schema missing 'model_2_food_security' definition")
            return False
    
    if 'diagnostics' in schema_dict:
        if 'vif_scores' not in schema_dict['diagnostics']:
            logging.error("Schema missing 'vif_scores' in diagnostics")
            return False

    logging.info("Schema structure validated against Pydantic expectations.")
    return True


def validate_with_jsonschema(schema_dict: dict) -> bool:
    """Validate the schema file itself against a meta-schema (optional)."""
    if not HAS_JSONSCHEMA:
        logging.info("Skipping JSONSchema validation (jsonschema library not installed).")
        return True
    
    # Basic check: ensure the schema is a valid JSON object
    try:
        jsonschema.Draft7Validator.check_schema(schema_dict)
        logging.info("Schema is valid JSONSchema Draft7.")
        return True
    except jsonschema.exceptions.SchemaError as e:
        logging.error(f"Schema is not a valid JSONSchema: {e}")
        return False


def main():
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "output.schema.yaml"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logging.info(f"Validating schema: {schema_path}")

    try:
        schema_dict = load_yaml_schema(schema_path)
    except Exception as e:
        logging.error(f"Failed to load schema: {e}")
        sys.exit(1)

    # 1. Validate against Pydantic structure expectations
    if not validate_with_pydantic(schema_dict):
        logging.error("Pydantic validation failed.")
        sys.exit(1)

    # 2. Validate against JSONSchema (if available)
    if not validate_with_jsonschema(schema_dict):
        logging.error("JSONSchema validation failed.")
        sys.exit(1)

    logging.info("Validation successful. contracts/output.schema.yaml is valid.")
    sys.exit(0)


if __name__ == "__main__":
    main()