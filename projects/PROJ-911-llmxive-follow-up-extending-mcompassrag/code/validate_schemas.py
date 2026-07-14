"""
Schema validation utilities for llmXive artifacts.
Provides functions to validate dataset and output artifacts against their YAML schemas.
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

# Import path constants
from code.config import CONTRACTS_DIR, DATA_DIR

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema file from the contracts directory."""
    schema_path = Path(CONTRACTS_DIR) / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_artifact(artifact_path: Path, schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an artifact file against a specified schema.
    
    Args:
        artifact_path: Path to the artifact file (JSON or YAML)
        schema_name: Name of the schema file in contracts/
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Load schema
        schema = load_schema(schema_name)
        
        # Load artifact
        if artifact_path.suffix == '.json':
            with open(artifact_path, 'r', encoding='utf-8') as f:
                artifact_data = json.load(f)
        elif artifact_path.suffix in ['.yaml', '.yml']:
            with open(artifact_path, 'r', encoding='utf-8') as f:
                artifact_data = yaml.safe_load(f)
        else:
            return False, f"Unsupported file format: {artifact_path.suffix}"
        
        # Validate
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(artifact_data))
        
        if errors:
            error_msgs = [f"  - {e.message} (at {list(e.path)})" for e in errors]
            return False, "\n".join(error_msgs)
        
        return True, None
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def validate_all_outputs() -> bool:
    """
    Validate all generated output artifacts against their schemas.
    
    Returns:
        True if all validations pass, False otherwise.
    """
    results = []
    
    # Define artifact to schema mappings
    validations = [
        ("data/processed/graphs.json", "output.schema.yaml"),
        ("data/processed/features.csv", None),  # CSV validation is separate
        ("data/results/retrieval_scores.csv", None),
        ("data/results/metrics.json", "output.schema.yaml"),
        ("data/results/correlation.csv", None),
    ]
    
    for artifact_path, schema_name in validations:
        full_path = Path(DATA_DIR) / artifact_path
        
        if not full_path.exists():
            print(f"  [SKIP] {artifact_path} (not found)")
            continue
        
        if schema_name is None:
            # Skip CSV validation for now (could add CSV schema later)
            print(f"  [SKIP] {artifact_path} (no schema defined)")
            continue
        
        is_valid, error = validate_artifact(full_path, schema_name)
        status = "PASS" if is_valid else "FAIL"
        print(f"  [{status}] {artifact_path}")
        
        if not is_valid:
            print(f"      Error: {error}")
            results.append(False)
        else:
            results.append(True)
    
    return all(results)

if __name__ == "__main__":
    print("Validating artifacts against schemas...")
    success = validate_all_outputs()
    if success:
        print("\nAll validations passed.")
    else:
        print("\nSome validations failed.")
        exit(1)
