"""
Validation of all output artifacts (CSV, JSON, PNG) against schemas and success criteria.
Implements T028: Validate all output artifacts.
"""
import os
import sys
import csv
import json
import yaml
import struct
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Import logging config from sibling module
from logging_config import get_logger, setup_logging

# Import schema loader from validators if available, otherwise define locally
try:
    from validators import load_schema
except ImportError:
    def load_schema(schema_path: str) -> Dict:
        """Fallback loader if validators module is not fully imported yet."""
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)


def validate_csv_schema(file_path: str, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates a CSV file against a provided schema definition.
    
    Args:
        file_path: Path to the CSV file.
        schema: Dictionary defining required columns and types.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    logger = get_logger()
    
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return False, ["CSV file is empty or has no headers"]
            
            # Check required columns
            required_cols = schema.get('required_columns', [])
            missing_cols = set(required_cols) - set(headers)
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
            
            # Validate row count (minimum 1 data row)
            row_count = 0
            for row in reader:
                row_count += 1
                # Optional: Validate specific column types if schema defines them
                # e.g., if schema has 'column_types': {'trust_score': 'float'}
                for col, expected_type in schema.get('column_types', {}).items():
                    if col in row:
                        val = row[col]
                        if val is None or val == '':
                            continue # Allow empty if not required
                        try:
                            if expected_type == 'float':
                                float(val)
                            elif expected_type == 'int':
                                int(val)
                            elif expected_type == 'bool':
                                if val.lower() not in ['true', 'false', '1', '0']:
                                    raise ValueError("Invalid boolean")
                        except ValueError:
                            errors.append(f"Row {row_count+1}: Column '{col}' expected {expected_type}, got '{val}'")
            
            if row_count == 0:
                errors.append("CSV file contains no data rows")
                
            if errors:
                logger.warning(f"CSV validation failed for {file_path}: {errors}")
                return False, errors
            
            logger.info(f"CSV validation passed for {file_path} ({row_count} rows)")
            return True, []
            
    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")
        return False, errors


def validate_json_schema(file_path: str, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates a JSON file against a provided schema definition.
    
    Args:
        file_path: Path to the JSON file.
        schema: Dictionary defining required keys and types.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    logger = get_logger()
    
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not isinstance(data, dict):
            return False, ["JSON root must be an object/dictionary"]
        
        # Check required keys
        required_keys = schema.get('required_keys', [])
        missing_keys = set(required_keys) - set(data.keys())
        if missing_keys:
            errors.append(f"Missing required keys: {missing_keys}")
        
        # Validate types
        for key, expected_type in schema.get('key_types', {}).items():
            if key in data:
                val = data[key]
                if expected_type == 'float' and not isinstance(val, (int, float)):
                    errors.append(f"Key '{key}' expected float, got {type(val).__name__}")
                elif expected_type == 'int' and not isinstance(val, int):
                    errors.append(f"Key '{key}' expected int, got {type(val).__name__}")
                elif expected_type == 'string' and not isinstance(val, str):
                    errors.append(f"Key '{key}' expected string, got {type(val).__name__}")
                elif expected_type == 'list' and not isinstance(val, list):
                    errors.append(f"Key '{key}' expected list, got {type(val).__name__}")
        
        if errors:
            logger.warning(f"JSON validation failed for {file_path}: {errors}")
            return False, errors
        
        logger.info(f"JSON validation passed for {file_path}")
        return True, []
        
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON format: {str(e)}"]
    except Exception as e:
        return False, [f"Error reading JSON: {str(e)}"]


def validate_png_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Validates that a file is a valid PNG image by checking the magic bytes.
    
    Args:
        file_path: Path to the PNG file.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    logger = get_logger()
    
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    try:
        with open(file_path, 'rb') as f:
            # PNG Magic bytes: 89 50 4E 47 0D 0A 1A 0A
            header = f.read(8)
            expected_header = b'\x89PNG\r\n\x1a\n'
            
            if header != expected_header:
                return False, ["File is not a valid PNG (invalid magic bytes)"]
            
            # Basic file size check (should be > 0)
            f.seek(0, 2) # Seek to end
            size = f.tell()
            if size < 64: # Minimum reasonable PNG size
                return False, [f"File size too small ({size} bytes), likely corrupted"]
                
        logger.info(f"PNG validation passed for {file_path} ({size} bytes)")
        return True, []
        
    except Exception as e:
        return False, [f"Error reading PNG: {str(e)}"]


def validate_success_criteria(file_path: str, criteria: Dict) -> Tuple[bool, List[str]]:
    """
    Validates specific success criteria for a file (e.g., correlation coefficient range, font size).
    
    Args:
        file_path: Path to the file.
        criteria: Dictionary of criteria to check.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    logger = get_logger()
    
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.csv':
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Example: Check if correlation coefficient is within [-1, 1]
                    if 'correlation_coefficient' in row:
                        val = float(row['correlation_coefficient'])
                        if not (-1.0 <= val <= 1.0):
                            errors.append(f"Correlation coefficient {val} out of range [-1, 1]")
                            
        elif file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Example: Check for presence of non-causal disclaimer
                if 'disclaimer' in data:
                    if 'associational' not in data['disclaimer'].lower() and 'non-causal' not in data['disclaimer'].lower():
                        errors.append("Missing 'associational' or 'non-causal' disclaimer in JSON")
                elif 'results' in data:
                    # Check nested results
                    pass
                    
        elif file_ext == '.png':
            # For PNG, we might check file size or existence of metadata if needed
            # Currently just checking existence and validity in validate_png_file
            pass
            
        if errors:
            logger.warning(f"Success criteria validation failed for {file_path}: {errors}")
            return False, errors
            
        logger.info(f"Success criteria validation passed for {file_path}")
        return True, []
        
    except Exception as e:
        return False, [f"Error validating success criteria: {str(e)}"]


def run_validation_pipeline(
    csv_path: Optional[str] = None,
    json_path: Optional[str] = None,
    png_path: Optional[str] = None,
    schema_dir: str = "specs/001-emotional-synchrony-trust/contracts"
) -> Dict[str, Any]:
    """
    Runs the full validation pipeline on output artifacts.
    
    Args:
        csv_path: Path to the main results CSV.
        json_path: Path to the analysis report JSON.
        png_path: Path to the output figure PNG.
        schema_dir: Directory containing schema YAML files.
        
    Returns:
        Dictionary with validation results.
    """
    logger = get_logger()
    results = {
        "csv": {"valid": False, "errors": [], "path": csv_path},
        "json": {"valid": False, "errors": [], "path": json_path},
        "png": {"valid": False, "errors": [], "path": png_path},
        "overall_valid": True
    }
    
    # Load schemas
    dataset_schema_path = os.path.join(schema_dir, "dataset_schema.yaml")
    feature_schema_path = os.path.join(schema_dir, "feature_extraction_schema.yaml")
    
    dataset_schema = {}
    if os.path.exists(dataset_schema_path):
        dataset_schema = load_schema(dataset_schema_path)
    else:
        logger.warning(f"Dataset schema not found at {dataset_schema_path}, using defaults")
        # Default schema for results CSV if external schema missing
        dataset_schema = {
            "required_columns": ["interaction_id", "consistency_score", "trust_score"],
            "column_types": {"consistency_score": "float", "trust_score": "float"}
        }
    
    # Validate CSV
    if csv_path:
        is_valid, errors = validate_csv_schema(csv_path, dataset_schema)
        results["csv"]["valid"] = is_valid
        results["csv"]["errors"] = errors
        if not is_valid:
            results["overall_valid"] = False
    
    # Validate JSON
    if json_path:
        # Default schema for analysis report
        json_schema = {
            "required_keys": ["correlation_coefficient", "confidence_interval", "disclaimer"],
            "key_types": {"correlation_coefficient": "float"}
        }
        is_valid, errors = validate_json_schema(json_path, json_schema)
        results["json"]["valid"] = is_valid
        results["json"]["errors"] = errors
        if not is_valid:
            results["overall_valid"] = False
    
    # Validate PNG
    if png_path:
        is_valid, errors = validate_png_file(png_path)
        results["png"]["valid"] = is_valid
        results["png"]["errors"] = errors
        if not is_valid:
            results["overall_valid"] = False
    
    # Run success criteria checks
    if csv_path:
        criteria = {"correlation_range": (-1.0, 1.0)}
        is_valid, errors = validate_success_criteria(csv_path, criteria)
        if not is_valid:
            results["csv"]["success_criteria_valid"] = False
            results["csv"]["success_criteria_errors"] = errors
            results["overall_valid"] = False
        else:
            results["csv"]["success_criteria_valid"] = True
            
    if json_path:
        criteria = {"requires_disclaimer": True}
        is_valid, errors = validate_success_criteria(json_path, criteria)
        if not is_valid:
            results["json"]["success_criteria_valid"] = False
            results["json"]["success_criteria_errors"] = errors
            results["overall_valid"] = False
        else:
            results["json"]["success_criteria_valid"] = True
            
    return results


def main():
    """Main entry point for validation script."""
    setup_logging()
    logger = get_logger()
    
    parser = argparse.ArgumentParser(description="Validate output artifacts for PROJ-344")
    parser.add_argument("--csv", type=str, required=True, help="Path to results CSV")
    parser.add_argument("--json", type=str, required=True, help="Path to analysis JSON")
    parser.add_argument("--png", type=str, required=True, help="Path to output PNG")
    parser.add_argument("--schema-dir", type=str, default="specs/001-emotional-synchrony-trust/contracts",
                        help="Directory containing schema YAML files")
    
    args = parser.parse_args()
    
    logger.info("Starting output artifact validation...")
    
    results = run_validation_pipeline(
        csv_path=args.csv,
        json_path=args.json,
        png_path=args.png,
        schema_dir=args.schema_dir
    )
    
    # Print summary
    print("\n=== Validation Summary ===")
    print(f"CSV Valid: {results['csv']['valid']}")
    if results['csv']['errors']:
        print(f"  Errors: {results['csv']['errors']}")
    print(f"JSON Valid: {results['json']['valid']}")
    if results['json']['errors']:
        print(f"  Errors: {results['json']['errors']}")
    print(f"PNG Valid: {results['png']['valid']}")
    if results['png']['errors']:
        print(f"  Errors: {results['png']['errors']}")
    
    print(f"\nOverall Status: {'PASS' if results['overall_valid'] else 'FAIL'}")
    
    if not results['overall_valid']:
        sys.exit(1)
    else:
        logger.info("All validations passed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
