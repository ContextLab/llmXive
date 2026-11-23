import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaField:
    def __init__(self, name: str, dtype: str, required: bool = True, description: str = ""):
        self.name = name
        self.dtype = dtype
        self.required = required
        self.description = description

class Schema:
    def __init__(self, name: str, fields: List[SchemaField]):
        self.name = name
        self.fields = fields

def validate_dataframe_schema(df: pd.DataFrame, schema: Schema) -> Dict[str, Any]:
    """Validates a DataFrame against a defined schema."""
    errors = []
    warnings = []
    for field in schema.fields:
        if field.name not in df.columns:
            if field.required:
                errors.append(f"Missing required column: {field.name}")
            continue
        
        actual_dtype = str(df[field.name].dtype)
        # Map pandas dtypes to expected string representations loosely
        expected_map = {
            "int64": ["int64", "int32", "int"],
            "float64": ["float64", "float32", "float"],
            "object": ["object", "string"],
            "bool": ["bool"]
        }
        
        if field.dtype not in expected_map.get(actual_dtype, [actual_dtype]):
            # Strict check for specific string match if not in loose map
            if field.dtype != actual_dtype:
                warnings.append(f"Column '{field.name}' has dtype {actual_dtype}, expected {field.dtype}")

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings}
    return {"valid": True, "errors": [], "warnings": warnings}

def validate_json_schema(file_path: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validates a JSON file against a simple schema definition."""
    errors = []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            errors.append("JSON root must be a list of records.")
            return {"valid": False, "errors": errors}

        if not data:
            return {"valid": True, "errors": [], "warnings": ["File is empty"]}

        sample = data[0]
        for field_name, field_type in schema.get("fields", {}).items():
            if field_name not in sample:
                if schema.get("required", True):
                    errors.append(f"Missing required field: {field_name}")
                continue
            
            val = sample[field_name]
            type_map = {
                "int": int,
                "float": float,
                "str": str,
                "bool": bool
            }
            expected_type = type_map.get(field_type)
            if expected_type and not isinstance(val, expected_type):
                errors.append(f"Field '{field_name}' has type {type(val).__name__}, expected {field_type}")

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {str(e)}")
    except FileNotFoundError:
        errors.append(f"File not found: {file_path}")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": []}

def create_processed_directories(root_path: Path) -> None:
    """Creates the data/processed directory structure if it doesn't exist."""
    processed_dir = root_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {processed_dir}")

def validate_schema_file(root_path: Path) -> Dict[str, Any]:
    """Creates and validates the schema definition file for processed metrics."""
    schemas = {
        "ablation_labels_full.json": {
            "type": "json",
            "fields": {
                "layer_id": "str",
                "utility_score": "float"
            }
        },
        "utility_labels.csv": {
            "type": "csv",
            "fields": {
                "layer_id": "int",
                "utility_score": "float",
                "turn_id": "int"
            }
        },
        "train_set.csv": {
            "type": "csv",
            "fields": {
                "trajectory_id": "str",
                "turn": "int",
                "entropy": "float",
                "utility_score": "float"
            }
        },
        "holdout_set.csv": {
            "type": "csv",
            "fields": {
                "trajectory_id": "str",
                "turn": "int",
                "entropy": "float",
                "utility_score": "float"
            }
        },
        "proxy_validation_report.json": {
            "type": "json",
            "fields": {
                "correlation": "float",
                "threshold": "float",
                "passed": "bool"
            }
        },
        "baseline_comparison.csv": {
            "type": "csv",
            "fields": {
                "condition": "str",
                "win_rate": "float",
                "avg_tokens": "float"
            }
        },
        "token_reduction_verification.json": {
            "type": "json",
            "fields": {
                "reduction_percent": "float",
                "threshold_percent": "float",
                "passed": "bool"
            }
        },
        "divergence_report.json": {
            "type": "json",
            "fields": {
                "is_divergent": "bool",
                "count": "int"
            }
        },
        "statistical_results.json": {
            "type": "json",
            "fields": {
                "p_value": "float",
                "effect_size": "float",
                "test_type": "str",
                "bonferroni_adjusted": "float",
                "divergence_status": "bool"
            }
        }
    }

    schema_path = root_path / "specs" / "schema_registry.json"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(schema_path, 'w') as f:
        json.dump(schemas, f, indent=2)
    
    return {"valid": True, "message": "Schema registry created", "path": str(schema_path)}

def validate_all_processed_files(root_path: Path) -> List[Dict[str, Any]]:
    """Validates all existing files in data/processed against their schemas."""
    processed_dir = root_path / "data" / "processed"
    results = []
    
    if not processed_dir.exists():
        return [{"valid": False, "message": "data/processed directory does not exist"}]

    registry_path = root_path / "specs" / "schema_registry.json"
    if not registry_path.exists():
        results.append({"valid": False, "message": "Schema registry not found. Run create_schema_registry first."})
        return results

    with open(registry_path, 'r') as f:
        registry = json.load(f)

    for filename, spec in registry.items():
        file_path = processed_dir / filename
        if not file_path.exists():
            results.append({"file": filename, "valid": False, "message": "File missing"})
            continue

        if spec["type"] == "json":
            schema_def = {"fields": spec["fields"]}
            res = validate_json_schema(file_path, schema_def)
            results.append({"file": filename, **res})
        elif spec["type"] == "csv":
            try:
                df = pd.read_csv(file_path)
                schema_obj = Schema(name=filename, fields=[
                    SchemaField(name=k, dtype=v) for k, v in spec["fields"].items()
                ])
                res = validate_dataframe_schema(df, schema_obj)
                results.append({"file": filename, **res})
            except Exception as e:
                results.append({"file": filename, "valid": False, "message": str(e)})
    
    return results

def write_schema_registry(root_path: Path) -> None:
    """Writes the schema registry to specs/schema_registry.json."""
    schemas = {
        "ablation_labels_full.json": {"type": "json", "fields": {"layer_id": "str", "utility_score": "float"}},
        "utility_labels.csv": {"type": "csv", "fields": {"layer_id": "int", "utility_score": "float", "turn_id": "int"}},
        "train_set.csv": {"type": "csv", "fields": {"trajectory_id": "str", "turn": "int", "entropy": "float", "utility_score": "float"}},
        "holdout_set.csv": {"type": "csv", "fields": {"trajectory_id": "str", "turn": "int", "entropy": "float", "utility_score": "float"}},
        "proxy_validation_report.json": {"type": "json", "fields": {"correlation": "float", "threshold": "float", "passed": "bool"}},
        "baseline_comparison.csv": {"type": "csv", "fields": {"condition": "str", "win_rate": "float", "avg_tokens": "float"}},
        "token_reduction_verification.json": {"type": "json", "fields": {"reduction_percent": "float", "threshold_percent": "float", "passed": "bool"}},
        "divergence_report.json": {"type": "json", "fields": {"is_divergent": "bool", "count": "int"}},
        "statistical_results.json": {"type": "json", "fields": {"p_value": "float", "effect_size": "float", "test_type": "str", "bonferroni_adjusted": "float", "divergence_status": "bool"}}
    }
    registry_path = root_path / "specs" / "schema_registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, 'w') as f:
        json.dump(schemas, f, indent=2)

def main():
    root = Path(__file__).resolve().parent.parent
    logger.info(f"Running schema validation for project at {root}")
    
    create_processed_directories(root)
    validate_schema_file(root)
    
    validation_results = validate_all_processed_files(root)
    
    all_valid = all(r.get("valid", False) for r in validation_results)
    
    report_path = root / "data" / "processed" / "schema_validation_report.json"
    with open(report_path, 'w') as f:
        json.dump({
            "valid": all_valid,
            "results": validation_results
        }, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    if all_valid:
        logger.info("All processed files are valid.")
    else:
        logger.warning("Some files failed validation.")
    
    return all_valid

if __name__ == "__main__":
    main()
