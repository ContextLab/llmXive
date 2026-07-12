import os
import sys
import json
import logging
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError, SchemaError

# Add project root to path to allow relative imports if needed, 
# though this script is standalone logic
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, setup_data_flow_logger

def setup_logger(name):
    """Setup a logger specific for this validation task."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_schema(schema_path: Path) -> dict:
    """Load a JSON/YAML schema file. Assuming JSON for jsonschema compatibility."""
    logger = logging.getLogger(__name__)
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        # Try JSON first, if it fails try simple YAML-like parsing if needed, 
        # but jsonschema expects dict, usually from JSON.
        # The task mentions .yaml extension in tasks.md but jsonschema usually consumes JSON.
        # We will attempt to load as JSON. If the file is YAML, we'd need PyYAML.
        # Given the API surface doesn't explicitly show PyYAML usage for schemas in other tasks,
        # and jsonschema is the standard, we assume the schema is valid JSON or we use PyYAML.
        # Let's import yaml safely if available, otherwise assume JSON.
        try:
            import yaml
            return yaml.safe_load(f)
        except ImportError:
            f.seek(0)
            return json.load(f)

def validate_json_against_schema(json_path: Path, schema_path: Path, output_log_path: Path) -> bool:
    """
    Validates a JSON file against a JSON Schema.
    Writes the result (success/failure details) to output_log_path.
    Returns True if valid, False if invalid or error occurred.
    """
    logger = setup_logger("validate_json_schema")
    logger.info(f"Starting validation of {json_path} against {schema_path}")
    
    log_lines = []
    log_lines.append(f"Validation Log: {json_path.name}")
    log_lines.append(f"Timestamp: {Path(output_log_path).parent.parent / 'now'}") # Placeholder for actual timestamp logic if needed, or just static
    from datetime import datetime
    log_lines[1] = f"Timestamp: {datetime.now().isoformat()}"
    
    try:
        # Load Data
        if not json_path.exists():
            msg = f"ERROR: Input JSON file not found: {json_path}"
            logger.error(msg)
            log_lines.append(msg)
            with open(output_log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return False

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load Schema
        schema = load_schema(schema_path)
        
        # Validate
        try:
            validate(instance=data, schema=schema)
            msg = f"SUCCESS: {json_path.name} is valid against {schema_path.name}."
            logger.info(msg)
            log_lines.append(msg)
            with open(output_log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return True
            
        except ValidationError as ve:
            msg = f"FAILURE: Validation Error in {json_path.name}."
            logger.error(msg)
            log_lines.append(msg)
            log_lines.append(f"  Message: {ve.message}")
            log_lines.append(f"  Path: {list(ve.path)}")
            log_lines.append(f"  Instance: {ve.instance}")
            
            with open(output_log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(log_lines))
            return False

    except json.JSONDecodeError as je:
        msg = f"ERROR: Invalid JSON in {json_path.name}: {str(je)}"
        logger.error(msg)
        log_lines.append(msg)
        with open(output_log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        return False
    except Exception as e:
        msg = f"ERROR: Unexpected error during validation: {str(e)}"
        logger.error(msg)
        log_lines.append(msg)
        with open(output_log_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))
        return False

def main():
    logger = setup_logger("validate_json_schema_main")
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    specs_dir = project_root / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts"
    logs_dir = project_root / "logs"
    
    # Ensure logs directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = data_processed_dir / "sensitivity_report.json"
    schema_file = specs_dir / "output.schema.yaml"
    output_log_file = logs_dir / "validation_log.json.txt"
    
    logger.info(f"Input: {input_file}")
    logger.info(f"Schema: {schema_file}")
    logger.info(f"Output Log: {output_log_file}")
    
    is_valid = validate_json_against_schema(input_file, schema_file, output_log_file)
    
    if is_valid:
        logger.info("Validation completed successfully.")
        sys.exit(0)
    else:
        logger.warning("Validation failed or error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    main()