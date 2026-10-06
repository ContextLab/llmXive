import os
import sys
import json
import logging
from pathlib import Path
import jsonschema
from utils.logging_config import setup_general_logger

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for the validation script."""
    return setup_general_logger(name)

def load_schema(schema_path: Path) -> dict:
    """
    Load a JSON schema from a YAML or JSON file.
    Since the project uses .yaml for schemas, we support basic YAML parsing 
    by converting simple YAML structures or using a simple parser if yaml is available.
    However, to strictly adhere to dependencies without adding 'pyyaml' here if not needed,
    we assume the schema is valid JSON or we use a minimal yaml loader if installed.
    Given T001 pinned 'pyyaml==6.0.1', we can safely import it.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml is required to load .yaml schemas. Install it via requirements.txt.")

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in schema file {schema_path}: {e}")
    
    return schema

def validate_json_against_schema(json_path: Path, schema_path: Path, logger: logging.Logger) -> bool:
    """
    Validates a JSON file against a JSON schema.
    Returns True if valid, False if invalid.
    Logs the result.
    """
    if not json_path.exists():
        logger.error(f"Input JSON file not found: {json_path}")
        return False

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        return False

    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.info(f"Validation PASSED for {json_path.name} against {schema_path.name}")
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Validation FAILED for {json_path.name}: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        return False
    except jsonschema.SchemaError as e:
        logger.error(f"Invalid Schema in {schema_path.name}: {e.message}")
        return False

def main():
    """
    Main entry point for T032b.
    Validates data/processed/sensitivity_report.json against 
    specs/001-neural-entropy-cognitive-flexibility/contracts/output.schema.yaml
    and writes results to logs/validation_results_json.txt.
    """
    # Setup paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    json_path = project_root / "data" / "processed" / "sensitivity_report.json"
    schema_path = project_root / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts" / "output.schema.yaml"
    log_path = project_root / "logs" / "validation_results_json.txt"

    # Ensure logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup logger that writes to the specific file and console
    logger = setup_logger("T032b_JsonValidator")
    
    # Add a file handler specifically for the task log
    fh = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.info(f"Starting JSON validation for task T032b")
    logger.info(f"Input JSON: {json_path}")
    logger.info(f"Schema: {schema_path}")

    success = validate_json_against_schema(json_path, schema_path, logger)

    if success:
        logger.info("Final Result: VALID")
    else:
        logger.info("Final Result: INVALID")

    # Remove file handler to avoid double logging if logger is reused
    logger.removeHandler(fh)
    
    # Exit with error code if validation failed
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
