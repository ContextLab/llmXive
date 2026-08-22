"""
Script to validate the regression output schema (contracts/output.schema.yaml)
using both Pydantic and jsonschema libraries.
"""
import json
import sys
import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, List, Optional
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Define Pydantic model matching the YAML schema structure
class RegressionOutputMetadata(BaseModel):
    timestamp: str
    n_observations: int
    n_features: int
    source_dataset: str
    model_formula: Optional[str] = None

class RegressionOutput(BaseModel):
    model_type: str
    adjusted_alpha: float
    bonferroni_corrected_p_values: Dict[str, float]
    coefficients: Dict[str, float]
    vif_scores: Dict[str, float]
    collinearity_warning: bool
    metadata: RegressionOutputMetadata

    model_config = {
        "json_schema_extra": {
            "additionalProperties": False
        }
    }

def load_yaml_schema(schema_path: Path) -> dict:
    """Load the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_with_pydantic(schema_path: Path) -> bool:
    """
    Validate that the schema structure is compatible with the Pydantic model.
    This checks that the schema can be parsed and that the Pydantic model
    is validly defined.
    """
    logger.info(f"Validating schema structure with Pydantic model: {schema_path}")
    
    try:
        # Load the schema to ensure it's valid YAML
        schema_dict = load_yaml_schema(schema_path)
        
        # Validate that required fields exist in the schema
        required_fields = [
            "model_type", "adjusted_alpha", "bonferroni_corrected_p_values",
            "coefficients", "vif_scores", "collinearity_warning", "metadata"
        ]
        
        schema_properties = schema_dict.get("properties", {})
        for field in required_fields:
            if field not in schema_properties:
                logger.error(f"Missing required field '{field}' in schema")
                return False
        
        # Create a sample valid output to test Pydantic validation
        sample_output = {
            "model_type": "aggregated",
            "adjusted_alpha": 0.0167,
            "bonferroni_corrected_p_values": {
                "CSA_Index": 0.034,
                "finance_access": 0.002
            },
            "coefficients": {
                "CSA_Index": 0.45,
                "finance_access": 0.12
            },
            "vif_scores": {
                "CSA_Index": 1.2,
                "finance_access": 1.1
            },
            "collinearity_warning": False,
            "metadata": {
                "timestamp": "2024-01-15T10:30:00Z",
                "n_observations": 500,
                "n_features": 2,
                "source_dataset": "data/processed/analysis_dataset.csv",
                "model_formula": "Stability_Score ~ CSA_Index + finance_access"
            }
        }
        
        # Validate sample against Pydantic model
        validated = RegressionOutput(**sample_output)
        logger.info("Pydantic model validation successful with sample data.")
        return True
        
    except ValidationError as e:
        logger.error(f"Pydantic validation error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Pydantic validation: {e}")
        return False

def validate_with_jsonschema(schema_path: Path) -> bool:
    """
    Validate that the schema file itself is a valid JSON Schema
    and can be used to validate data.
    """
    logger.info(f"Validating schema file with jsonschema library: {schema_path}")
    
    try:
        schema_dict = load_yaml_schema(schema_path)
        
        # Validate that the schema is a valid JSON Schema
        # This checks that required keywords are present
        if "$schema" not in schema_dict:
            logger.warning("Schema missing '$schema' keyword, but continuing...")
        
        if "type" not in schema_dict or schema_dict["type"] != "object":
            logger.error("Schema must define type as 'object'")
            return False
        
        if "properties" not in schema_dict:
            logger.error("Schema must define 'properties'")
            return False
        
        # Create a sample valid output to test JSON Schema validation
        sample_output = {
            "model_type": "aggregated",
            "adjusted_alpha": 0.0167,
            "bonferroni_corrected_p_values": {
                "CSA_Index": 0.034,
                "finance_access": 0.002
            },
            "coefficients": {
                "CSA_Index": 0.45,
                "finance_access": 0.12
            },
            "vif_scores": {
                "CSA_Index": 1.2,
                "finance_access": 1.1
            },
            "collinearity_warning": False,
            "metadata": {
                "timestamp": "2024-01-15T10:30:00Z",
                "n_observations": 500,
                "n_features": 2,
                "source_dataset": "data/processed/analysis_dataset.csv",
                "model_formula": "Stability_Score ~ CSA_Index + finance_access"
            }
        }
        
        # Validate sample against JSON Schema
        validate(instance=sample_output, schema=schema_dict)
        logger.info("JSON Schema validation successful with sample data.")
        return True
        
    except JsonSchemaValidationError as e:
        logger.error(f"JSON Schema validation error: {e.message}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during JSON Schema validation: {e}")
        return False

def main():
    """Main entry point for schema validation."""
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "contracts" / "output.schema.yaml"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Schema path: {schema_path}")
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        logger.info("Please ensure contracts/output.schema.yaml exists.")
        sys.exit(1)
    
    pydantic_valid = validate_with_pydantic(schema_path)
    jsonschema_valid = validate_with_jsonschema(schema_path)
    
    if pydantic_valid and jsonschema_valid:
        logger.info("SUCCESS: Schema validation passed with both Pydantic and jsonschema.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Schema validation failed.")
        if not pydantic_valid:
            logger.error("  - Pydantic validation failed")
        if not jsonschema_valid:
            logger.error("  - JSON Schema validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()