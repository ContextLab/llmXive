import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis" / "contracts"

REQUIRED_COLUMNS = [
    "prompt",
    "image_url",
    "teacher_scores",
    "student_scalar",
    "human_annotations",
    "primary_dimension"
]

RUBRIC_KEYS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], schema_path: Path):
    """Save a schema definition to YAML."""
    with open(schema_path, "w") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(data_path: Path) -> pd.DataFrame:
    """Load the raw dataset (Parquet) into a DataFrame."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")
    
    # Try to infer format from extension or just try parquet
    if data_path.suffix == ".parquet":
        return pd.read_parquet(data_path)
    elif data_path.suffix == ".csv":
        return pd.read_csv(data_path)
    else:
        # Default to parquet as per T037 output
        return pd.read_parquet(data_path)

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Discover the actual schema of the dataframe.
    Returns a structure compatible with the project's schema format.
    """
    fields = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        field = {
            "name": col,
            "type": dtype
        }
        
        # Special handling for complex types if they are dicts/objects
        if col in ["teacher_scores", "human_annotations"]:
            # Check if it's a stringified JSON or actual dict
            sample = df[col].iloc[0] if len(df) > 0 else None
            if isinstance(sample, dict):
                field["type"] = "object"
                field["properties"] = {}
                for key in sample.keys():
                    # Infer type of property
                    val_type = str(type(sample[key]).__name__)
                    if val_type == "float":
                        field["properties"][key] = "float"
                    elif val_type == "int":
                        field["properties"][key] = "int"
                    else:
                        field["properties"][key] = "string"
            else:
                # Fallback if stored as string
                field["type"] = "string"
        
        fields.append(field)
    
    return {
        "schema_version": "1.0",
        "discovered_from": str(data_path),
        "fields": fields
    }

def validate_schema(discovered: Dict[str, Any], template: Dict[str, Any]) -> List[str]:
    """
    Compare discovered schema against the template.
    Returns a list of discrepancies/errors.
    """
    errors = []
    discovered_fields = {f["name"]: f for f in discovered["fields"]}
    template_fields = {f["name"]: f for f in template["fields"]}

    # Check for missing required columns
    for req_col in REQUIRED_COLUMNS:
        if req_col not in discovered_fields:
            errors.append(f"CRITICAL: Missing required column '{req_col}'")

    # Check for rubric keys inside teacher_scores and human_annotations
    if "teacher_scores" in discovered_fields:
        ts_field = discovered_fields["teacher_scores"]
        if "properties" in ts_field:
          missing_rubric = [k for k in RUBRIC_KEYS if k not in ts_field["properties"]]
          if missing_rubric:
              errors.append(f"CRITICAL: Missing rubric keys in 'teacher_scores': {missing_rubric}")
        else:
            errors.append("CRITICAL: 'teacher_scores' is not an object with properties")

    if "human_annotations" in discovered_fields:
        ha_field = discovered_fields["human_annotations"]
        if "properties" in ha_field:
            missing_rubric = [k for k in RUBRIC_KEYS if k not in ha_field["properties"]]
            if missing_rubric:
                errors.append(f"CRITICAL: Missing rubric keys in 'human_annotations': {missing_rubric}")
        else:
            errors.append("CRITICAL: 'human_annotations' is not an object with properties")

    # Check for primary_dimension
    if "primary_dimension" not in discovered_fields:
        errors.append("WARNING: 'primary_dimension' column missing, will use fallback logic in T014")

    return errors

def update_contract(discovered: Dict[str, Any], template: Dict[str, Any], output_path: Path):
    """
    Merge discovered schema with template logic to create the validated schema.
    If discrepancies exist (missing columns), we raise an error as per task spec.
    If only type mismatches or extra columns, we update the template to match reality.
    """
    errors = validate_schema(discovered, template)
    
    critical_errors = [e for e in errors if e.startswith("CRITICAL")]
    if critical_errors:
        raise RuntimeError(f"Schema validation failed with critical errors:\n" + "\n".join(critical_errors))

    # If we get here, the core structure is valid. 
    # We update the template to reflect the actual discovered types and any extra columns.
    final_schema = {
        "schema_version": "1.0",
        "validated_from": discovered.get("discovered_from", "unknown"),
        "fields": []
    }

    # Start with discovered fields as the source of truth for types
    for field in discovered["fields"]:
        final_schema["fields"].append(field)

    # Ensure required structure matches template expectations if types were vague
    # (e.g. ensure teacher_scores has properties if discovered as object)
    # The 'discover_schema' function already attempts to extract properties.
    
    save_schema(final_schema, output_path)
    return final_schema

def parse_args():
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation for Z-Reward Dataset")
    parser.add_argument(
        "--input-data",
        type=str,
        default=str(DATA_RAW_DIR / "z_reward.parquet"),
        help="Path to the raw dataset file (default: data/raw/z_reward.parquet)"
    )
    parser.add_argument(
        "--template-schema",
        type=str,
        default=str(CONTRACTS_DIR / "dataset.schema.yaml"),
        help="Path to the provisional schema template (default: contracts/dataset.schema.yaml)"
    )
    parser.add_argument(
        "--output-schema",
        type=str,
        default=str(CONTRACTS_DIR / "dataset.validated.schema.yaml"),
        help="Path to write the validated schema (default: contracts/dataset.validated.schema.yaml)"
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    data_path = Path(args.input_data)
    template_path = Path(args.template_schema)
    output_path = Path(args.output_schema)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading dataset from: {data_path}")
    try:
        df = load_dataset(data_path)
        logger.info(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    logger.info(f"Loading schema template from: {template_path}")
    try:
        template_schema = load_schema(template_path)
    except Exception as e:
        logger.error(f"Failed to load schema template: {e}")
        sys.exit(1)

    logger.info("Discovering schema...")
    discovered_schema = discover_schema(df)

    logger.info("Validating schema against template...")
    try:
        final_schema = update_contract(discovered_schema, template_schema, output_path)
        logger.info(f"Schema validation successful. Validated schema written to: {output_path}")
        logger.info(f"Final fields count: {len(final_schema['fields'])}")
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # Summary output
    logger.info("Schema Discovery Complete.")

if __name__ == "__main__":
    main()
