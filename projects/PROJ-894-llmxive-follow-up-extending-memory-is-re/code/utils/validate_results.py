"""
Schema validation script for result CSVs.
Verifies that all result files strictly adhere to the defined schema.
"""

import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the expected schema for result CSVs
# This matches the structure expected by the analysis pipeline
RESULTS_SCHEMA = {
    "baseline_results.csv": {
        "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
        "optional_columns": ["strategy", "timestamp", "timeout"]
    },
    "lazy_results.csv": {
        "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
        "optional_columns": ["strategy", "timestamp", "timeout", "evidence_threshold"]
    },
    "greedy_results.csv": {
        "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
        "optional_columns": ["strategy", "timestamp", "timeout", "top_k"]
    },
    "noisy_baseline_results.csv": {
        "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
        "optional_columns": ["strategy", "timestamp", "timeout", "noise_level"]
    },
    "noisy_lazy_results.csv": {
        "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
        "optional_columns": ["strategy", "timestamp", "timeout", "evidence_threshold", "noise_level"]
    },
    "noisy_greedy_results.csv": {
        "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
        "optional_columns": ["strategy", "timestamp", "timeout", "top_k", "noise_level"]
    }
}

# Default paths relative to project root
DEFAULT_DATA_DIR = Path("data/processed")
DEFAULT_SCHEMA_FILE = Path("contracts/results.schema.yaml")

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the schema from a YAML file if it exists, otherwise return the default schema.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
    """
    if schema_path and schema_path.exists():
        try:
            with open(schema_path, 'r') as f:
                loaded_schema = yaml.safe_load(f)
                logger.info(f"Loaded schema from {schema_path}")
                return loaded_schema
        except Exception as e:
            logger.warning(f"Failed to load schema from {schema_path}: {e}. Using default schema.")
            return RESULTS_SCHEMA
    else:
        logger.info("No schema file found. Using default schema.")
        return RESULTS_SCHEMA

def validate_csv_structure(
    file_path: Path,
    schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate the structure of a single CSV file against the schema.
    
    Args:
        file_path: Path to the CSV file.
        schema: Schema definition for this specific file.
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not file_path.exists():
        errors.append(f"File does not exist: {file_path}")
        return False, errors
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if headers is None:
                errors.append(f"File is empty or has no headers: {file_path}")
                return False, errors
            
            # Check required columns
            required_cols = schema.get("required_columns", [])
            for col in required_cols:
                if col not in headers:
                    errors.append(f"Missing required column '{col}' in {file_path.name}")
            
            # Check optional columns (just log, don't fail)
            optional_cols = schema.get("optional_columns", [])
            found_optional = [col for col in optional_cols if col in headers]
            if found_optional:
                logger.debug(f"Found optional columns in {file_path.name}: {found_optional}")
            
            # Validate data types for required columns (basic check)
            for row_idx, row in enumerate(reader, start=2): # start=2 because row 1 is header
                # Check for empty task_id
                if 'task_id' in row and (row['task_id'] is None or row['task_id'].strip() == ''):
                    errors.append(f"Empty task_id at row {row_idx} in {file_path.name}")
                
                # Check numeric columns
                for col in ['accuracy', 'nodes_visited', 'latency_ms']:
                    if col in row and row[col]:
                        try:
                            float(row[col])
                        except ValueError:
                            errors.append(f"Invalid numeric value for '{col}' at row {row_idx} in {file_path.name}: {row[col]}")
                
                # Only check first few rows for performance if file is huge
                if row_idx > 10:
                    break
    
    except csv.Error as e:
        errors.append(f"CSV parsing error in {file_path.name}: {e}")
    except Exception as e:
        errors.append(f"Unexpected error reading {file_path.name}: {e}")
    
    return len(errors) == 0, errors

def validate_all_results(
    data_dir: Optional[Path] = None,
    schema_path: Optional[Path] = None,
    specific_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate all result CSV files against the schema.
    
    Args:
        data_dir: Directory containing the result CSVs.
        schema_path: Path to the schema YAML file.
        specific_files: Optional list of specific filenames to validate.
        
    Returns:
        Dictionary containing validation results.
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    
    schema = load_schema(schema_path)
    
    # Determine which files to validate
    files_to_check = specific_files if specific_files else list(RESULTS_SCHEMA.keys())
    
    results = {
        "valid": True,
        "files_validated": 0,
        "files_failed": 0,
        "details": {}
    }
    
    for filename in files_to_check:
        if filename not in schema:
            logger.warning(f"No schema defined for {filename}. Skipping.")
            continue
        
        file_path = data_dir / filename
        logger.info(f"Validating {filename}...")
        
        is_valid, errors = validate_csv_structure(file_path, schema[filename])
        
        results["files_validated"] += 1
        
        if not is_valid:
            results["valid"] = False
            results["files_failed"] += 1
            results["details"][filename] = {
                "status": "FAILED",
                "errors": errors
            }
            logger.error(f"Validation failed for {filename}: {errors}")
        else:
            results["details"][filename] = {
                "status": "PASSED",
                "errors": []
            }
            logger.info(f"Validation passed for {filename}")
    
    return results

def main():
    """
    Main entry point for the validation script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate result CSVs against the schema."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Directory containing result CSVs (default: {DEFAULT_DATA_DIR})"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_FILE,
        help=f"Path to schema YAML file (default: {DEFAULT_SCHEMA_FILE})"
    )
    parser.add_argument(
        "--files",
        nargs='+',
        default=None,
        help="Specific files to validate (default: all defined in schema)"
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Path to save validation report as JSON"
    )
    
    args = parser.parse_args()
    
    logger.info("Starting result validation...")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Schema file: {args.schema}")
    
    validation_results = validate_all_results(
        data_dir=args.data_dir,
        schema_path=args.schema,
        specific_files=args.files
    )
    
    # Print summary
    status = "PASSED" if validation_results["valid"] else "FAILED"
    logger.info(f"\nValidation {status}")
    logger.info(f"Files validated: {validation_results['files_validated']}")
    logger.info(f"Files failed: {validation_results['files_failed']}")
    
    # Save JSON report if requested
    if args.json_output:
        with open(args.json_output, 'w') as f:
            json.dump(validation_results, f, indent=2)
        logger.info(f"Validation report saved to {args.json_output}")
    
    # Exit with appropriate code
    sys.exit(0 if validation_results["valid"] else 1)

if __name__ == "__main__":
    main()