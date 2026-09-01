import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import yaml
import jsonschema

# Import existing utilities from the project
from utils.config import get_specs_path, get_processed_path, get_output_path
from utils.logging_config import get_logger, log_error_context
from utils.validators import validate_file_exists

logger = get_logger(__name__)

SCHEMA_PATH = Path("specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml")
INPUT_DATA_PATH = Path("data/processed/cleared_with_diversity.csv")
OUTPUT_REPORT_PATH = Path("data/results/schema_validation_report.json")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the dataframe against the JSON-schema-like YAML definition.
    The schema provided is a simplified object schema, not a full JSON Schema draft.
    We adapt the validation logic to match the specific structure provided in the task.
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "stats": {
            "total_rows": len(df),
            "columns_found": list(df.columns),
            "required_columns_found": []
        }
    }

    # 1. Check required top-level keys
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # The schema defines 'taxa_abundances' as an object, but our CSV has flattened columns.
    # We map the schema's 'taxa_abundances' requirement to the presence of taxon columns.
    # We map 'subject_id', 'titer_baseline', 'titer_post' to direct columns.
    
    missing_required = []
    found_required = []

    for field in required_fields:
        if field == "taxa_abundances":
            # Check if there are any columns that look like taxon abundances (not metadata)
            # Heuristic: columns that are not subject_id, titer_baseline, titer_post, 
            # shannon_diversity, log_titer, taxa_clr
            meta_cols = {'subject_id', 'titer_baseline', 'titer_post', 
                         'shannon_diversity', 'log_titer', 'taxa_clr'}
            potential_taxa = [c for c in df.columns if c not in meta_cols]
            if not potential_taxa:
                missing_required.append("taxa_abundances (no taxon columns found)")
            else:
                found_required.append("taxa_abundances")
        elif field in df.columns:
            found_required.append(field)
        else:
            missing_required.append(field)

    results["stats"]["required_columns_found"] = found_required

    if missing_required:
        results["valid"] = False
        results["errors"].append(f"Missing required fields: {missing_required}")
        logger.error(f"Schema validation failed: Missing required fields {missing_required}")
        return results

    # 2. Validate types for specific columns
    # subject_id: string
    if "subject_id" in df.columns:
        if not pd.api.types.is_string_dtype(df["subject_id"]) and not pd.api.types.is_object_dtype(df["subject_id"]):
            results["valid"] = False
            results["errors"].append("subject_id must be of type string")
            logger.error("Validation error: subject_id is not string type")
        elif df["subject_id"].isna().any():
            results["valid"] = False
            results["errors"].append("subject_id contains null values")
            logger.error("Validation error: subject_id contains null values")

    # titer_baseline: number
    if "titer_baseline" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["titer_baseline"]):
            results["valid"] = False
            results["errors"].append("titer_baseline must be numeric")
            logger.error("Validation error: titer_baseline is not numeric")
        elif df["titer_baseline"].isna().any():
            results["valid"] = False
            results["errors"].append("titer_baseline contains null values")
            logger.error("Validation error: titer_baseline contains null values")

    # titer_post: number
    if "titer_post" in df.columns:
        if not pd.api.types.is_numeric_dtype(df["titer_post"]):
            results["valid"] = False
            results["errors"].append("titer_post must be numeric")
            logger.error("Validation error: titer_post is not numeric")
        elif df["titer_post"].isna().any():
            results["valid"] = False
            results["errors"].append("titer_post contains null values")
            logger.error("Validation error: titer_post contains null values")

    # 3. Validate taxa_abundances (flattened columns) are numbers
    # We assume any column not in the known metadata list is a taxon abundance
    meta_cols = {'subject_id', 'titer_baseline', 'titer_post', 
                 'shannon_diversity', 'log_titer', 'taxa_clr'}
    taxon_cols = [c for c in df.columns if c not in meta_cols]
    
    for col in taxon_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            results["valid"] = False
            results["errors"].append(f"Taxon column '{col}' must be numeric")
            logger.error(f"Validation error: Taxon column {col} is not numeric")
        elif df[col].isna().any():
            results["valid"] = False
            results["errors"].append(f"Taxon column '{col}' contains null values")
            logger.error(f"Validation error: Taxon column {col} contains null values")

    if results["valid"]:
        logger.info("Schema validation passed successfully.")
    else:
        logger.warning(f"Schema validation failed with {len(results['errors'])} errors.")

    return results

def run_validation():
    """Main entry point for schema validation."""
    logger.info("Starting schema validation task T013.")
    
    # Ensure paths exist
    if not INPUT_DATA_PATH.exists():
        raise FileNotFoundError(f"Input data file not found: {INPUT_DATA_PATH}")
    
    schema = load_schema(SCHEMA_PATH)
    
    try:
        df = pd.read_csv(INPUT_DATA_PATH)
        logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns.")
        
        validation_result = validate_csv_against_schema(df, schema)
        
        # Ensure output directory exists
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(OUTPUT_REPORT_PATH, 'w') as f:
            json.dump(validation_result, f, indent=2)
        
        logger.info(f"Validation report written to {OUTPUT_REPORT_PATH}")
        
        if not validation_result["valid"]:
            logger.error("Validation failed. Exiting with error code.")
            sys.exit(1)
        
        return validation_result

    except Exception as e:
        log_error_context("Error during schema validation", e)
        sys.exit(1)

def main():
    run_validation()

if __name__ == "__main__":
    main()