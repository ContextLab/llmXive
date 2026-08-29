import os
import sys
import json
import logging
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path if running from code/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from logging_config import setup_logging

logger = setup_logging("validate_schemas")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON/YAML schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_data_schema(data_path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a data file against a schema.
    Checks for required columns, types, and constraints.
    """
    import pandas as pd
    
    if not os.path.exists(data_path):
        return {
            "valid": False,
            "errors": [f"Data file not found: {data_path}"],
            "warnings": []
        }
    
    try:
        # Determine file type
        if data_path.endswith('.csv'):
            df = pd.read_csv(data_path)
        elif data_path.endswith('.parquet'):
            df = pd.read_parquet(data_path)
        else:
            return {
                "valid": False,
                "errors": [f"Unsupported file format: {data_path}"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        
        # Validate required columns
        required_columns = schema.get("required_columns", [])
        actual_columns = list(df.columns)
        
        for col in required_columns:
            if col not in actual_columns:
                errors.append(f"Missing required column: {col}")
        
        # Validate column types
        column_schemas = schema.get("columns", {})
        for col_name, col_spec in column_schemas.items():
            if col_name not in actual_columns:
                continue
            
            # Check type constraints
            expected_type = col_spec.get("type")
            if expected_type:
                if expected_type == "integer" and not pd.api.types.is_integer_dtype(df[col_name]):
                    warnings.append(f"Column '{col_name}' is not integer type")
                elif expected_type == "float" and not pd.api.types.is_numeric_dtype(df[col_name]):
                    warnings.append(f"Column '{col_name}' is not numeric type")
                elif expected_type == "string" and not pd.api.types.is_string_dtype(df[col_name]):
                    warnings.append(f"Column '{col_name}' is not string type")
            
            # Check value constraints
            if "enum" in col_spec:
                unique_values = df[col_name].unique()
                allowed_values = set(col_spec["enum"])
                invalid_values = set(unique_values) - allowed_values
                if invalid_values:
                    errors.append(f"Column '{col_name}' contains invalid values: {invalid_values}")
            
            if "min" in col_spec or "max" in col_spec:
                if pd.api.types.is_numeric_dtype(df[col_name]):
                    min_val = col_spec.get("min")
                    max_val = col_spec.get("max")
                    if min_val is not None and df[col_name].min() < min_val:
                        errors.append(f"Column '{col_name}' has values below minimum: {df[col_name].min()} < {min_val}")
                    if max_val is not None and df[col_name].max() > max_val:
                        errors.append(f"Column '{col_name}' has values above maximum: {df[col_name].max()} > {max_val}")
        
        # Check for null values in required columns
        for col in required_columns:
            if col in actual_columns and df[col].isnull().any():
                errors.append(f"Column '{col}' contains null values")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(df),
            "column_count": len(df.columns)
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Error reading data file: {str(e)}"],
            "warnings": []
        }

def validate_model_output_schema(output_path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a model output JSON file against a schema.
    """
    if not os.path.exists(output_path):
        return {
            "valid": False,
            "errors": [f"Output file not found: {output_path}"],
            "warnings": []
        }
    
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        errors = []
        warnings = []
        
        # Validate top-level structure
        required_keys = schema.get("required_keys", [])
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        # Validate nested structures
        key_schemas = schema.get("keys", {})
        for key_name, key_spec in key_schemas.items():
            if key_name not in data:
                continue
            
            value = data[key_name]
            expected_type = key_spec.get("type")
            
            if expected_type == "list" and not isinstance(value, list):
                errors.append(f"Key '{key_name}' should be a list")
            elif expected_type == "dict" and not isinstance(value, dict):
                errors.append(f"Key '{key_name}' should be a dict")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Key '{key_name}' should be a number")
            elif expected_type == "string" and not isinstance(value, str):
                errors.append(f"Key '{key_name}' should be a string")
            
            # Validate list items if specified
            if expected_type == "list" and "item_schema" in key_spec:
                item_schema = key_spec["item_schema"]
                for i, item in enumerate(value):
                    if not isinstance(item, item_schema.get("type", dict)):
                        warnings.append(f"Item {i} in '{key_name}' has unexpected type")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "file_path": output_path
        }
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"Invalid JSON format: {str(e)}"],
            "warnings": []
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Error reading output file: {str(e)}"],
            "warnings": []
        }

def validate_all_outputs() -> Dict[str, Any]:
    """
    Validate all output files against their respective schemas.
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "data_validations": [],
        "model_validations": [],
        "overall_valid": True,
        "summary": {
            "data_files_checked": 0,
            "data_files_valid": 0,
            "model_files_checked": 0,
            "model_files_valid": 0
        }
    }
    
    # Define paths to validate
    contracts_dir = os.path.join(project_root, "contracts")
    data_processed_dir = os.path.join(project_root, "data", "processed")
    data_synthetic_dir = os.path.join(project_root, "data", "synthetic")
    results_models_dir = os.path.join(project_root, "results", "models")
    
    # Load schemas
    dataset_schema_path = os.path.join(contracts_dir, "dataset.schema.yaml")
    model_output_schema_path = os.path.join(contracts_dir, "model-output.schema.yaml")
    
    if not os.path.exists(dataset_schema_path):
        logger.warning(f"Dataset schema not found: {dataset_schema_path}")
    else:
        dataset_schema = load_schema(dataset_schema_path)
        
        # Validate processed data files
        if os.path.exists(data_processed_dir):
            for filename in os.listdir(data_processed_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(data_processed_dir, filename)
                    logger.info(f"Validating processed data: {filename}")
                    validation_result = validate_data_schema(file_path, dataset_schema)
                    results["data_validations"].append({
                        "file": filename,
                        "type": "processed",
                        **validation_result
                    })
                    results["summary"]["data_files_checked"] += 1
                    if validation_result["valid"]:
                        results["summary"]["data_files_valid"] += 1
                    else:
                        results["overall_valid"] = False
        
        # Validate synthetic data files
        if os.path.exists(data_synthetic_dir):
            for filename in os.listdir(data_synthetic_dir):
                if filename.endswith('.csv'):
                    file_path = os.path.join(data_synthetic_dir, filename)
                    logger.info(f"Validating synthetic data: {filename}")
                    validation_result = validate_data_schema(file_path, dataset_schema)
                    results["data_validations"].append({
                        "file": filename,
                        "type": "synthetic",
                        **validation_result
                    })
                    results["summary"]["data_files_checked"] += 1
                    if validation_result["valid"]:
                        results["summary"]["data_files_valid"] += 1
                    else:
                        results["overall_valid"] = False
    
    if not os.path.exists(model_output_schema_path):
        logger.warning(f"Model output schema not found: {model_output_schema_path}")
    else:
        model_schema = load_schema(model_output_schema_path)
        
        # Validate model output files
        if os.path.exists(results_models_dir):
            for filename in os.listdir(results_models_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(results_models_dir, filename)
                    logger.info(f"Validating model output: {filename}")
                    validation_result = validate_model_output_schema(file_path, model_schema)
                    results["model_validations"].append({
                        "file": filename,
                        **validation_result
                    })
                    results["summary"]["model_files_checked"] += 1
                    if validation_result["valid"]:
                        results["summary"]["model_files_valid"] += 1
                    else:
                        results["overall_valid"] = False
    
    return results

def main():
    """Main entry point for schema validation."""
    logger.info("Starting schema validation for all outputs")
    
    results = validate_all_outputs()
    
    # Save validation report
    report_path = os.path.join(project_root, "results", "reports", "schema_validation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Validation report saved to: {report_path}")
    
    # Print summary
    print("\n=== Schema Validation Summary ===")
    print(f"Overall Valid: {results['overall_valid']}")
    print(f"Data Files: {results['summary']['data_files_valid']}/{results['summary']['data_files_checked']}")
    print(f"Model Files: {results['summary']['model_files_valid']}/{results['summary']['model_files_checked']}")
    
    if not results['overall_valid']:
        print("\nErrors found:")
        for validation in results['data_validations']:
            if not validation['valid']:
                print(f"  Data ({validation['file']}): {validation['errors']}")
        for validation in results['model_validations']:
            if not validation['valid']:
                print(f"  Model ({validation['file']}): {validation['errors']}")
        sys.exit(1)
    else:
        print("\nAll validations passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
