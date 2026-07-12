import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaField:
    """Represents a single field in a schema definition."""
    def __init__(self, name: str, dtype: str, required: bool = True, description: str = ""):
        self.name = name
        self.dtype = dtype
        self.required = required
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "required": self.required,
            "description": self.description
        }

class Schema:
    """Represents a schema for a processed dataset."""
    def __init__(self, name: str, fields: List[SchemaField], description: str = ""):
        self.name = name
        self.fields = fields
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields]
        }

def validate_dataframe_schema(df: pd.DataFrame, schema: Schema) -> Dict[str, Any]:
    """
    Validates a DataFrame against a Schema definition.
    Returns a report dict with 'valid' (bool) and 'errors' (list).
    """
    errors = []
    existing_cols = set(df.columns)
    
    for field in schema.fields:
        if field.name not in existing_cols:
            if field.required:
                errors.append(f"Missing required column: {field.name}")
            continue
        
        # Check dtype compatibility
        actual_dtype = str(df[field.name].dtype)
        # Map pandas dtypes to generic types for comparison
        expected_type = field.dtype.lower()
        
        type_mapping = {
            'int': ['int64', 'int32', 'int'],
            'float': ['float64', 'float32', 'float'],
            'string': ['object', 'string', 'str'],
            'bool': ['bool', 'boolean']
        }
        
        valid_types = type_mapping.get(expected_type, [expected_type])
        if actual_dtype not in valid_types:
            errors.append(f"Column '{field.name}' has dtype {actual_dtype}, expected {expected_type}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "schema_name": schema.name,
        "row_count": len(df)
    }

def create_processed_directories(base_dir: Path) -> None:
    """
    Creates the data/processed directory structure and schema registry file.
    """
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a placeholder registry if it doesn't exist
    registry_path = processed_dir / "schema_registry.json"
    if not registry_path.exists():
        registry = {
            "version": "1.0",
            "schemas": {}
        }
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        logger.info(f"Created schema registry at {registry_path}")
    
    logger.info(f"Ensured processed directory exists at {processed_dir}")

def validate_schema_file(schema_path: Path) -> Optional[Schema]:
    """
    Loads and validates a schema definition file (JSON).
    Returns the Schema object if valid, None otherwise.
    """
    try:
        with open(schema_path, 'r') as f:
            data = json.load(f)
        
        fields = []
        for field_data in data.get("fields", []):
            fields.append(SchemaField(
                name=field_data["name"],
                dtype=field_data["dtype"],
                required=field_data.get("required", True),
                description=field_data.get("description", "")
            ))
        
        return Schema(
            name=data.get("name", "unknown"),
            fields=fields,
            description=data.get("description", "")
        )
    except Exception as e:
        logger.error(f"Failed to load schema from {schema_path}: {e}")
        return None

def validate_all_processed_files(base_dir: Path) -> Dict[str, Any]:
    """
    Scans data/processed/ for CSV files and validates them against registered schemas.
    """
    processed_dir = base_dir / "data" / "processed"
    registry_path = processed_dir / "schema_registry.json"
    
    if not processed_dir.exists():
        return {"valid": False, "error": "Processed directory does not exist"}
    
    if not registry_path.exists():
        return {"valid": False, "error": "Schema registry not found"}
    
    with open(registry_path, 'r') as f:
        registry = json.load(f)
    
    results = {}
    all_valid = True
    
    for csv_file in processed_dir.glob("*.csv"):
        file_name = csv_file.stem
        if file_name in registry.get("schemas", {}):
            schema_data = registry["schemas"][file_name]
            # Reconstruct schema object for validation
            fields = [SchemaField(**f) for f in schema_data.get("fields", [])]
            schema = Schema(name=file_name, fields=fields)
            
            try:
                df = pd.read_csv(csv_file)
                validation_result = validate_dataframe_schema(df, schema)
                results[file_name] = validation_result
                if not validation_result["valid"]:
                    all_valid = False
                    logger.warning(f"Validation failed for {csv_file}: {validation_result['errors']}")
                else:
                    logger.info(f"Validation passed for {csv_file}: {validation_result['row_count']} rows")
            except Exception as e:
                results[file_name] = {"valid": False, "errors": [str(e)]}
                all_valid = False
        else:
            logger.info(f"No schema registered for {csv_file}, skipping validation")
    
    return {
        "valid": all_valid,
        "results": results,
        "total_files_checked": len(results)
    }

def write_schema_registry(base_dir: Path, schemas: Dict[str, Schema]) -> None:
    """
    Writes the schema registry to data/processed/schema_registry.json.
    """
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    registry_path = processed_dir / "schema_registry.json"
    
    registry = {
        "version": "1.0",
        "schemas": {}
    }
    
    for name, schema in schemas.items():
        registry["schemas"][name] = schema.to_dict()
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    logger.info(f"Wrote schema registry to {registry_path}")

def main():
    """
    Main entry point to initialize the processed directory structure 
    and validate existing files against the registry.
    """
    base_dir = Path.cwd()
    create_processed_directories(base_dir)
    
    # Define standard schemas for this project
    utility_labels_schema = Schema(
        name="utility_labels",
        fields=[
            SchemaField("trajectory_id", "string", True, "Unique ID for the trajectory"),
            SchemaField("turn_id", "int", True, "Turn number within trajectory"),
            SchemaField("layer_id", "int", True, "Layer index being evaluated"),
            SchemaField("utility_score", "float", True, "Utility score from ablation"),
            SchemaField("entropy", "float", False, "Shannon entropy at this turn")
        ],
        description="Derived utility labels from ablation study"
    )
    
    train_set_schema = Schema(
        name="train_set",
        fields=[
            SchemaField("trajectory_id", "string", True, "Unique ID for the trajectory"),
            SchemaField("features", "string", True, "JSON string of feature vector"),
            SchemaField("utility_score", "float", True, "Target utility score")
        ],
        description="Training split of processed data"
    )
    
    holdout_set_schema = Schema(
        name="holdout_set",
        fields=[
            SchemaField("trajectory_id", "string", True, "Unique ID for the trajectory"),
            SchemaField("features", "string", True, "JSON string of feature vector"),
            SchemaField("utility_score", "float", True, "Target utility score")
        ],
        description="Hold-out validation split of processed data"
    )
    
    baseline_comparison_schema = Schema(
        name="baseline_comparison",
        fields=[
            SchemaField("condition", "string", True, "Agent condition (Dynamic, Static, Random)"),
            SchemaField("win_rate", "float", True, "Average win rate"),
            SchemaField("avg_tokens", "float", True, "Average token usage")
        ],
        description="Aggregated baseline comparison metrics"
    )
    
    schemas = {
        "utility_labels": utility_labels_schema,
        "train_set": train_set_schema,
        "holdout_set": holdout_set_schema,
        "baseline_comparison": baseline_comparison_schema
    }
    
    write_schema_registry(base_dir, schemas)
    
    # Validate any existing files
    validation_report = validate_all_processed_files(base_dir)
    
    if validation_report["valid"]:
        print("All processed files validated successfully.")
    else:
        print("Validation issues found:")
        for name, res in validation_report.get("results", {}).items():
            if not res.get("valid", True):
                print(f"  - {name}: {res.get('errors', [])}")
    
    return validation_report

if __name__ == "__main__":
    main()
