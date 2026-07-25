import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

REQUIRED_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
REQUIRED_HUMAN_COLS_PREFIX = "human_annotation_"

logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the current schema contract from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema contract not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_schema(schema: Dict[str, Any], schema_path: Path) -> None:
    """Save the updated schema contract to YAML."""
    with open(schema_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)


def load_dataset(parquet_path: Path) -> pd.DataFrame:
    """Load the Z-Reward dataset from Parquet."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {parquet_path}")
    logger.info(f"Loading dataset from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
    return df


def discover_schema(df: pd.DataFrame, current_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform schema discovery: map actual columns to logical fields.
    Updates the schema contract with actual column names and types.
    """
    actual_columns = list(df.columns)
    logger.info(f"Discovered columns: {actual_columns}")

    updated_schema = current_schema.copy()
    updated_schema["actual_columns"] = actual_columns
    updated_schema["row_count"] = len(df)
    updated_schema["column_types"] = {col: str(df[col].dtype) for col in actual_columns}

    # Map logical fields to actual columns based on heuristics or exact match
    mapping = {}
    logical_fields = ["prompt", "teacher_logits", "student_scalar", "human_annotations", "primary_dimension"]

    # Heuristic mapping
    for col in actual_columns:
        col_lower = col.lower()
        if "prompt" in col_lower:
            mapping["prompt"] = col
        elif "logits" in col_lower or "teacher" in col_lower:
            mapping["teacher_logits"] = col
        elif "student" in col_lower and "scalar" in col_lower:
            mapping["student_scalar"] = col
        elif "primary" in col_lower and "dimension" in col_lower:
            mapping["primary_dimension"] = col
        elif "human" in col_lower and ("annotation" in col_lower or "score" in col_lower):
            # Handle human annotation columns
            if "human_annotations" not in mapping:
                mapping["human_annotations"] = []
            mapping["human_annotations"].append(col)

    # If exact match fails for specific required dims, try to find them in human annotations
    if "human_annotations" in mapping and isinstance(mapping["human_annotations"], list):
        found_dims = []
        for dim in REQUIRED_DIMENSIONS:
            for col in mapping["human_annotations"]:
                if dim.lower() in col.lower():
                    found_dims.append(col)
                    break
        # Store the found dimension columns explicitly in schema
        updated_schema["required_dimensions_found"] = found_dims

    updated_schema["logical_field_mapping"] = mapping
    return updated_schema


def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate that all required rubric dimensions and human annotation columns exist.
    Raises RuntimeError if critical mismatch is found.
    """
    actual_columns = set(df.columns)
    mapping = schema.get("logical_field_mapping", {})

    # Check for required rubric dimensions in human annotations
    human_cols = mapping.get("human_annotations", [])
    if not isinstance(human_cols, list):
        human_cols = [human_cols] if human_cols else []

    found_dims = []
    missing_dims = []

    for dim in REQUIRED_DIMENSIONS:
        found = False
        for col in human_cols:
            if dim.lower() in col.lower():
                found = True
                found_dims.append(col)
                break
        if not found:
            missing_dims.append(dim)

    if missing_dims:
        error_msg = (
            f"CRITICAL SCHEMA MISMATCH: Missing required rubric dimensions: {missing_dims}. "
            f"Found human annotation columns: {human_cols}."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info(f"Validation passed. Found dimensions: {found_dims}")

    # Check for student_scalar if expected
    if "student_scalar" in mapping:
        if mapping["student_scalar"] not in actual_columns:
            error_msg = f"CRITICAL: Student scalar column '{mapping['student_scalar']}' not found."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    else:
        # Try to find it
        found_scalar = False
        for col in actual_columns:
            if "student" in col.lower() and "scalar" in col.lower():
                found_scalar = True
                break
        if not found_scalar:
            logger.warning("No student_scalar column found. This may affect downstream tasks.")

    return True


def update_contract(schema: Dict[str, Any], schema_path: Path) -> None:
    """Save the updated schema back to the contract file."""
    schema["validated"] = True
    schema["validation_timestamp"] = str(pd.Timestamp.now())
    save_schema(schema, schema_path)
    logger.info(f"Updated schema contract saved to {schema_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation for Z-Reward Dataset")
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=str(DATA_RAW_DIR / "zreward_dataset.parquet"),
        help="Path to the Z-Reward dataset Parquet file."
    )
    parser.add_argument(
        "--schema-path",
        type=str,
        default=str(CONTRACTS_DIR / "dataset.schema.yaml"),
        help="Path to the schema contract YAML file."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s - %(levelname)s - %(message)s")

    dataset_path = Path(args.dataset_path)
    schema_path = Path(args.schema_path)

    try:
        # 1. Load current schema
        logger.info(f"Loading schema contract from {schema_path}...")
        current_schema = load_schema(schema_path)

        # 2. Load dataset
        df = load_dataset(dataset_path)

        # 3. Discover schema
        logger.info("Performing schema discovery...")
        updated_schema = discover_schema(df, current_schema)

        # 4. Validate schema
        logger.info("Validating schema...")
        validate_schema(df, updated_schema)

        # 5. Update contract
        update_contract(updated_schema, schema_path)

        logger.info("Schema Discovery and Validation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
