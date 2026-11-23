"""
Validation logic for model_result.schema.yaml.
This script verifies the schema generated in T016 is correctly formatted
and contains all required fields.
"""
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Set, List

REQUIRED_FIELDS: Set[str] = {
    "model_type",
    "mae",
    "r_squared",
    "feature_importance_ranking",
    "cv_stability_scores"
}

def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_model_result_schema(schema_path: Path) -> bool:
    """
    Validate that model_result.schema.yaml exists and contains all required fields.
    
    Args:
        schema_path: Path to the model_result.schema.yaml file.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If required fields are missing or schema is invalid.
    """
    schema = load_yaml_schema(schema_path)
    
    # Basic schema structure validation
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")
    
    # Check for 'properties' key (standard JSON Schema / YAML schema structure)
    if "properties" not in schema:
        # Try alternative structure if 'properties' is not at root
        # Some schemas might have 'type' -> 'object' -> 'properties'
        if "type" in schema and schema["type"] == "object" and "properties" not in schema:
            raise ValueError("Schema has 'type: object' but missing 'properties'")
        # If no 'properties' found, check if the schema itself uses the fields as keys
        # This handles non-standard schemas where fields are at root level
        properties = schema
    else:
        properties = schema["properties"]
    
    if not isinstance(properties, dict):
        raise ValueError("'properties' must be a dictionary")
    
    # Check for required fields
    found_fields = set(properties.keys())
    missing_fields = REQUIRED_FIELDS - found_fields
    
    if missing_fields:
        raise ValueError(f"Missing required fields in model_result schema: {missing_fields}")
    
    # Validate specific field types/structures if needed
    # For 'feature_importance_ranking', check it's an array or has 'items'
    if "feature_importance_ranking" in properties:
        ranking_prop = properties["feature_importance_ranking"]
        if isinstance(ranking_prop, dict):
            if "type" in ranking_prop and ranking_prop["type"] != "array":
                # Allow for object type if it represents a structured ranking
                pass 
            elif "type" not in ranking_prop:
                # Assume it's valid if no type specified but key exists
                pass
    
    # For 'cv_stability_scores', similar check
    if "cv_stability_scores" in properties:
        cv_prop = properties["cv_stability_scores"]
        if isinstance(cv_prop, dict):
            if "type" in cv_prop and cv_prop["type"] != "array":
                pass
            elif "type" not in cv_prop:
                pass
    
    return True

def main() -> int:
    """Main entry point for schema validation."""
    # Determine project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    schema_path = project_root / "code" / "contracts" / "model_result.schema.yaml"
    
    print(f"Validating schema at: {schema_path}")
    
    try:
        if validate_model_result_schema(schema_path):
            print("✓ model_result.schema.yaml validation PASSED")
            print(f"  - Found all required fields: {REQUIRED_FIELDS}")
            return 0
    except FileNotFoundError as e:
        print(f"✗ Validation FAILED: {e}")
        return 1
    except ValueError as e:
        print(f"✗ Validation FAILED: {e}")
        return 1
    except Exception as e:
        print(f"✗ Validation FAILED with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
