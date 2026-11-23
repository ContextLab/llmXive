"""
Script to validate all data artifacts produced by the pipeline against their schemas.

Usage:
    python code/data/validate_artifacts.py [--schema-dir <path>] [--data-dir <path>]
"""
import argparse
import sys
from pathlib import Path
import json
import yaml

from data.schema_validator import (
    SchemaValidationError,
    load_schema,
    validate_json_against_schema,
    validate_file_exists,
    validate_directory_exists
)


def load_yaml_schema(file_path: str) -> dict:
    """Load a YAML schema file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_json_data(file_path: str) -> dict:
    """Load a JSON data file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_artifact(data_file: str, schema_file: str) -> bool:
    """
    Validate a single artifact against its schema.
    
    Args:
        data_file: Path to the data file
        schema_file: Path to the schema file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not validate_file_exists(data_file):
            print(f"  ERROR: Data file not found: {data_file}")
            return False
            
        if not validate_file_exists(schema_file):
            print(f"  ERROR: Schema file not found: {schema_file}")
            return False
            
        data = load_json_data(data_file)
        schema = load_yaml_schema(schema_file)
        
        validate_json_against_schema(data, schema)
        print(f"  ✓ Valid: {Path(data_file).name}")
        return True
        
    except SchemaValidationError as e:
        print(f"  ✗ Invalid: {Path(data_file).name} - {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error validating {Path(data_file).name}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate data artifacts against schemas")
    parser.add_argument("--schema-dir", default="contracts", help="Directory containing schema files")
    parser.add_argument("--data-dir", default="data", help="Directory containing data files")
    args = parser.parse_args()
    
    schema_dir = Path(args.schema_dir)
    data_dir = Path(args.data_dir)
    
    if not schema_dir.exists():
        print(f"Schema directory not found: {schema_dir}")
        sys.exit(1)
        
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        sys.exit(1)
        
    # Define artifact mappings: (data_file, schema_file)
    artifact_mappings = [
        ("data/context_splits.json", "contracts/dataset.schema.yaml"),
        ("data/teacher_logits_raw.json", "contracts/training_output.schema.yaml"),
        ("data/teacher_distribution.json", "contracts/training_output.schema.yaml"),
        ("results/training_metrics.json", "contracts/training_output.schema.yaml"),
        ("results/memory_log.json", "contracts/analysis_results.schema.yaml"),
        ("data/analysis_results.json", "contracts/analysis_results.schema.yaml"),
    ]
    
    print("Validating data artifacts against schemas...")
    print("-" * 50)
    
    all_valid = True
    for data_file, schema_file in artifact_mappings:
        data_path = data_dir / data_file
        schema_path = schema_dir / schema_file
        
        if not data_path.exists():
            print(f"  - Skipping (data not found): {data_file}")
            continue
            
        if not schema_path.exists():
            print(f"  - Skipping (schema not found): {schema_file}")
            continue
            
        print(f"Checking: {data_file} against {schema_file}")
        if not validate_artifact(str(data_path), str(schema_path)):
            all_valid = False
        print()
    
    print("-" * 50)
    if all_valid:
        print("✓ All artifacts are valid")
        sys.exit(0)
    else:
        print("✗ Some artifacts failed validation")
        sys.exit(1)


if __name__ == "__main__":
    main()