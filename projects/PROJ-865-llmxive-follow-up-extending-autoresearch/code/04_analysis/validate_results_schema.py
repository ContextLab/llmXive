import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema from the given path."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_csv_schema(csv_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate that the CSV file matches the schema requirements.
    
    Checks:
    1. Required columns are present
    2. Column types (if specified) match the data
    3. Enum constraints are respected
    
    Args:
        csv_path: Path to the CSV file to validate
        schema: The schema dictionary to validate against
    
    Returns:
        True if validation passes, False otherwise.
    
    Raises:
        ValueError: If the CSV does not match the schema.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Load schema definitions
    required_columns = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Read CSV header
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        
        if header is None:
            raise ValueError("CSV file is empty or has no header.")
        
        header_set = set(header)
        
        # Check required columns
        missing_cols = set(required_columns) - header_set
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Validate each row against schema constraints
        row_num = 1
        for row in reader:
            row_num += 1
            for col_name, col_schema in properties.items():
                if col_name not in row:
                    continue  # Optional column
                
                value = row[col_name]
                
                # Check type constraints
                if 'type' in col_schema:
                    expected_type = col_schema['type']
                    if expected_type == 'integer':
                        try:
                            int(value)
                        except ValueError:
                            raise ValueError(
                                f"Row {row_num}, Column '{col_name}': "
                                f"Expected integer, got '{value}'"
                            )
                    elif expected_type == 'number':
                        try:
                            float(value)
                        except ValueError:
                            raise ValueError(
                                f"Row {row_num}, Column '{col_name}': "
                                f"Expected number, got '{value}'"
                            )
                    
                # Check enum constraints
                if 'enum' in col_schema:
                    allowed_values = col_schema['enum']
                    if value not in allowed_values:
                        raise ValueError(
                            f"Row {row_num}, Column '{col_name}': "
                            f"Value '{value}' not in allowed values {allowed_values}"
                        )
    
    return True

def main():
    """Main entry point for schema validation."""
    log_stage_start("Validate Results Schema", "T024")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    results_csv = project_root / "data" / "derived" / "results.csv"
    schema_path = project_root / "specs" / "001-llmxive-followup" / "contracts" / "pivot_attempt.schema.yaml"
    
    # Note: The schema is YAML, but we expect it to be JSON-serializable or converted.
    # If it's strictly YAML, we need to handle that. 
    # For now, we assume the schema file is JSON-compatible or we convert it.
    # If the file is actually .yaml, we try to load it as JSON first, then YAML.
    if not schema_path.exists():
        # Try with .json extension if .yaml doesn't exist or isn't valid JSON
        schema_path_json = project_root / "specs" / "001-llmxive-followup" / "contracts" / "pivot_attempt.schema.json"
        if schema_path_json.exists():
            schema_path = schema_path_json
        else:
            raise FileNotFoundError(
                f"Schema file not found at {schema_path} or {schema_path_json}"
            )
    
    try:
        # Load schema (handling potential YAML format if pyyaml is available)
        # Since requirements.txt includes standard libs, we check if pyyaml is needed.
        # The task description says "schema.yaml", so we might need to parse YAML.
        # However, the provided API surface doesn't show pyyaml usage. 
        # We will attempt to load as JSON first. If it fails, we assume the schema 
        # was meant to be JSON or we raise an error if pyyaml isn't available.
        try:
            schema = load_schema(schema_path)
        except json.JSONDecodeError:
            # Try to parse as YAML if JSON fails
            try:
                import yaml
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
            except ImportError:
                raise RuntimeError(
                    "Schema file is YAML but PyYAML is not installed. "
                    "Install PyYAML to parse YAML schemas."
                )
        
        # Validate CSV
        validate_csv_schema(results_csv, schema)
        
        logger.info(f"Validation passed: {results_csv} matches schema.")
        log_stage_end("Validate Results Schema", "T024", status="SUCCESS")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_stage_end("Validate Results Schema", "T024", status="FAILED", error=str(e))
        return 1
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        log_stage_end("Validate Results Schema", "T024", status="FAILED", error=str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_stage_end("Validate Results Schema", "T024", status="FAILED", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
