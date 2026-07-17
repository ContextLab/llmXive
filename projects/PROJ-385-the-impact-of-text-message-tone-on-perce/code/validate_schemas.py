import json
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any
import jsonschema
from jsonschema import validate, ValidationError

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(json_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate JSON data against a schema."""
    try:
        validate(instance=json_data, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation Error: {e.message}")
        return False

def main():
    """Main function to validate schemas."""
    base_path = Path(__file__).parent.parent / "specs" / "001-text-tone-emotional-support" / "contracts"
    
    schemas = {
        "stimulus": base_path / "stimulus.schema.yaml",
        "rating": base_path / "rating.schema.yaml",
        "analysis_result": base_path / "analysis_result.schema.yaml"
    }

    # Sample data for validation
    sample_data = {
        "stimulus": {
            "stimulus_id": "S001",
            "text": "Hey, how are you doing? :)",
            "emoji_level": "low",
            "punctuation_type": "standard",
            "length_category": "short",
            "context": "friend"
        },
        "rating": {
            "participant_id": "P-AB123456",
            "stimulus_id": "S001",
            "relationship_context": "friend",
            "rating": 5,
            "timestamp": "2023-10-27T10:00:00Z"
        },
        "analysis_result": {
            "model_id": "M001",
            "fixed_effects": {
                "emoji_level": {"estimate": 0.5, "std_err": 0.1},
                "punctuation_type": {"estimate": 0.2, "std_err": 0.05}
            },
            "random_effects": {
                "Participant": 0.3,
                "Stimulus": 0.1
            },
            "p_values": {
                "emoji_level": 0.001,
                "punctuation_type": 0.04
            },
            "post_hoc_results": [
                {"comparison": "high_vs_none", "estimate": 0.8, "p_value": 0.02}
            ],
            "timestamp": "2023-10-27T12:00:00Z"
        }
    }

    all_valid = True
    for name, schema_path in schemas.items():
        print(f"Validating {name} schema...")
        schema = load_schema(schema_path)
        is_valid = validate_json_against_schema(sample_data[name], schema)
        if not is_valid:
            all_valid = False
            print(f"  -> {name} schema validation FAILED")
        else:
            print(f"  -> {name} schema validation PASSED")

    if all_valid:
        print("\nAll schemas are valid.")
        sys.exit(0)
    else:
        print("\nSome schemas are invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()