import os
import sys
import json
import yaml
import logging
from pathlib import Path
import hashlib
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "code" / "contracts"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"

def load_schema(schema_name: str) -> Optional[Dict[str, Any]]:
    """Load a schema definition from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}.yaml"
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None
    
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing schema {schema_name}: {e}")
        return None

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def validate_csv_schema(df: pd.DataFrame, schema: Dict[str, Any], file_path: Path) -> Tuple[bool, List[str]]:
    """Validate a CSV dataframe against a schema definition."""
    errors = []
    schema_columns = schema.get("columns", {})
    required_columns = schema.get("required_columns", [])
    
    # Check required columns
    existing_columns = set(df.columns)
    for col in required_columns:
        if col not in existing_columns:
            errors.append(f"Missing required column: {col}")
    
    # Check column types if defined
    for col_name, col_def in schema_columns.items():
        if col_name not in existing_columns:
            continue
        
        expected_type = col_def.get("type")
        if expected_type:
            # Map schema types to pandas types
            dtype_map = {
                "string": "object",
                "integer": "int64",
                "float": "float64",
                "boolean": "bool",
                "date": "datetime64[ns]"
            }
            target_dtype = dtype_map.get(expected_type)
            
            if target_dtype:
                try:
                    # Check if current dtype is compatible
                    current_dtype = str(df[col_name].dtype)
                    if target_dtype == "object" and current_dtype not in ["object", "string"]:
                        # Allow some flexibility for object types
                        pass 
                    elif target_dtype not in current_dtype:
                        # Strict check for numeric types
                        if target_dtype in ["int64", "float64"] and not pd.api.types.is_numeric_dtype(df[col_name]):
                            errors.append(f"Column '{col_name}' expected {expected_type} but found {current_dtype}")
                except Exception as e:
                    errors.append(f"Type check failed for '{col_name}': {e}")
    
    return len(errors) == 0, errors

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any], file_path: Path) -> Tuple[bool, List[str]]:
    """Validate a JSON file against a schema definition."""
    errors = []
    required_keys = schema.get("required_keys", [])
    properties = schema.get("properties", {})
    
    # Check required keys
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key: {key}")
    
    # Check property types
    for key, prop_def in properties.items():
        if key not in data:
            continue
        
        expected_type = prop_def.get("type")
        value = data[key]
        
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if expected_type in type_map:
            if not isinstance(value, type_map[expected_type]):
                errors.append(f"Key '{key}' expected {expected_type} but found {type(value).__name__}")
    
    return len(errors) == 0, errors

def run_schema_validation() -> Dict[str, Any]:
    """Run schema validation on all processed data files."""
    report = {
        "status": "pass",
        "files_checked": 0,
        "files_passed": 0,
        "files_failed": 0,
        "errors": []
    }

    if not PROCESSED_DIR.exists():
        logger.warning(f"Processed directory not found: {PROCESSED_DIR}")
        report["status"] = "fail"
        report["errors"].append("Processed directory does not exist")
        return report

    # Map file patterns to schema names
    file_schema_map = {
        "valid_threads.csv": "thread.schema",
        "all_threads_classified.csv": "thread.schema",
        "threads_with_seeds.csv": "thread.schema",
        "thread_metrics.csv": "result.schema",
        "sensitivity_analysis.csv": "result.schema",
        "external_validation_correlation.csv": "result.schema",
        "collinearity_diagnostics.json": "result.schema", # Assuming generic result schema for JSON
        "validity_status.json": "result.schema",
        "exclusion_counts.json": "result.schema",
        "vader_validation_report.json": "result.schema",
        "validation_justification.json": "result.schema",
        "sensitivity_analysis.csv": "result.schema"
    }

    # Also check generic schemas if specific mapping fails
    csv_schema = load_schema("thread.schema") or load_schema("result.schema")
    json_schema = load_schema("result.schema")

    files_to_check = list(PROCESSED_DIR.iterdir())
    report["files_checked"] = len(files_to_check)

    for file_path in files_to_check:
        if file_path.suffix not in [".csv", ".json"]:
            continue

        filename = file_path.name
        schema_name = file_schema_map.get(filename)
        
        if not schema_name:
            # Try to infer schema based on extension if not explicitly mapped
            if file_path.suffix == ".csv":
                schema_name = "thread.schema" # Default to thread for CSV
            elif file_path.suffix == ".json":
                schema_name = "result.schema" # Default to result for JSON
            else:
                continue

        schema = load_schema(schema_name)
        if not schema:
            # If schema not found, we might still check if it's a generic valid file
            # but strictly speaking, we need the schema definition.
            # For this implementation, we assume if schema is missing, it's a warning but not a hard fail 
            # unless the spec requires strict schema existence. 
            # Given the task "match the schema definitions", missing schema is an issue.
            logger.warning(f"No schema found for {filename} (mapped to {schema_name})")
            report["errors"].append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "error": f"Schema '{schema_name}' not found"
            })
            report["status"] = "fail"
            report["files_failed"] += 1
            continue

        is_valid, errors = False, []
        
        if file_path.suffix == ".csv":
            try:
                df = pd.read_csv(file_path)
                is_valid, errors = validate_csv_schema(df, schema, file_path)
            except Exception as e:
                errors.append(f"Failed to read CSV: {e}")
        
        elif file_path.suffix == ".json":
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                is_valid, errors = validate_json_schema(data, schema, file_path)
            except Exception as e:
                errors.append(f"Failed to read JSON: {e}")

        if is_valid:
            report["files_passed"] += 1
            # Optionally compute hash for successful files
            file_hash = compute_file_hash(file_path)
            if file_hash:
                report.setdefault("checksums", {})[str(file_path.relative_to(PROJECT_ROOT))] = file_hash
        else:
            report["files_failed"] += 1
            report["status"] = "fail"
            for err in errors:
                report["errors"].append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "error": err
                })

    # Ensure output directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    report_path = STATE_DIR / "schema_validation_report.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Schema validation report written to {report_path}")
    return report

def main():
    logger.info("Starting schema validation...")
    report = run_schema_validation()
    
    if report["status"] == "pass":
        logger.info("Schema validation PASSED.")
        sys.exit(0)
    else:
        logger.error("Schema validation FAILED.")
        logger.error(f"Files passed: {report['files_passed']}, Files failed: {report['files_failed']}")
        for err in report["errors"]:
            logger.error(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()