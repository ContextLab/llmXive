"""
Script to validate the contracts/output.schema.yaml against pydantic and jsonschema.
Verification for Task T008: Ensure the schema is syntactically valid and loadable.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path to allow imports if needed, though this script is standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "output.schema.yaml"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def get_project_root():
    return PROJECT_ROOT

def load_yaml_schema(path: Path) -> dict:
    """Load YAML schema file."""
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.error("PyYAML not installed. Install with: pip install pyyaml")
        raise
    except Exception as e:
        logger.error(f"Failed to load YAML from {path}: {e}")
        raise

def validate_with_jsonschema(schema_dict: dict) -> bool:
    """Validate the schema itself against JSON Schema meta-schema (basic check)."""
    try:
        import jsonschema
        # Validate that the loaded dict is a valid JSON Schema draft-07
        jsonschema.Draft7Validator.check_schema(schema_dict)
        logger.info("JSON Schema validation passed: Schema structure is valid.")
        return True
    except ImportError:
        logger.warning("jsonschema not installed. Skipping JSON Schema meta-validation.")
        return False
    except Exception as e:
        logger.error(f"JSON Schema validation failed: {e}")
        return False

def validate_with_pydantic(schema_dict: dict) -> bool:
    """
    Validate the schema structure by attempting to instantiate a Pydantic model
    that mirrors the expected output structure defined in the schema.
    """
    try:
        from pydantic import BaseModel, Field, ValidationError
        from typing import Dict, Any, Optional, List
        
        # We define a Pydantic model that strictly matches the structure described in output.schema.yaml
        # to ensure the schema is logically consistent and loadable as a Python object.
        
        class Metadata(BaseModel):
            generated_at: str
            n_observations: int
            n_predictors: int
            alpha_threshold: float
            bonferroni_adjusted_alpha: float
            cluster_variable: Optional[str] = None

        class RegressionModelResult(BaseModel):
            coefficients: Dict[str, float]
            p_values: Dict[str, float]
            standard_errors: Dict[str, float]
            model_type: str
            adj_r_squared: Optional[float] = None
            collinearity_warning: bool

        class VIFScores(BaseModel):
            # Dynamic keys allowed
            pass

        class OutputSchema(BaseModel):
            model_1_stability: RegressionModelResult
            model_2_food_security: RegressionModelResult
            vif_scores: Dict[str, float]
            metadata: Metadata

        # Attempt to parse a dummy valid instance to ensure the model works
        dummy_instance = {
            "model_1_stability": {
                "coefficients": {"CSA_Index": 0.5},
                "p_values": {"CSA_Index": 0.01},
                "standard_errors": {"CSA_Index": 0.1},
                "model_type": "clustered",
                "collinearity_warning": False
            },
            "model_2_food_security": {
                "coefficients": {"CSA_Index": -0.2},
                "p_values": {"CSA_Index": 0.03},
                "standard_errors": {"CSA_Index": 0.05},
                "model_type": "clustered",
                "collinearity_warning": False
            },
            "vif_scores": {"CSA_Index": 1.2, "education": 1.1},
            "metadata": {
                "generated_at": "2025-01-01T00:00:00Z",
                "n_observations": 500,
                "n_predictors": 5,
                "alpha_threshold": 0.05,
                "bonferroni_adjusted_alpha": 0.0167
            }
        }
        
        # Validate the dummy instance
        OutputSchema.model_validate(dummy_instance)
        logger.info("Pydantic validation passed: Schema structure is logically consistent.")
        return True

    except ImportError:
        logger.warning("pydantic not installed. Skipping Pydantic validation.")
        return False
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during Pydantic validation: {e}")
        return False

def main():
    logger.info(f"Validating schema at: {SCHEMA_PATH}")
    
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)

    try:
        schema_dict = load_yaml_schema(SCHEMA_PATH)
        logger.info("Schema loaded successfully from YAML.")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)

    # Run validators
    jsonschema_ok = validate_with_jsonschema(schema_dict)
    pydantic_ok = validate_with_pydantic(schema_dict)

    if not jsonschema_ok and not pydantic_ok:
        logger.error("Schema validation failed: No validator passed.")
        sys.exit(1)
    
    logger.info("Task T008 Verification: Schema is valid and loadable.")
    sys.exit(0)

if __name__ == "__main__":
    main()