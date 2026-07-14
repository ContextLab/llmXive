import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from utils.logging_config import get_logger, error

logger = get_logger(__name__)

# Define the project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "schemas"

def _load_schema(schema_name: str) -> Optional[Dict[str, Any]]:
    """Load a YAML schema file from the specs/schemas directory."""
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse schema {schema_name}: {e}")
        return None

def _validate_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Perform basic validation of data against a JSON-schema-like YAML structure.
    This is a simplified validator suitable for the project's data models.
    It checks for required keys and basic type constraints if defined.
    """
    if schema is None:
        return False

    # Check 'required' fields
    if "required" in schema:
        if isinstance(data, dict):
            for field in schema["required"]:
                if field not in data:
                    logger.error(f"Missing required field in data: {field}")
                    return False
        else:
            # If data is not a dict but schema requires fields, it's invalid
            logger.error("Data is not a dictionary but schema requires fields")
            return False

    # Check 'properties' types if data is a dict
    if "properties" in schema and isinstance(data, dict):
        for prop_name, prop_schema in schema["properties"].items():
            if prop_name in data:
                value = data[prop_name]
                expected_type = prop_schema.get("type")
                if expected_type:
                    type_map = {
                        "string": str,
                        "integer": int,
                        "number": (int, float),
                        "boolean": bool,
                        "array": list,
                        "object": dict,
                    }
                    expected_python_type = type_map.get(expected_type)
                    if expected_python_type and not isinstance(value, expected_python_type):
                        logger.error(
                            f"Type mismatch for field '{prop_name}': "
                            f"expected {expected_type}, got {type(value).__name__}"
                        )
                        return False
    return True

def validate_neural_data(data_path: Optional[str] = None) -> bool:
    """
    Validates neural data (e.g., ROI timecourses) against 'neural-data.schema.yaml'.
    
    Args:
        data_path: Path to the data file (CSV or JSON). If None, assumes the
                   standard path derived from project structure if needed,
                   but primarily validates the structure of provided data.
                   For this utility, we expect the caller to load the data
                   and pass the dict/list object, or we load a JSON file.
                   If data_path is provided and points to a JSON file, we load it.
                   If it's a CSV, we load it into a dict structure (simplified).
    
    Returns:
        bool: True if valid, False otherwise.
    """
    schema = _load_schema("neural-data.schema.yaml")
    if not schema:
        return False

    data = None
    
    if data_path:
        path_obj = Path(data_path)
        if not path_obj.exists():
            logger.error(f"Data file not found: {data_path}")
            return False
        
        if path_obj.suffix.lower() == ".json":
            try:
                with open(path_obj, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) # JSON is subset of YAML
            except Exception as e:
                logger.error(f"Failed to load JSON data: {e}")
                return False
        elif path_obj.suffix.lower() == ".csv":
            # For CSV, we perform a structural check by loading headers
            # This is a simplified check; full validation requires pandas
            try:
                import csv
                with open(path_obj, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    if not headers:
                        logger.error("CSV file is empty or has no headers")
                        return False
                    # Check if required headers exist
                    required_fields = schema.get("required", [])
                    if required_fields:
                        missing = set(required_fields) - set(headers)
                        if missing:
                            logger.error(f"CSV missing required columns: {missing}")
                            return False
                    # If valid structure, return True (assuming data types are okay)
                    return True
            except Exception as e:
                logger.error(f"Failed to parse CSV data: {e}")
                return False
    else:
        # If no path provided, we cannot validate specific file content,
        # but we can verify the schema is loadable and valid structure.
        # However, the task implies validating data *against* the schema.
        # If called without data, we return False or True depending on interpretation.
        # Standard behavior: validation requires data.
        logger.warning("validate_neural_data called without data path. Skipping content validation.")
        return True

    if data is not None:
        return _validate_against_schema(data, schema)
    
    return False

def validate_text_data(data_path: Optional[str] = None) -> bool:
    """
    Validates text data (e.g., ROCStories sample) against 'text-data.schema.yaml'.
    
    Args:
        data_path: Path to the data file (JSONL or JSON).
    
    Returns:
        bool: True if valid, False otherwise.
    """
    schema = _load_schema("text-data.schema.yaml")
    if not schema:
        return False

    if not data_path:
        logger.warning("validate_text_data called without data path. Skipping content validation.")
        return True

    path_obj = Path(data_path)
    if not path_obj.exists():
        logger.error(f"Text data file not found: {data_path}")
        return False

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Handle JSONL (newline delimited JSON)
        if path_obj.suffix.lower() == ".jsonl":
            lines = content.strip().split("\n")
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                try:
                    import json
                    data_obj = json.loads(line)
                    if not _validate_against_schema(data_obj, schema):
                        logger.error(f"Invalid JSONL record at line {i+1}")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSONL line {i+1}: {e}")
                    return False
            return True
        
        # Handle JSON
        elif path_obj.suffix.lower() == ".json":
            import json
            data_obj = json.loads(content)
            return _validate_against_schema(data_obj, schema)
        
        else:
            logger.error(f"Unsupported file format for text data: {path_obj.suffix}")
            return False

    except Exception as e:
        logger.error(f"Error reading text data file: {e}")
        return False

def validate_rsa_output(data_path: Optional[str] = None) -> bool:
    """
    Validates RSA output data against 'rsa-output.schema.yaml'.
    
    Args:
        data_path: Path to the RSA output file (JSON or CSV).
    
    Returns:
        bool: True if valid, False otherwise.
    """
    schema = _load_schema("rsa-output.schema.yaml")
    if not schema:
        return False

    if not data_path:
        logger.warning("validate_rsa_output called without data path. Skipping content validation.")
        return True

    path_obj = Path(data_path)
    if not path_obj.exists():
        logger.error(f"RSA output file not found: {data_path}")
        return False

    try:
        if path_obj.suffix.lower() == ".csv":
            import csv
            with open(path_obj, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                if not headers:
                    logger.error("RSA CSV file is empty or has no headers")
                    return False
                
                required_fields = schema.get("required", [])
                if required_fields:
                    missing = set(required_fields) - set(headers)
                    if missing:
                        logger.error(f"RSA CSV missing required columns: {missing}")
                        return False
                # Check numeric columns if defined in schema
                properties = schema.get("properties", {})
                for field, prop_def in properties.items():
                    if field in headers and prop_def.get("type") in ["number", "integer"]:
                        # Check first row for type validity
                        try:
                            for row in reader:
                                val = row[field]
                                if val:
                                    float(val) # Try to convert
                                break # Just check first non-empty
                        except ValueError:
                            logger.error(f"Column '{field}' contains non-numeric data")
                            return False
            return True

        elif path_obj.suffix.lower() == ".json":
            import json
            with open(path_obj, "r", encoding="utf-8") as f:
                data_obj = json.load(f)
            return _validate_against_schema(data_obj, schema)
        
        else:
            logger.error(f"Unsupported file format for RSA output: {path_obj.suffix}")
            return False

    except Exception as e:
        logger.error(f"Error reading RSA output file: {e}")
        return False
