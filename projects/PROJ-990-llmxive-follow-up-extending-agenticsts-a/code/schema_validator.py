import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass, field
import csv

from config import ensure_directories, load_config_from_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SchemaField:
    name: str
    dtype: str
    nullable: bool = False
    description: str = ""

@dataclass
class Schema:
    name: str
    fields: List[SchemaField]
    description: str = ""

# Define schemas for processed data files
SCHEMAS = {
    "utility_labels": Schema(
        name="utility_labels",
        fields=[
            SchemaField(name="layer_id", dtype="int64", nullable=False, description="Unique identifier for the layer"),
            SchemaField(name="utility_score", dtype="float64", nullable=False, description="Calculated utility score from ablation"),
            SchemaField(name="turn_id", dtype="int64", nullable=False, description="Turn identifier from original trajectory"),
            SchemaField(name="entropy", dtype="float64", nullable=True, description="Shannon entropy at this turn"),
        ],
        description="Structured training labels derived from ablation study"
    ),
    "train_set": Schema(
        name="train_set",
        fields=[
            SchemaField(name="trajectory_id", dtype="object", nullable=False, description="Unique trajectory identifier"),
            SchemaField(name="turn_id", dtype="int64", nullable=False, description="Turn number within trajectory"),
            SchemaField(name="health", dtype="float64", nullable=True, description="Agent health at this turn"),
            SchemaField(name="threat", dtype="float64", nullable=True, description="Threat level at this turn"),
            SchemaField(name="deck_size", dtype="int64", nullable=True, description="Deck size at this turn"),
            SchemaField(name="entropy", dtype="float64", nullable=True, description="Shannon entropy of move distribution"),
            SchemaField(name="utility_score", dtype="float64", nullable=False, description="Ground truth utility score"),
        ],
        description="Training split of processed trajectories with utility labels"
    ),
    "holdout_set": Schema(
        name="holdout_set",
        fields=[
            SchemaField(name="trajectory_id", dtype="object", nullable=False, description="Unique trajectory identifier"),
            SchemaField(name="turn_id", dtype="int64", nullable=False, description="Turn number within trajectory"),
            SchemaField(name="health", dtype="float64", nullable=True, description="Agent health at this turn"),
            SchemaField(name="threat", dtype="float64", nullable=True, description="Threat level at this turn"),
            SchemaField(name="deck_size", dtype="int64", nullable=True, description="Deck size at this turn"),
            SchemaField(name="entropy", dtype="float64", nullable=True, description="Shannon entropy of move distribution"),
            SchemaField(name="utility_score", dtype="float64", nullable=False, description="Ground truth utility score"),
        ],
        description="Hold-out split of processed trajectories for validation"
    ),
    "ablation_labels_full": Schema(
        name="ablation_labels_full",
        fields=[
            SchemaField(name="layer_id", dtype="int64", nullable=False, description="Layer identifier"),
            SchemaField(name="utility_score", dtype="float64", nullable=False, description="Utility score from ablation"),
            SchemaField(name="trajectory_id", dtype="object", nullable=False, description="Source trajectory"),
            SchemaField(name="turn_id", dtype="int64", nullable=False, description="Turn identifier"),
        ],
        description="Full ablation study results (ground truth labels)"
    ),
    "proxy_validation_report": Schema(
        name="proxy_validation_report",
        fields=[
            SchemaField(name="correlation_coefficient", dtype="float64", nullable=False, description="Pearson correlation between proxy and ground truth"),
            SchemaField(name="sample_size", dtype="int64", nullable=False, description="Number of samples evaluated"),
            SchemaField(name="validation_passed", dtype="bool", nullable=False, description="Whether correlation >= 0.7"),
        ],
        description="Validation report for static log proxy against ablation ground truth"
    ),
    "baseline_comparison": Schema(
        name="baseline_comparison",
        fields=[
            SchemaField(name="condition", dtype="object", nullable=False, description="Experimental condition (Dynamic, Static, Random)"),
            SchemaField(name="win_rate", dtype="float64", nullable=False, description="Mean win rate for condition"),
            SchemaField(name="avg_tokens", dtype="float64", nullable=False, description="Mean token usage for condition"),
        ],
        description="Aggregated baseline comparison results"
    ),
    "token_reduction_verification": Schema(
        name="token_reduction_verification",
        fields=[
            SchemaField(name="passed", dtype="bool", nullable=False, description="Whether token reduction >= 30%"),
            SchemaField(name="dynamic_avg_tokens", dtype="float64", nullable=False, description="Average tokens for dynamic policy"),
            SchemaField(name="static_avg_tokens", dtype="float64", nullable=False, description="Average tokens for static baseline"),
            SchemaField(name="reduction_percentage", dtype="float64", nullable=False, description="Calculated reduction percentage"),
        ],
        description="Verification of token budget compliance and reduction"
    ),
    "divergence_report": Schema(
        name="divergence_report",
        fields=[
            SchemaField(name="is_divergent", dtype="bool", nullable=False, description="Whether trajectories diverged"),
            SchemaField(name="divergence_count", dtype="int64", nullable=False, description="Number of divergent pairs"),
            SchemaField(name="total_pairs", dtype="int64", nullable=False, description="Total trajectory pairs analyzed"),
        ],
        description="Report on trajectory divergence between dynamic and static runs"
    ),
    "statistical_results": Schema(
        name="statistical_results",
        fields=[
            SchemaField(name="p_value", dtype="float64", nullable=False, description="Raw p-value from statistical test"),
            SchemaField(name="effect_size", dtype="float64", nullable=True, description="Calculated effect size"),
            SchemaField(name="test_type", dtype="object", nullable=False, description="Type of statistical test used"),
            SchemaField(name="bonferroni_adjusted", dtype="float64", nullable=False, description="Bonferroni corrected p-value"),
            SchemaField(name="divergence_status", dtype="bool", nullable=False, description="Divergence status from report"),
        ],
        description="Final statistical testing results with corrections"
    )
}

def validate_dataframe_schema(df: pd.DataFrame, schema: Schema, file_path: str) -> bool:
    """
    Validate that a DataFrame matches the expected schema.
    
    Args:
        df: DataFrame to validate
        schema: Expected schema definition
        file_path: Path of the file being validated (for logging)
        
    Returns:
        True if validation passes, False otherwise
    """
    errors = []
    
    # Check required columns
    expected_columns = {field.name for field in schema.fields}
    actual_columns = set(df.columns)
    missing_columns = expected_columns - actual_columns
    
    if missing_columns:
        errors.append(f"Missing columns: {missing_columns}")
    
    # Check data types
    for field in schema.fields:
        if field.name in df.columns:
            series = df[field.name]
            
            # Type mapping from schema to pandas dtype
            type_map = {
                "int64": ["int64", "int32", "int16", "int8"],
                "float64": ["float64", "float32"],
                "object": ["object", "string"],
                "bool": ["bool"],
            }
            
            expected_types = type_map.get(field.dtype, [field.dtype])
            actual_dtype = str(series.dtype)
            
            if not any(expected in actual_dtype for expected in expected_types):
                errors.append(f"Column '{field.name}': expected {field.dtype}, got {actual_dtype}")
            
            # Check nullability
            if not field.nullable and series.isna().any():
                errors.append(f"Column '{field.name}': contains null values but nullable=False")
    
    if errors:
        logger.error(f"Schema validation failed for {file_path}:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info(f"Schema validation passed for {file_path}")
    return True

def create_processed_directories() -> Path:
    """Create the data/processed/ directory structure."""
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory: {processed_dir}")
    return processed_dir

def validate_schema_file(file_path: Path, schema_name: str) -> bool:
    """
    Validate a specific data file against its schema.
    
    Args:
        file_path: Path to the file to validate
        schema_name: Name of the schema to validate against (key in SCHEMAS)
        
    Returns:
        True if validation passes, False otherwise
    """
    if not schema_name in SCHEMAS:
        logger.error(f"Unknown schema: {schema_name}")
        return False
    
    schema = SCHEMAS[schema_name]
    
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False
    
    try:
        # Determine file type and load
        suffix = file_path.suffix.lower()
        
        if suffix == '.csv':
            df = pd.read_csv(file_path)
        elif suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle both list of records and single object
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    # If it's a single object, wrap it in a list
                    df = pd.DataFrame([data])
                else:
                    logger.error(f"Unexpected JSON structure in {file_path}")
                    return False
        else:
            logger.error(f"Unsupported file format: {suffix}")
            return False
        
        return validate_dataframe_schema(df, schema, str(file_path))
        
    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False

def validate_all_processed_files() -> bool:
    """
    Validate all expected files in data/processed/ against their schemas.
    
    Returns:
        True if all validations pass, False otherwise
    """
    processed_dir = Path("data/processed")
    if not processed_dir.exists():
        logger.error("data/processed/ directory does not exist")
        return False
    
    # Mapping of expected files to their schema names
    file_schema_map = {
        "utility_labels.csv": "utility_labels",
        "train_set.csv": "train_set",
        "holdout_set.csv": "holdout_set",
        "ablation_labels_full.json": "ablation_labels_full",
        "proxy_validation_report.json": "proxy_validation_report",
        "baseline_comparison.csv": "baseline_comparison",
        "token_reduction_verification.json": "token_reduction_verification",
        "divergence_report.json": "divergence_report",
        "statistical_results.json": "statistical_results",
    }
    
    all_passed = True
    
    for filename, schema_name in file_schema_map.items():
        file_path = processed_dir / filename
        if file_path.exists():
            if not validate_schema_file(file_path, schema_name):
                all_passed = False
        else:
            logger.info(f"File not yet created (expected later in pipeline): {filename}")
    
    return all_passed

def write_schema_registry() -> Path:
    """
    Write a schema registry file documenting all expected schemas.
    
    Returns:
        Path to the written registry file
    """
    registry = {
        "version": "1.0",
        "schemas": {}
    }
    
    for name, schema in SCHEMAS.items():
        registry["schemas"][name] = {
            "description": schema.description,
            "fields": [
                {
                    "name": f.name,
                    "dtype": f.dtype,
                    "nullable": f.nullable,
                    "description": f.description
                }
                for f in schema.fields
            ]
        }
    
    registry_path = Path("data/processed/schema_registry.json")
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    logger.info(f"Schema registry written to {registry_path}")
    return registry_path

def main():
    """Main entry point for schema validation and directory creation."""
    logger.info("Starting T007: Create data/processed/ directory structure and schema validation")
    
    # Load config
    config = load_config_from_file()
    
    # Create directories
    processed_dir = create_processed_directories()
    
    # Write schema registry
    write_schema_registry()
    
    # Validate any existing files
    if validate_all_processed_files():
        logger.info("All existing processed files validated successfully")
    else:
        logger.warning("Some existing files failed validation (may be expected if pipeline not complete)")
    
    logger.info("T007 completed successfully")
    return True

if __name__ == "__main__":
    main()
