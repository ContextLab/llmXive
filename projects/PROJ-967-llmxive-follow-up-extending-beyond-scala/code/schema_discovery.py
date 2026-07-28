import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the expected schema template."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema template not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """Save the validated schema to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(data_path: Path) -> pd.DataFrame:
    """Load the dataset from Parquet."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    logger.info(f"Loading dataset from {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def discover_schema(df: pd.DataFrame, expected_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Discover the actual schema from the dataframe and map it to logical fields.
    Returns an updated schema definition.
    """
    actual_columns = set(df.columns)
    discovered_fields = []
    critical_logical_fields = ["prompt", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]
    found_critical = []

    # Map logical fields to actual columns
    logical_mapping = {
        "prompt": "prompt",
        "image_url": "image_url",
        "teacher_scores": "teacher_scores",
        "student_scalar": "student_scalar",
        "human_annotations": "human_annotations",
        "primary_dimension": "primary_dimension",
        "sample_id": "sample_id",
        "excluded_reason": "excluded_reason"
    }

    for logical, potential_cols in logical_mapping.items():
        # Check if the exact column name exists
        if potential_cols in actual_columns:
            col_type = df[potential_cols].dtype
            if logical in ["teacher_scores", "human_annotations"]:
                # These are object/dict columns, infer structure from sample
                sample_val = df[potential_cols].iloc[0] if len(df) > 0 else {}
                dims = list(sample_val.keys()) if isinstance(sample_val, dict) else []
                discovered_fields.append({
                    "name": logical,
                    "type": "object",
                    "logical_field": logical,
                    "source_column": potential_cols,
                    "required": True,
                    "dimensions": dims
                })
            else:
                discovered_fields.append({
                    "name": logical,
                    "type": str(col_type),
                    "logical_field": logical,
                    "source_column": potential_cols,
                    "required": logical in critical_logical_fields
                })
            if logical in critical_logical_fields:
                found_critical.append(logical)
        else:
            # Check for variations if exact match fails
            found = False
            for col in actual_columns:
                if col.lower().replace("_", "") == logical.lower().replace("_", ""):
                    discovered_fields.append({
                        "name": logical,
                        "type": str(df[col].dtype),
                        "logical_field": logical,
                        "source_column": col,
                        "required": logical in critical_logical_fields,
                        "note": f"Matched via fuzzy: {col}"
                    })
                    if logical in critical_logical_fields:
                        found_critical.append(logical)
                    found = True
                    break
            if not found:
                if logical in critical_logical_fields:
                    logger.warning(f"Critical field '{logical}' not found in dataset!")

    # Validate dimensions in teacher_scores and human_annotations
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    if "teacher_scores" in df.columns:
        sample_t = df["teacher_scores"].iloc[0]
        if isinstance(sample_t, dict):
            if not all(d in sample_t for d in dimensions):
                logger.warning(f"Teacher scores missing expected dimensions. Found: {list(sample_t.keys())}")

    return {
        "schema": {
            "description": "Validated schema for Z-Reward dataset after T038 discovery",
            "version": "1.0.0",
            "derived_from": str(data_path),
            "fields": discovered_fields
        },
        "validation_status": "PASSED" if set(found_critical) == set(critical_logical_fields) else "FAILED",
        "critical_columns_found": found_critical,
        "mapping_notes": f"Schema discovered from {data_path.name}. Critical fields: {found_critical}"
    }

def validate_schema(discovered: Dict[str, Any]) -> bool:
    """Validate that critical fields are present."""
    status = discovered.get("validation_status", "FAILED")
    return status == "PASSED"

def update_contract(discovered: Dict[str, Any], output_path: Path) -> None:
    """Write the validated schema to the output contract file."""
    save_schema(discovered, output_path)
    logger.info(f"Validated schema saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument(
        "--input-data",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "raw_data.parquet",
        help="Path to input parquet file"
    )
    parser.add_argument(
        "--template-schema",
        type=Path,
        default=PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis" / "contracts" / "dataset.schema.yaml",
        help="Path to template schema YAML"
    )
    parser.add_argument(
        "--output-schema",
        type=Path,
        default=PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis" / "contracts" / "dataset.validated.schema.yaml",
        help="Path to output validated schema YAML"
    )
    return parser.parse_args()

def main():
    global logger
    logger = setup_logging()
    args = parse_args()

    logger.info(f"Starting schema discovery for {args.input_data}")

    # Load template
    try:
        template = load_schema(args.template_schema)
        logger.info(f"Loaded template schema from {args.template_schema}")
    except FileNotFoundError as e:
        logger.error(f"Template schema missing: {e}")
        # Create a minimal template if missing to allow discovery to proceed
        template = {"schema": {"fields": []}}

    # Load data
    try:
        df = load_dataset(args.input_data)
    except FileNotFoundError as e:
        logger.critical(f"Input data missing: {e}")
        sys.exit(1)

    # Discover
    discovered = discover_schema(df, template)

    # Validate
    is_valid = validate_schema(discovered)
    if not is_valid:
        logger.error("Schema validation FAILED. Critical fields missing.")
        # Still write the discovered schema for debugging
        update_contract(discovered, args.output_schema)
        sys.exit(1)

    # Write
    update_contract(discovered, args.output_schema)
    logger.info("Schema discovery and validation completed successfully.")

if __name__ == "__main__":
    main()
