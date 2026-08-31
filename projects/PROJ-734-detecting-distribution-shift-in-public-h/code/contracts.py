import os
import yaml
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from exceptions import E_NO_DATA

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_date_format(date_str: str) -> bool:
    """Validate ISO week format (YYYY-Www or YYYY-ww)."""
    try:
        # Attempt to parse common week formats
        if 'W' in date_str:
            datetime.strptime(date_str, "%Y-W%W")
        else:
            # Fallback for YYYY-ww format if supported by specific parser
            # Basic regex check for YYYY-ww
            if len(date_str) == 7 and date_str[4] == '-':
                int(date_str[:4])
                int(date_str[5:])
                return True
            return False
        return True
    except ValueError:
        return False

def validate_numeric(value: Any) -> bool:
    """Check if a value is numeric."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def validate_record(record: Dict[str, Any], schema: Dict[str, Any], record_type: str) -> List[str]:
    """
    Validate a single record against a schema definition.
    Returns a list of errors.
    """
    errors = []
    required_cols = schema.get('required_columns', [])
    
    for col in required_cols:
        if col not in record:
            errors.append(f"Missing required column: {col}")
            continue
        
        value = record[col]
        
        # Type checks based on column name heuristics if specific type not in schema
        if 'week' in col.lower():
            if not validate_date_format(str(value)):
                errors.append(f"Invalid date format in {col}: {value}")
        elif 'ili' in col.lower() or 'percent' in col.lower():
            if not validate_numeric(value):
                errors.append(f"Non-numeric value in {col}: {value}")
        elif col == 'event_name':
            if not isinstance(value, str) or len(value.strip()) == 0:
                errors.append(f"Invalid event name in {col}: {value}")
    
    return errors

def validate_csv_file(file_path: str, schema: Dict[str, Any], record_type: str = "dataset") -> bool:
    """
    Validate a CSV file against a schema.
    Returns True if valid, raises E_NO_DATA or ValueError if invalid.
    """
    if not os.path.exists(file_path):
        raise E_NO_DATA(f"Required data file missing: {file_path}")
    
    schema_props = schema.get('properties', {}).get(record_type, {})
    expected_cols = schema_props.get('columns', [])
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check header
        if reader.fieldnames is None:
            raise ValueError(f"Empty CSV file: {file_path}")
        
        missing_cols = set(expected_cols) - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing columns in {file_path}: {missing_cols}")
        
        # Validate rows
        row_count = 0
        for i, row in enumerate(reader):
            row_count += 1
            errors = validate_record(row, schema_props, record_type)
            if errors:
                # Log first error and raise
                raise ValueError(f"Validation error in {file_path}, row {i+2}: {errors[0]}")
        
        if row_count == 0:
            raise ValueError(f"CSV file {file_path} contains no data rows")
    
    return True

def validate_raw_data(raw_dir: str = "data/raw") -> bool:
    """
    Validate raw dataset schemas.
    Checks fluview_ili.csv and ground_truth_events.csv.
    """
    dataset_schema_path = "contracts/dataset.schema.yaml"
    if not os.path.exists(dataset_schema_path):
        raise E_NO_DATA(f"Dataset schema missing: {dataset_schema_path}")
    
    schema = load_schema(dataset_schema_path)
    
    # Validate FluView
    fluview_path = os.path.join(raw_dir, "fluview_ili.csv")
    try:
        validate_csv_file(fluview_path, schema, "fluview_ili")
    except E_NO_DATA:
        raise
    except Exception as e:
        raise ValueError(f"FluView data invalid: {e}")
    
    # Validate Ground Truth
    gt_path = os.path.join(raw_dir, "ground_truth_events.csv")
    try:
        validate_csv_file(gt_path, schema, "ground_truth_events")
    except E_NO_DATA:
        raise
    except Exception as e:
        raise ValueError(f"Ground truth data invalid: {e}")
    
    return True

def validate_output_data(processed_dir: str = "data/processed") -> bool:
    """
    Validate output dataset schemas.
    Checks flags.csv, baselines.csv, sensitivity.csv, etc.
    """
    output_schema_path = "contracts/output.schema.yaml"
    if not os.path.exists(output_schema_path):
        raise E_NO_DATA(f"Output schema missing: {output_schema_path}")
    
    schema = load_schema(output_schema_path)
    
    # Validate Flags
    flags_path = os.path.join(processed_dir, "flags.csv")
    try:
        validate_csv_file(flags_path, schema, "flags")
    except E_NO_DATA:
        # Flags might be empty if no shifts detected, but file must exist
        if not os.path.exists(flags_path):
            raise E_NO_DATA(f"Output file missing: {flags_path}")
    
    # Validate Baselines
    baselines_path = os.path.join(processed_dir, "baselines.csv")
    if os.path.exists(baselines_path):
        try:
            validate_csv_file(baselines_path, schema, "baselines")
        except Exception as e:
            raise ValueError(f"Baselines data invalid: {e}")
    
    # Validate Sensitivity
    sens_path = os.path.join(processed_dir, "sensitivity.csv")
    if os.path.exists(sens_path):
        try:
            validate_csv_file(sens_path, schema, "sensitivity")
        except Exception as e:
            raise ValueError(f"Sensitivity data invalid: {e}")
    
    # Validate Report
    report_path = os.path.join(processed_dir, "report.pdf")
    if not os.path.exists(report_path):
        raise E_NO_DATA(f"Output file missing: {report_path}")
    
    return True