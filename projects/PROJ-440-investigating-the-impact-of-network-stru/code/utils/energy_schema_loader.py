"""
Utility module for loading and validating the energy decay schema.
Provides functions to read the YAML schema and validate CSV data against it.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import csv

SCHEMA_PATH = Path("contracts/energy_schema.schema.yaml")

def load_energy_schema() -> Dict[str, Any]:
    """
    Load the energy decay schema from the YAML file.
    
    Returns:
        Dict containing the parsed schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
        
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
        
    return schema

def validate_csv_against_schema(csv_path: str, schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Validate a CSV file against the energy decay schema.
    
    Args:
        csv_path: Path to the CSV file to validate.
        schema: Optional pre-loaded schema. If None, loads from default path.
        
    Returns:
        Tuple of (is_valid, error_message)
        is_valid is True if the CSV matches the schema requirements.
    """
    if schema is None:
        try:
            schema = load_energy_schema()
        except Exception as e:
            return False, f"Failed to load schema: {e}"
    
    if not os.path.exists(csv_path):
        return False, f"CSV file not found: {csv_path}"
    
    try:
        with open(csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return False, "CSV file is empty or has no headers"
            
            # Check required fields from schema
            required_fields = schema.get('required', [])
            missing_fields = [field for field in required_fields if field not in headers]
            
            if missing_fields:
                return False, f"Missing required columns: {', '.join(missing_fields)}"
            
            # Validate a few rows for type consistency (basic check)
            row_count = 0
            for row in reader:
                row_count += 1
                if row_count > 100:  # Check first 100 rows for performance
                    break
                    
                # Check numeric fields
                numeric_fields = ['decay_rate', 'r_squared', 'convergence_std', 'convergence_mean', 
                                'clustering_coeff', 'avg_path_length', 'avg_degree', 'N']
                
                for field in numeric_fields:
                    if field in row and row[field]:
                        try:
                            float(row[field])
                        except ValueError:
                            return False, f"Row {row_count}: Invalid numeric value for '{field}': {row[field]}"
                
                # Check enum fields
                enum_fields = {
                    'class': ['random', 'scale_free', 'small_world', 'lattice', 'star'],
                    'status': ['dissipative', 'resonant', 'unstable', 'failed']
                }
                
                for field, allowed_values in enum_fields.items():
                    if field in row and row[field] and row[field] not in allowed_values:
                        return False, f"Row {row_count}: Invalid value for '{field}': {row[field]}. Allowed: {allowed_values}"
            
            return True, f"Validation passed. Checked {row_count} rows."
            
    except csv.Error as e:
        return False, f"CSV parsing error: {e}"
    except Exception as e:
        return False, f"Unexpected error during validation: {e}"
