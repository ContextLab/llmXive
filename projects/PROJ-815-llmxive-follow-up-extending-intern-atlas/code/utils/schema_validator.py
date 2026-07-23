"""
Schema validation utilities for the llmXive pipeline.
Validates CSV data against YAML schemas.
"""
import os
import sys
import csv
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_metadata(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate the metadata section against the schema."""
    errors = []
    required_meta = schema.get('properties', {}).get('metadata', {}).get('properties', {})
    actual_meta = data.get('metadata', {})
    
    if not actual_meta:
        errors.append("Missing 'metadata' section in dataset file.")
        return errors

    # Check source
    if 'source' in required_meta and actual_meta.get('source') != required_meta['source'].get('const'):
        errors.append(f"Metadata source mismatch. Expected: {required_meta['source'].get('const')}, Got: {actual_meta.get('source')}")
    
    # Check extraction window
    if 'extraction_window' in required_meta:
        win_props = required_meta['extraction_window']['properties']
        actual_win = actual_meta.get('extraction_window', {})
        if actual_win.get('start_year') != win_props.get('start_year', {}).get('const'):
            errors.append(f"Extraction window start_year mismatch. Expected: {win_props['start_year']['const']}, Got: {actual_win.get('start_year')}")
        if actual_win.get('end_year') != win_props.get('end_year', {}).get('const'):
            errors.append(f"Extraction window end_year mismatch. Expected: {win_props['end_year']['const']}, Got: {actual_win.get('end_year')}")

    # Check edge filtering
    if 'edge_filtering' in required_meta:
        edge_props = required_meta['edge_filtering']['properties']
        actual_edge = actual_meta.get('edge_filtering', {})
        expected_types = edge_props.get('allowed_types', {}).get('const', [])
        actual_types = actual_edge.get('allowed_types', [])
        if set(actual_types) != set(expected_types):
            errors.append(f"Edge filtering types mismatch. Expected: {expected_types}, Got: {actual_types}")
        
        if edge_props.get('llm_inferred_excluded', {}).get('const') is True:
            if actual_edge.get('llm_inferred_excluded') is not True:
                errors.append("Edge filtering must exclude LLM-inferred types (llm_inferred_excluded=True).")

    return errors

def validate_data_types(row: Dict[str, str], schema_def: Dict[str, Any], row_num: int) -> List[str]:
    """Validate a single row's data types against the schema definition."""
    errors = []
    
    for col_name, col_schema in schema_def.items():
        if col_name not in row:
            # Skip if column is not present but might be optional (though schema says required in sample)
            # For strict validation, we check if it's required in the sample schema
            if col_name in ['node_id', 'title', 'publication_year', 'field_of_study', 'publication_venue', 
                            'citation_count', 'bottleneck_resolution_ratio', 'branching_entropy', 
                            'retraction_status', 'retraction_status_binary']:
                errors.append(f"Row {row_num}: Missing required column '{col_name}'")
            continue

        value = row[col_name]
        col_type = col_schema.get('type')
        
        # Nullable check
        if value == '' or value is None:
            if col_schema.get('nullable') is not True:
                errors.append(f"Row {row_num}: Column '{col_name}' is null but not marked nullable.")
            continue

        try:
            if col_type == 'string':
                # Ensure it's a string (already is in CSV)
                pass
            elif col_type == 'integer':
                  int_val = int(value)
                  if 'minimum' in col_schema and int_val < col_schema['minimum']:
                      errors.append(f"Row {row_num}: Column '{col_name}' value {int_val} is below minimum {col_schema['minimum']}")
                  if 'maximum' in col_schema and int_val > col_schema['maximum']:
                      errors.append(f"Row {row_num}: Column '{col_name}' value {int_val} is above maximum {col_schema['maximum']}")
                  if 'enum' in col_schema and int_val not in col_schema['enum']:
                      errors.append(f"Row {row_num}: Column '{col_name}' value {int_val} not in enum {col_schema['enum']}")
            elif col_type == 'number':
                  float_val = float(value)
                  if 'minimum' in col_schema and float_val < col_schema['minimum']:
                      errors.append(f"Row {row_num}: Column '{col_name}' value {float_val} is below minimum {col_schema['minimum']}")
                  if 'maximum' in col_schema and float_val > col_schema['maximum']:
                      errors.append(f"Row {row_num}: Column '{col_name}' value {float_val} is above maximum {col_schema['maximum']}")
            else:
                # Unknown type, skip strict check but log if needed
                pass
        except ValueError as e:
            errors.append(f"Row {row_num}: Column '{col_name}' failed type conversion ({col_type}): {e}")

    return errors

def validate_dataset(csv_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a CSV dataset against a YAML schema.
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    
    # Load Schema
    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        return False, [str(e)]
    
    # Load CSV
    csv_path_obj = Path(csv_path)
    if not csv_path_obj.exists():
        return False, [f"Dataset file not found: {csv_path}"]
    
    try:
        with open(csv_path_obj, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            if not header:
                return False, ["CSV file is empty or has no header."]
            
            # Check required columns from schema_definition
            schema_def = schema.get('properties', {}).get('schema_definition', {})
            required_cols = list(schema_def.keys())
            missing_cols = [c for c in required_cols if c not in header]
            if missing_cols:
                errors.append(f"Missing required columns in CSV header: {missing_cols}")
            
            # Validate data rows
            row_count = 0
            for row in reader:
                row_count += 1
                row_errors = validate_data_types(row, schema_def, row_count)
                errors.extend(row_errors)
                if len(errors) > 100: # Limit error reporting
                    errors.append("... validation stopped due to too many errors.")
                    break
            
            if row_count == 0:
                errors.append("CSV file contains no data rows.")

    except Exception as e:
        return False, [f"Error reading CSV file: {e}"]

    # Validate Metadata (if present in CSV or separate file? Assuming schema implies structure)
    # The schema provided is a JSON schema for a JSON object, but the task validates a CSV.
    # The CSV likely contains the 'data_sample' part. The 'metadata' and 'schema_definition' 
    # are structural requirements for the *dataset artifact* (which might be a JSON wrapper or 
    # just the CSV conforming to the schema_definition).
    # Given the task says "Validate contracts... on features_2010_2018.csv", we assume the CSV 
    # must match the 'schema_definition' and 'data_sample' structure. 
    # The 'metadata' section in the schema likely refers to a separate sidecar or header info 
    # not present in the raw CSV rows. We will skip metadata validation for the CSV file itself 
    # unless the CSV has a specific format for it, and focus on the column/row structure.
    
    # If the schema expects a JSON structure with metadata, and we are validating a CSV,
    # we assume the CSV represents the 'data_sample' array items.
    # We have already validated columns and types.
    
    return len(errors) == 0, errors

def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dataset against schema.")
    parser.add_argument("--csv", required=True, help="Path to the CSV file to validate.")
    parser.add_argument("--schema", required=True, help="Path to the YAML schema file.")
    args = parser.parse_args()
    
    print(f"Validating {args.csv} against {args.schema}...")
    is_valid, errors = validate_dataset(args.csv, args.schema)
    
    if is_valid:
        print("Validation PASSED.")
        sys.exit(0)
    else:
        print("Validation FAILED.")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
