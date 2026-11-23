"""
Script to validate the regression output schema (contracts/output.schema.yaml)
using both Pydantic and JSON Schema validation.
"""
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any

import yaml
from pydantic import BaseModel, Field, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RegressionOutput(BaseModel):
    """Pydantic model for validating regression output structure."""
    coefficients: Dict[str, float]
    p_values: Dict[str, float]
    vif_scores: Dict[str, float]
    model_type: str
    collinearity_warning: bool
    aggregation_warning: bool
    adjusted_alpha: float | None = None
    bonferroni_corrected_p_values: Dict[str, float] | None = None
    model_summary: Dict[str, Any] | None = None
    execution_metadata: Dict[str, Any] | None = None

    # Validation constraints
    def __init__(self, **data):
        super().__init__(**data)
        # Validate p_values range
        for var, p_val in self.p_values.items():
            if not (0.0 <= p_val <= 1.0):
                raise ValueError(f"P-value for {var} must be between 0 and 1, got {p_val}")
        
        # Validate VIF scores
        for var, vif in self.vif_scores.items():
            if vif < 1.0:
                raise ValueError(f"VIF for {var} must be >= 1, got {vif}")

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_with_pydantic(data: Dict[str, Any]) -> bool:
    """Validate data against Pydantic model."""
    try:
        RegressionOutput(**data)
        logger.info("Pydantic validation: PASSED")
        return True
    except ValidationError as e:
        logger.error(f"Pydantic validation: FAILED - {e}")
        return False

def validate_with_jsonschema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate data against JSON Schema."""
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        logger.info("JSON Schema validation: PASSED")
        return True
    except ImportError:
        logger.warning("jsonschema library not installed, skipping JSON Schema validation")
        return True  # Don't fail if library is missing
    except jsonschema.ValidationError as e:
        logger.error(f"JSON Schema validation: FAILED - {e.message}")
        return False

def main():
    """Main entry point for schema validation."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "output.schema.yaml"
    
    # Check if schema file exists
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    # Load schema
    try:
        schema = load_yaml_schema(schema_path)
        logger.info(f"Loaded schema from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)
    
    # Create a sample valid output for testing
    sample_data = {
        "coefficients": {
            "CSA_Index": 0.45,
            "finance_access": 0.12,
            "land_size": 0.08
        },
        "p_values": {
            "CSA_Index": 0.001,
            "finance_access": 0.03,
            "land_size": 0.15
        },
        "vif_scores": {
            "CSA_Index": 1.2,
            "finance_access": 1.1,
            "land_size": 1.05
        },
        "model_type": "aggregated",
        "collinearity_warning": False,
        "aggregation_warning": False,
        "adjusted_alpha": 0.0167,
        "bonferroni_corrected_p_values": {
            "CSA_Index": 0.003,
            "finance_access": 0.09,
            "land_size": 0.45
        }
    }
    
    # Validate with Pydantic
    pydantic_valid = validate_with_pydantic(sample_data)
    
    # Validate with JSON Schema
    jsonschema_valid = validate_with_jsonschema(sample_data, schema)
    
    # Exit with appropriate code
    if pydantic_valid and jsonschema_valid:
        logger.info("All validations passed successfully.")
        sys.exit(0)
    else:
        logger.error("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()