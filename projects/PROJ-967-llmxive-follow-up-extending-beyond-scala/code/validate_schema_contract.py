"""
Validation script for T001d: Create schema contracts.
Validates that `contracts/dataset.schema.yaml` is syntactically correct YAML
and contains all required fields defined in the task specification.
"""
import sys
import yaml
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent / "contracts" / "dataset.schema.yaml"

REQUIRED_TOP_LEVEL = [
    "prompt",
    "image_path",
    "teacher_logits",
    "student_scalar",
    "human_annotations",
    "primary_dimension"
]

REQUIRED_HUMAN_DIMS = [
    "Alignment",
    "Realism",
    "Aesthetics",
    "Plausibility"
]

def validate_schema():
    """
    Validates the YAML file exists, is parseable, and contains required keys.
    Raises ValueError if validation fails.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at: {SCHEMA_PATH}")

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in {SCHEMA_PATH}: {e}")

    if not isinstance(schema, dict):
        raise ValueError("Root of schema.yaml must be a YAML mapping (dict).")

    # Check top-level required fields
    if "properties" not in schema:
        raise ValueError("Schema is missing 'properties' key.")

    props = schema["properties"]
    missing_top = [k for k in REQUIRED_TOP_LEVEL if k not in props]
    if missing_top:
        raise ValueError(f"Missing required top-level properties: {missing_top}")

    # Check human_annotations structure
    if "human_annotations" not in props:
        raise ValueError("Missing 'human_annotations' property.")

    ha_props = props["human_annotations"].get("properties", {})
    missing_dims = [d for d in REQUIRED_HUMAN_DIMS if d not in ha_props]
    if missing_dims:
        raise ValueError(f"Missing required dimensions in human_annotations: {missing_dims}")

    # Check types
    if props.get("prompt", {}).get("type") != "string":
        raise ValueError("prompt must be type 'string'")
    if props.get("student_scalar", {}).get("type") != "number":
        raise ValueError("student_scalar must be type 'number'")
    if props.get("primary_dimension", {}).get("type") != "string":
        raise ValueError("primary_dimension must be type 'string'")

    return True

def main():
    print(f"Validating schema contract at: {SCHEMA_PATH}")
    try:
        validate_schema()
        print("✅ Schema validation PASSED.")
        print("   - All required top-level fields present.")
        print("   - All required human annotation dimensions present.")
        print("   - YAML syntax is valid.")
        return 0
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ Schema validation FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
