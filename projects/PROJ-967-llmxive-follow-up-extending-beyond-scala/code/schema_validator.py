import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import yaml

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"

# Required rubric dimensions (indices 0-3)
RUBRIC_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
REQUIRED_COLUMNS = [
    "image_path",
    "species_id",
    "prompt_text",
    "teacher_scores",
    "student_scalar",
    "human_annotations",
]

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

def load_provisional_schema(schema_path: Path) -> dict:
    """Load the provisional dataset schema from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Provisional schema not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def infer_actual_schema(df: pd.DataFrame) -> dict:
    """Infer the actual schema from the DataFrame."""
    inferred_fields = []
    for col in df.columns:
        sample_val = df[col].iloc[0] if len(df) > 0 else None
        inferred_type = "unknown"
        if isinstance(sample_val, (int, np.integer)):
            inferred_type = "integer"
        elif isinstance(sample_val, float):
            inferred_type = "float"
        elif isinstance(sample_val, str):
            inferred_type = "string"
        elif isinstance(sample_val, list):
            # Check if it's a list of floats (common for scores)
            if all(isinstance(x, float) for x in sample_val):
                inferred_type = "list[float]"
            else:
                inferred_type = "list"
        elif pd.isna(sample_val):
            inferred_type = "null"
        else:
            inferred_type = type(sample_val).__name__

        inferred_fields.append({"name": col, "type": inferred_type})
    return {"version": 1.0, "fields": inferred_fields}

def validate_schema(actual_schema: dict, provisional_schema: dict, df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate actual schema against provisional schema.
    Returns (is_valid, list_of_discrepancies).
    """
    discrepancies = []
    actual_fields = {f["name"]: f["type"] for f in actual_schema["fields"]}
    provisional_fields = {f["name"]: f["type"] for f in provisional_schema["fields"]}

    # Check for missing columns
    for field_name in REQUIRED_COLUMNS:
        if field_name not in actual_fields:
            discrepancies.append(f"Missing required column: {field_name}")

    # Check for rubric dimension integrity in teacher_scores and human_annotations
    if "teacher_scores" in actual_fields:
        # Validate length of list if possible (requires checking a sample)
        # For schema level, we assume list[float] is correct if present
        if actual_fields["teacher_scores"] != "list[float]":
            discrepancies.append(f"teacher_scores expected list[float], got {actual_fields['teacher_scores']}")

    if "human_annotations" in actual_fields:
        if actual_fields["human_annotations"] != "list[float]":
            discrepancies.append(f"human_annotations expected list[float], got {actual_fields['human_annotations']}")

    # Check for extra columns not in provisional (warning, not error)
    extra_cols = set(actual_fields.keys()) - set(provisional_fields.keys())
    if extra_cols:
        discrepancies.append(f"Extra columns not in provisional schema: {extra_cols}")

    # Check for missing columns in actual that are in provisional
    missing_in_actual = set(provisional_fields.keys()) - set(actual_fields.keys())
    if missing_in_actual:
        discrepancies.append(f"Columns in provisional but missing in actual: {missing_in_actual}")

    is_valid = len([d for d in discrepancies if d.startswith("Missing required") or d.endswith("expected list[float]")]) == 0
    return is_valid, discrepancies

def update_schema_file(actual_schema: dict, schema_path: Path):
    """Overwrite the provisional schema file with the discovered schema."""
    with open(schema_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(actual_schema, f, default_flow_style=False, sort_keys=False)
    logging.info(f"Updated schema file at {schema_path}")

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    # 1. Determine input file
    primary_path = DATA_RAW_DIR / "oxford_pets_simulated.parquet"
    fallback_path = DATA_RAW_DIR / "mock_oxford_pets.parquet"

    if primary_path.exists():
        input_file = primary_path
        logger.info(f"Using primary dataset: {input_file}")
    elif fallback_path.exists():
        input_file = fallback_path
        logger.warning(f"Primary dataset missing. Using fallback: {input_file}")
    else:
        raise FileNotFoundError(
            f"Neither primary ({primary_path}) nor fallback ({fallback_path}) dataset found. "
            "Please run T037-deterministic-sim or T037b first."
        )

    # 2. Load data
    try:
        df = pd.read_parquet(input_file)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset from {input_file}: {e}")

    if df.empty:
        raise ValueError("Dataset is empty. Cannot infer schema.")

    logger.info(f"Loaded {len(df)} samples from {input_file}")

    # 3. Load provisional schema
    if not SCHEMA_PATH.exists():
        logger.warning(f"Provisional schema not found at {SCHEMA_PATH}. Creating new one.")
        # If file doesn't exist, we can't validate against it, so we just write the inferred one
        provisional_schema = None
    else:
        provisional_schema = load_provisional_schema(SCHEMA_PATH)

    # 4. Infer actual schema
    actual_schema = infer_actual_schema(df)

    # 5. Validate
    if provisional_schema:
        is_valid, discrepancies = validate_schema(actual_schema, provisional_schema, df)
        if discrepancies:
            logger.warning("Schema validation found discrepancies:")
            for d in discrepancies:
                logger.warning(f"  - {d}")
            if not is_valid:
                logger.error("Critical schema mismatch. Aborting.")
                sys.exit(1)
        else:
            logger.info("Schema validation passed. No discrepancies found.")

        # 6. Update schema if needed (even if valid, we update to reflect reality)
        logger.info("Updating schema file with discovered schema...")
        update_schema_file(actual_schema, SCHEMA_PATH)
    else:
        logger.info("No provisional schema found. Writing inferred schema.")
        update_schema_file(actual_schema, SCHEMA_PATH)

    logger.info("Schema discovery and validation completed successfully.")

if __name__ == "__main__":
    main()
