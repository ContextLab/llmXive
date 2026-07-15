"""
Schema validation script for llmXive research results.

This script verifies that all result CSVs strictly adhere to the
contracts/results.schema.yaml definition.

Expected input files (relative to project root):
- data/processed/baseline_results.csv
- data/processed/lazy_results.csv
- data/processed/greedy_results.csv
- data/processed/noisy_baseline_results.csv
- data/processed/noisy_lazy_results.csv
- data/processed/noisy_greedy_results.csv

Expected schema file:
- specs/contracts/results.schema.yaml (or contracts/results.schema.yaml)
"""

import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the expected schema based on task requirements
# Since the schema file might not exist yet, we define the expected structure
# based on the task description: task_id, accuracy, nodes_visited, inference_time_seconds/latency_ms
EXPECTED_SCHEMA = {
    "required_columns": ["task_id", "accuracy", "nodes_visited", "latency_ms"],
    "column_types": {
        "task_id": str,
        "accuracy": float,
        "nodes_visited": int,
        "latency_ms": float
    },
    "required_files": [
        "data/processed/baseline_results.csv",
        "data/processed/lazy_results.csv",
        "data/processed/greedy_results.csv",
        "data/processed/noisy_baseline_results.csv",
        "data/processed/noisy_lazy_results.csv",
        "data/processed/noisy_greedy_results.csv"
    ]
}

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load schema from YAML file if it exists, otherwise return default schema.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing schema definition
    """
    if schema_path.exists():
        try:
            import yaml
            with open(schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            logger.info(f"Loaded schema from {schema_path}")
            return schema
        except Exception as e:
            logger.warning(f"Failed to load schema from {schema_path}: {e}. Using default schema.")
            return EXPECTED_SCHEMA
    else:
        logger.warning(f"Schema file {schema_path} not found. Using default schema.")
        return EXPECTED_SCHEMA

def validate_csv_structure(csv_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of a single CSV file against the schema.
    
    Args:
        csv_path: Path to the CSV file
        schema: Schema definition dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not csv_path.exists():
        errors.append(f"File not found: {csv_path}")
        return errors
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                errors.append(f"Empty or invalid CSV: {csv_path}")
                return errors
            
            header_set = set(reader.fieldnames)
            required_cols = set(schema.get("required_columns", []))
            
            missing_cols = required_cols - header_set
            if missing_cols:
                errors.append(f"Missing required columns in {csv_path}: {missing_cols}")
            
            extra_cols = header_set - required_cols
            if extra_cols:
                logger.warning(f"Extra columns found in {csv_path}: {extra_cols}")
            
            # Validate data types and values
            row_count = 0
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-indexed, header is row 1)
                row_count += 1
                
                # Validate task_id (should be non-empty string)
                task_id = row.get("task_id", "")
                if not task_id or not isinstance(task_id, str):
                    errors.append(f"Invalid task_id at row {row_num} in {csv_path}")
                
                # Validate accuracy (should be float between 0 and 1)
                try:
                    accuracy = float(row.get("accuracy", ""))
                    if not (0.0 <= accuracy <= 1.0):
                        errors.append(f"Accuracy out of range [0, 1] at row {row_num} in {csv_path}: {accuracy}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid accuracy value at row {row_num} in {csv_path}: {row.get('accuracy')}")
                
                # Validate nodes_visited (should be non-negative integer)
                try:
                    nodes = int(row.get("nodes_visited", ""))
                    if nodes < 0:
                        errors.append(f"Negative nodes_visited at row {row_num} in {csv_path}: {nodes}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid nodes_visited value at row {row_num} in {csv_path}: {row.get('nodes_visited')}")
                
                # Validate latency_ms (should be non-negative float)
                try:
                    latency = float(row.get("latency_ms", ""))
                    if latency < 0:
                        errors.append(f"Negative latency_ms at row {row_num} in {csv_path}: {latency}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid latency_ms value at row {row_num} in {csv_path}: {row.get('latency_ms')}")
            
            if row_count == 0:
                errors.append(f"CSV file is empty (no data rows): {csv_path}")
                
    except Exception as e:
        errors.append(f"Error reading CSV {csv_path}: {str(e)}")
    
    return errors

def validate_all_results(project_root: Path) -> bool:
    """
    Validate all result CSV files against the schema.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        True if all validations pass, False otherwise
    """
    # Determine schema path
    schema_paths = [
        project_root / "specs" / "contracts" / "results.schema.yaml",
        project_root / "contracts" / "results.schema.yaml"
    ]
    
    schema_path = next((p for p in schema_paths if p.exists()), None)
    schema = load_schema(schema_path) if schema_path else EXPECTED_SCHEMA
    
    # Check all required files
    all_errors: List[str] = []
    valid_files: List[str] = []
    
    for file_rel_path in schema.get("required_files", EXPECTED_SCHEMA["required_files"]):
        csv_path = project_root / file_rel_path
        errors = validate_csv_structure(csv_path, schema)
        
        if errors:
            all_errors.extend(errors)
            logger.error(f"Validation failed for {file_rel_path}: {errors}")
        else:
            valid_files.append(file_rel_path)
            logger.info(f"Validation passed for {file_rel_path}")
    
    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Valid files: {len(valid_files)}/{len(schema.get('required_files', EXPECTED_SCHEMA['required_files']))}")
    
    if all_errors:
        logger.error(f"Total errors found: {len(all_errors)}")
        for err in all_errors:
            logger.error(f"  - {err}")
        return False
    else:
        logger.info("All result files validated successfully!")
        return True

def main():
    """Main entry point for the validation script."""
    logger.info("Starting results schema validation...")
    
    success = validate_all_results(PROJECT_ROOT)
    
    if success:
        logger.info("Validation completed successfully.")
        sys.exit(0)
    else:
        logger.error("Validation failed. Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()