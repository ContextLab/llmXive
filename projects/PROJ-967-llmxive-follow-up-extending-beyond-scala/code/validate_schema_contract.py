"""
Validate that the dataset schema contract is syntactically correct and contains all required fields.
This script verifies the YAML structure and ensures it meets the T001d requirements.
"""
import sys
import yaml
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACT_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

REQUIRED_TOP_LEVEL_KEYS = {
    "version",
    "description",
    "fields",
    "validation_rules",
    "metadata"
}

REQUIRED_FIELDS = {
    "prompt",
    "image_path",
    "teacher_logits",
    "student_scalar",
    "human_annotations",
    "primary_dimension"
}

REQUIRED_FIELD_TYPES = {
    "prompt": "str",
    "image_path": "str",
    "teacher_logits": "list[float]",
    "student_scalar": "float",
    "human_annotations": "dict",
    "primary_dimension": "str"
}

def setup_logging():
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_schema(schema_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        return schema
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML syntax in schema: {e}")

def validate_schema_structure(schema: dict) -> bool:
    """Validate the top-level structure of the schema."""
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(schema.keys())
    if missing_keys:
        raise ValueError(f"Schema missing required top-level keys: {missing_keys}")
    return True

def validate_fields(schema: dict) -> bool:
    """Validate that all required fields are present and correctly typed."""
    fields = schema.get("fields", {})
    missing_fields = REQUIRED_FIELDS - set(fields.keys())
    if missing_fields:
        raise ValueError(f"Schema missing required fields: {missing_fields}")
    
    for field_name, expected_type in REQUIRED_FIELD_TYPES.items():
        actual_type = fields[field_name].get("type")
        if actual_type != expected_type:
            raise ValueError(
                f"Field '{field_name}' has type '{actual_type}', expected '{expected_type}'"
            )
    
    # Validate teacher_logits specifically
    teacher_logits_def = fields.get("teacher_logits", {})
    if teacher_logits_def.get("length") != 4:
        raise ValueError("teacher_logits must have length 4")
    
    # Validate human_annotations keys
    human_annotations_def = fields.get("human_annotations", {})
    if "keys" not in human_annotations_def:
        raise ValueError("human_annotations must define dimension keys")
    
    expected_dims = {"Alignment", "Realism", "Aesthetics", "Plausibility"}
    actual_dims = set(human_annotations_def["keys"].keys())
    if expected_dims != actual_dims:
        raise ValueError(
            f"human_annotations must contain dimensions: {expected_dims}, got {actual_dims}"
        )
    
    # Validate primary_dimension allowed values
    primary_dim_def = fields.get("primary_dimension", {})
    allowed_values = set(primary_dim_def.get("allowed_values", []))
    if expected_dims != allowed_values:
        raise ValueError(
            f"primary_dimension allowed_values must be {expected_dims}, got {allowed_values}"
        )
    
    return True

def validate_schema(schema_path: Path = None) -> bool:
    """Main validation function."""
    if schema_path is None:
        schema_path = CONTRACT_PATH
    
    logger = setup_logging()
    logger.info(f"Validating schema at: {schema_path}")
    
    # Load schema
    schema = load_schema(schema_path)
    logger.info("Schema loaded successfully")
    
    # Validate structure
    validate_schema_structure(schema)
    logger.info("Top-level structure validated")
    
    # Validate fields
    validate_fields(schema)
    logger.info("Field definitions validated")
    
    logger.info("Schema validation PASSED")
    return True

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="Validate dataset schema contract"
    )
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=None,
        help="Path to schema file (default: contracts/dataset.schema.yaml)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    schema_path = args.schema_path if args.schema_path else CONTRACT_PATH
    
    try:
        validate_schema(schema_path)
        print("SUCCESS: Schema contract is valid and complete.")
        sys.exit(0)
    except Exception as e:
        print(f"FAILURE: Schema validation failed - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
