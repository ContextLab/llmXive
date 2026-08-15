import yaml
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_ceramic_entry_schema(schema_path: Path) -> bool:
    """
    Validate ceramic_entry.schema.yaml.
    Checks for required fields: composition, weibull_modulus, sample_count,
    is_range_flag, range_original, primary_anion_cation_group, sintering_temp,
    is_imputed, mean_atomic_radius, electronegativity_std, valence_electron_concentration.
    """
    required_fields = {
        'composition',
        'weibull_modulus',
        'sample_count',
        'is_range_flag',
        'range_original',
        'primary_anion_cation_group',
        'sintering_temp',
        'is_imputed',
        'mean_atomic_radius',
        'electronegativity_std',
        'valence_electron_concentration'
    }

    schema = load_yaml_schema(schema_path)
    
    # Navigate to properties (standard JSON Schema structure)
    properties = schema.get('properties', {})
    
    found_fields = set(properties.keys())
    missing_fields = required_fields - found_fields
    
    if missing_fields:
        raise ValueError(
            f"ceramic_entry.schema.yaml is missing required fields: {missing_fields}"
        )
    
    print(f"✓ ceramic_entry.schema.yaml validated successfully. Found {len(found_fields)} fields.")
    return True

def validate_model_result_schema(schema_path: Path) -> bool:
    """
    Validate model_result.schema.yaml.
    Checks for required fields: model_type, mae, r_squared, feature_importance_ranking, cv_stability_scores.
    """
    required_fields = {
        'model_type',
        'mae',
        'r_squared',
        'feature_importance_ranking',
        'cv_stability_scores'
    }

    schema = load_yaml_schema(schema_path)
    
    # Navigate to properties
    properties = schema.get('properties', {})
    
    found_fields = set(properties.keys())
    missing_fields = required_fields - found_fields
    
    if missing_fields:
        raise ValueError(
            f"model_result.schema.yaml is missing required fields: {missing_fields}"
        )
    
    print(f"✓ model_result.schema.yaml validated successfully. Found {len(found_fields)} fields.")
    return True

def main() -> int:
    """Main entry point for schema validation."""
    base_path = Path(__file__).parent
    ceramic_schema = base_path / "ceramic_entry.schema.yaml"
    model_schema = base_path / "model_result.schema.yaml"

    try:
        validate_ceramic_entry_schema(ceramic_schema)
        validate_model_result_schema(model_schema)
        print("All schema validations passed.")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
