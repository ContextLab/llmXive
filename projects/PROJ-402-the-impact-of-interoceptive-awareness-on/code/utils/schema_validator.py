import os
import json
import yaml
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import pandas as pd
import jsonschema
from jsonschema import ValidationError, SchemaError

def load_schema_from_file(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON/YAML schema from a file.
    
    Args:
        schema_path: Path to the schema file (.yaml or .json)
        
    Returns:
        The loaded schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            if schema_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif schema_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported schema file format: {schema_path.suffix}")
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML schema: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON schema: {e}")


def validate_data_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a dictionary of data against a schema.
    
    Args:
        data: The data to validate.
        schema: The JSON Schema to validate against.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If the data does not match the schema.
    """
    jsonschema.validate(instance=data, schema=schema)
    return True


def validate_file_against_schema(file_path: Union[str, Path], schema_path: Union[str, Path]) -> bool:
    """
    Validate a BIDS events.tsv file against a schema.
    
    This function:
    1. Loads the schema from schema_path.
    2. Loads the TSV file as a dictionary of rows.
    3. Validates the data structure and content against the schema.
    
    Args:
        file_path: Path to the events.tsv file.
        schema_path: Path to the schema file.
        
    Returns:
        True if the file is valid.
        
    Raises:
        FileNotFoundError: If the file or schema is missing.
        ValueError: If the file format is invalid or validation fails.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    # Load Schema
    try:
        schema = load_schema_from_file(schema_path)
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(f"Schema loading failed: {e}")
    
    # Load TSV Data
    try:
        df = pd.read_csv(file_path, sep='\t')
    except Exception as e:
        raise ValueError(f"Failed to parse TSV file: {e}")
    
    # Validate required columns exist
    required_cols = schema.get('required', [])
    # Note: In BIDS, 'task' is required by schema, but 'onset' and 'duration' 
    # are typically required by BIDS spec even if not in our custom schema's 'required' list.
    # We rely on the schema's property definitions for type checking.
    
    # Check if required columns are present in the TSV
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path.name}: {missing_cols}")
    
    # Validate row by row against the schema properties
    # Since JSON Schema validates objects, we iterate rows
    errors = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            jsonschema.validate(instance=row_dict, schema=schema)
        except ValidationError as ve:
            errors.append(f"Row {idx}: {ve.message}")
    
    if errors:
        error_msg = f"Validation failed for {file_path.name}:\n" + "\n".join(errors)
        raise ValueError(error_msg)
    
    return True


def validate_contract_input(
    file_path: Union[str, Path], 
    schema_path: Union[str, Path] = None,
    exit_on_error: bool = True
) -> int:
    """
    Validate a file against a schema and return an exit code.
    
    This function is designed to be used as a standalone entry point or
    a contract enforcement mechanism.
    
    Exit Codes:
        0: Success (File is valid)
        1: File not found
        2: Schema not found
        3: Schema loading/parsing error
        4: File parsing error (invalid TSV/JSON)
        5: Validation failed (schema mismatch)
        99: Unexpected error
        
    Args:
        file_path: Path to the file to validate.
        schema_path: Path to the schema file. If None, defaults to 
                     'contracts/dataset.schema.yaml'.
        exit_on_error: If True, prints error and exits with code. 
                       If False, returns code without exiting.
                       
    Returns:
        An integer exit code.
    """
    if schema_path is None:
        # Default to the project's schema location relative to project root
        # Assuming this script is run from project root or code/utils
        schema_path = Path("contracts/dataset.schema.yaml")
        if not schema_path.exists():
            # Try relative to script location
            schema_path = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"
    
    schema_path = Path(schema_path)
    file_path = Path(file_path)
    
    try:
        if not file_path.exists():
            print(f"ERROR: Input file not found: {file_path}", file=sys.stderr)
            return 1
        
        if not schema_path.exists():
            print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
            return 2
        
        try:
            schema = load_schema_from_file(schema_path)
        except ValueError as e:
            print(f"ERROR: Schema parsing failed: {e}", file=sys.stderr)
            return 3
        
        try:
            validate_file_against_schema(file_path, schema_path)
        except ValueError as e:
            if "Failed to parse" in str(e):
                print(f"ERROR: File parsing failed: {e}", file=sys.stderr)
                return 4
            else:
                print(f"ERROR: Validation failed: {e}", file=sys.stderr)
                return 5
        
        print(f"SUCCESS: {file_path.name} is valid against the schema.")
        return 0
        
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 99
    finally:
        if exit_on_error:
            # Note: In a real script, we would call sys.exit() here.
            # However, to allow this function to be used in tests, 
            # we return the code. If used as a script entry point, 
            # the caller should exit.
            pass


def main():
    """
    CLI entry point for schema validation.
    Usage: python -m utils.schema_validator <file_path> [schema_path]
    """
    if len(sys.argv) < 2:
        print("Usage: python -m utils.schema_validator <file_path> [schema_path]")
        sys.exit(99)
    
    file_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    exit_code = validate_contract_input(file_path, schema_path, exit_on_error=False)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()