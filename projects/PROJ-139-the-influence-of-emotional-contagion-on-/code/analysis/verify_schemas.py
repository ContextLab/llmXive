import os
import sys
import json
import yaml
import logging
from pathlib import Path
import hashlib
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> dict:
    """Load a schema definition from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_csv_schema(df: pd.DataFrame, schema: dict) -> list:
    """Validate a CSV dataframe against a schema definition.
    
    Args:
        df: Pandas DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    schema_columns = schema.get('columns', {})
    
    # Check for required columns
    required_columns = [col for col, props in schema_columns.items() 
                      if props.get('required', False)]
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {list(missing_columns)}")
    
    # Validate column types and constraints
    for col_name, col_schema in schema_columns.items():
        if col_name not in df.columns:
            continue
        
        # Check for null values if not allowed
        if not col_schema.get('allow_null', True) and df[col_name].isnull().any():
            errors.append(f"Column '{col_name}' contains null values but allows_null is False")
        
        # Validate data type if specified
        expected_type = col_schema.get('type')
        if expected_type:
            actual_type = str(df[col_name].dtype)
            # Map pandas dtypes to expected types
            type_mapping = {
                'int': ['int64', 'int32', 'int16', 'int8'],
                'float': ['float64', 'float32'],
                'string': ['object', 'string'],
                'bool': ['bool']
            }
            
            if expected_type in type_mapping:
                if actual_type not in type_mapping[expected_type]:
                    errors.append(
                        f"Column '{col_name}' has type '{actual_type}', expected '{expected_type}'"
                    )
            elif expected_type == actual_type:
                pass
            else:
                # Fallback: direct comparison
                errors.append(
                    f"Column '{col_name}' has type '{actual_type}', expected '{expected_type}'"
                )
    
    # Validate value ranges if specified
    for col_name, col_schema in schema_columns.items():
        if col_name not in df.columns:
            continue
        
        min_val = col_schema.get('min')
        max_val = col_schema.get('max')
        
        if min_val is not None:
            if (df[col_name] < min_val).any():
                errors.append(
                    f"Column '{col_name}' has values below minimum {min_val}"
                )
        
        if max_val is not None:
            if (df[col_name] > max_val).any():
                errors.append(
                    f"Column '{col_name}' has values above maximum {max_val}"
                )
    
    return errors

def validate_json_schema(data: dict, schema: dict) -> list:
    """Validate a JSON object against a schema definition.
    
    Args:
        data: Dictionary to validate
        schema: Schema definition dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check for required fields
    missing_fields = set(required_fields) - set(data.keys())
    if missing_fields:
        errors.append(f"Missing required fields: {list(missing_fields)}")
    
    # Validate field types
    for field_name, field_schema in properties.items():
        if field_name not in data:
            continue
        
        expected_type = field_schema.get('type')
        actual_value = data[field_name]
        
        # Simple type checking
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        if expected_type in type_map:
            if not isinstance(actual_value, type_map[expected_type]):
                errors.append(
                    f"Field '{field_name}' has type '{type(actual_value).__name__}', "
                    f"expected '{expected_type}'"
                )
        
        # Validate enum values
        if 'enum' in field_schema:
            if actual_value not in field_schema['enum']:
                errors.append(
                    f"Field '{field_name}' value '{actual_value}' not in allowed values: "
                    f"{field_schema['enum']}"
                )
        
        # Validate numeric ranges
        if expected_type in ['integer', 'number']:
            if 'minimum' in field_schema and actual_value < field_schema['minimum']:
                errors.append(
                    f"Field '{field_name}' value {actual_value} is below minimum {field_schema['minimum']}"
                )
            if 'maximum' in field_schema and actual_value > field_schema['maximum']:
                errors.append(
                    f"Field '{field_name}' value {actual_value} is above maximum {field_schema['maximum']}"
                )
    
    return errors

def run_schema_validation(
    processed_dir: Path, 
    contracts_dir: Path,
    output_path: Path
) -> dict:
    """Run schema validation on all processed data files.
    
    Args:
        processed_dir: Directory containing processed data files
        contracts_dir: Directory containing schema definitions
        output_path: Path to write the validation report
        
    Returns:
        Validation report dictionary
    """
    if not processed_dir.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        return {
            'status': 'fail',
            'errors': [f"Processed directory does not exist: {processed_dir}"],
            'files_checked': 0
        }
    
    if not contracts_dir.exists():
        logger.warning(f"Contracts directory does not exist: {contracts_dir}")
        return {
            'status': 'fail',
            'errors': [f"Contracts directory does not exist: {contracts_dir}"],
            'files_checked': 0
        }
    
    report = {
        'status': 'pass',
        'files_checked': 0,
        'files_passed': 0,
        'files_failed': 0,
        'errors': []
    }
    
    # Load all schemas
    schemas = {}
    for schema_file in contracts_dir.glob('*.yaml'):
        try:
            schema_name = schema_file.stem
            schemas[schema_name] = load_schema(schema_file)
            logger.info(f"Loaded schema: {schema_name}")
        except Exception as e:
            report['errors'].append(f"Failed to load schema {schema_name}: {str(e)}")
    
    if not schemas:
        report['status'] = 'fail'
        report['errors'].append("No schemas found in contracts directory")
        return report
    
    # Validate each processed file
    for file_path in processed_dir.glob('*'):
        if file_path.is_dir():
            continue
        
        report['files_checked'] += 1
        file_errors = []
        
        try:
            if file_path.suffix == '.csv':
                # Load CSV and validate against appropriate schema
                df = pd.read_csv(file_path)
                # Try to find matching schema (by filename stem)
                schema_name = file_path.stem
                if schema_name in schemas:
                    errors = validate_csv_schema(df, schemas[schema_name])
                    file_errors.extend(errors)
                else:
                    # Try to match by common naming patterns
                    matched = False
                    for s_name, s_def in schemas.items():
                        if s_name in str(file_path) or str(file_path) in s_name:
                            errors = validate_csv_schema(df, s_def)
                            file_errors.extend(errors)
                            matched = True
                            break
                    if not matched:
                        logger.warning(f"No matching schema found for {file_path}")
            
            elif file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Try to find matching schema
                schema_name = file_path.stem
                if schema_name in schemas:
                    errors = validate_json_schema(data, schemas[schema_name])
                    file_errors.extend(errors)
                else:
                    # Try to match by common naming patterns
                    matched = False
                    for s_name, s_def in schemas.items():
                        if s_name in str(file_path) or str(file_path) in s_name:
                            errors = validate_json_schema(data, s_def)
                            file_errors.extend(errors)
                            matched = True
                            break
                    if not matched:
                        logger.warning(f"No matching schema found for {file_path}")
            
            elif file_path.suffix == '.jsonl':
                # For JSONL files, validate first record and assume rest follows same schema
                schema_name = file_path.stem
                if schema_name in schemas:
                    with open(file_path, 'r') as f:
                        first_line = f.readline()
                        if first_line.strip():
                            data = json.loads(first_line)
                            errors = validate_json_schema(data, schemas[schema_name])
                            file_errors.extend(errors)
                else:
                    logger.warning(f"No matching schema found for {file_path}")
            
            else:
                logger.info(f"Skipping unsupported file format: {file_path}")
                continue
            
            # Compute file hash for record-keeping
            file_hash = compute_file_hash(file_path)
            
            if file_errors:
                report['files_failed'] += 1
                report['status'] = 'fail'
                for error in file_errors:
                    report['errors'].append(f"{file_path.name}: {error}")
                logger.error(f"Validation failed for {file_path.name}: {file_errors}")
            else:
                report['files_passed'] += 1
                logger.info(f"Validation passed for {file_path.name}")
        
        except Exception as e:
            report['files_failed'] += 1
            report['status'] = 'fail'
            error_msg = f"{file_path.name}: {str(e)}"
            report['errors'].append(error_msg)
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Schema validation complete. Status: {report['status']}")
    logger.info(f"Files checked: {report['files_checked']}, Passed: {report['files_passed']}, Failed: {report['files_failed']}")
    
    return report

def main():
    """Main entry point for schema validation."""
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    processed_dir = base_dir / 'data' / 'processed'
    contracts_dir = base_dir / 'code' / 'contracts'
    output_path = base_dir / 'state' / 'schema_validation_report.json'
    
    # Run validation
    report = run_schema_validation(processed_dir, contracts_dir, output_path)
    
    # Exit with appropriate code
    sys.exit(0 if report['status'] == 'pass' else 1)

if __name__ == '__main__':
    main()
