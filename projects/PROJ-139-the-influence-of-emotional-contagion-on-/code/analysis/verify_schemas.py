import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONTRACTS_DIR = Path("code/contracts")
PROCESSED_DIR = Path("data/processed")
STATE_DIR = Path("state")
REPORT_PATH = STATE_DIR / "schema_validation_report.json"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from the contracts directory.
    
    Args:
        schema_name: Name of the schema file (e.g., 'thread.schema.yaml')
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist
    """
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(file_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a CSV file against a schema definition.
    
    Args:
        file_path: Path to the CSV file
        schema: Schema definition dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    try:
        df = pd.read_csv(file_path)
        schema_columns = schema.get('columns', {})
        
        # Check for required columns
        required_columns = [col for col, props in schema_columns.items() 
                          if props.get('required', False)]
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {list(missing_cols)}")
        
        # Check column types (basic validation)
        for col, props in schema_columns.items():
            if col in df.columns:
                dtype = props.get('type')
                if dtype:
                    # Map schema types to pandas dtypes
                    type_map = {
                        'string': 'object',
                        'integer': 'int64',
                        'float': 'float64',
                        'boolean': 'bool',
                        'date': 'object',  # Dates are often stored as strings
                        'timestamp': 'object'
                    }
                    expected_dtype = type_map.get(dtype)
                    if expected_dtype and df[col].dtype != expected_dtype:
                        # Allow some flexibility for object types that might contain dates
                        if not (expected_dtype == 'object' and dtype in ['date', 'timestamp']):
                            logger.warning(
                                f"Column '{col}' in {file_path.name} has dtype {df[col].dtype}, "
                                f"expected {expected_dtype} (based on schema type {dtype})"
                            )
        
        # Check for null values in required columns
        for col in required_columns:
            if col in df.columns and df[col].isna().any():
                errors.append(f"Column '{col}' contains null values but is marked as required")
                
    except Exception as e:
        errors.append(f"Error reading or validating CSV: {str(e)}")
        
    return errors

def validate_json_schema(file_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a JSON file against a schema definition.
    
    Args:
        file_path: Path to the JSON file
        schema: Schema definition dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # For JSON, we check if the structure matches the schema
        schema_properties = schema.get('properties', {})
        
        if isinstance(data, dict):
            # Check required properties
            required_props = [prop for prop, props in schema_properties.items() 
                            if props.get('required', False)]
            
            missing_props = set(required_props) - set(data.keys())
            if missing_props:
                errors.append(f"Missing required properties: {list(missing_props)}")
                
            # Check property types
            for prop, props in schema_properties.items():
                if prop in data:
                    expected_type = props.get('type')
                    actual_value = data[prop]
                    
                    type_map = {
                        'string': str,
                        'integer': int,
                        'float': (int, float),
                        'boolean': bool,
                        'array': list,
                        'object': dict
                    }
                    
                    if expected_type and expected_type in type_map:
                        if not isinstance(actual_value, type_map[expected_type]):
                            errors.append(
                                f"Property '{prop}' has type {type(actual_value).__name__}, "
                                f"expected {expected_type}"
                            )
                            
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        errors.append(f"Error reading or validating JSON: {str(e)}")
        
    return errors

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_schema_validation() -> Dict[str, Any]:
    """
    Run schema validation on all processed data files.
    
    Returns:
        Validation report dictionary
    """
    report = {
        "status": "pass",
        "timestamp": pd.Timestamp.now().isoformat(),
        "files_checked": 0,
        "errors": []
    }
    
    if not PROCESSED_DIR.exists():
        report["status"] = "fail"
        report["errors"].append(f"Processed directory not found: {PROCESSED_DIR}")
        return report
        
    if not CONTRACTS_DIR.exists():
        report["status"] = "fail"
        report["errors"].append(f"Contracts directory not found: {CONTRACTS_DIR}")
        return report
        
    # Find all schema files
    schema_files = list(CONTRACTS_DIR.glob("*.yaml"))
    if not schema_files:
        report["status"] = "fail"
        report["errors"].append("No schema files found in contracts directory")
        return report
        
    # Load all schemas
    schemas = {}
    for schema_file in schema_files:
        try:
            schemas[schema_file.stem] = load_schema(schema_file.name)
        except Exception as e:
            report["errors"].append(f"Error loading schema {schema_file.name}: {str(e)}")
            
    # Find all data files to validate
    data_files = []
    for ext in ['*.csv', '*.json']:
        data_files.extend(PROCESSED_DIR.glob(ext))
        
    if not data_files:
        report["status"] = "fail"
        report["errors"].append("No data files found in processed directory")
        return report
        
    # Validate each data file
    for data_file in data_files:
        report["files_checked"] += 1
        file_errors = []
        
        # Try to find matching schema
        matched_schema = None
        schema_name = data_file.stem
        
        if schema_name in schemas:
            matched_schema = schemas[schema_name]
        else:
            # Try to match by common naming patterns
            for schema_key, schema_def in schemas.items():
                # Check if schema has a 'file_pattern' or similar hint
                if schema_def.get('file_pattern') and schema_def['file_pattern'] in data_file.name:
                    matched_schema = schema_def
                    break
                
        if not matched_schema:
            # If no schema found, log warning but don't fail
            logger.warning(f"No matching schema found for {data_file.name}. Skipping validation.")
            continue
            
        # Validate based on file type
        if data_file.suffix == '.csv':
            errors = validate_csv_schema(data_file, matched_schema)
        elif data_file.suffix == '.json':
            errors = validate_json_schema(data_file, matched_schema)
        else:
            errors = [f"Unsupported file type: {data_file.suffix}"]
            
        if errors:
            report["status"] = "fail"
            for error in errors:
                report["errors"].append({
                    "file": str(data_file),
                    "error": error,
                    "checksum": compute_file_hash(data_file)
                })
        else:
            logger.info(f"✓ {data_file.name} passed schema validation")
            
    return report

def main():
    """Main entry point for schema validation."""
    logger.info("Starting schema validation...")
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    report = run_schema_validation()
    
    # Save report
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Validation report saved to {REPORT_PATH}")
    logger.info(f"Status: {report['status']}")
    logger.info(f"Files checked: {report['files_checked']}")
    
    if report['errors']:
        logger.warning(f"Found {len(report['errors'])} validation errors")
        sys.exit(1)
    else:
        logger.info("All validations passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
