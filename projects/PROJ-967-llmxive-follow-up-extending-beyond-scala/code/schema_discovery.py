import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Project root relative to this script's location (code/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis" / "contracts"

# File paths
PROVISIONAL_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
VALIDATED_SCHEMA_PATH = CONTRACTS_DIR / "dataset.validated.schema.yaml"

# Logical field mappings (what we expect vs what might be in the raw data)
LOGICAL_FIELDS = {
    "prompt": ["prompt", "text", "input", "question"],
    "image_url": ["image_url", "image", "url", "img"],
    "teacher_scores": ["teacher_scores", "teacher", "scores", "rubric"],
    "student_scalar": ["student_scalar", "student_score", "student", "scalar"],
    "human_annotations": ["human_annotations", "human", "annotations", "human_scores"],
    "primary_dimension": ["primary_dimension", "primary", "dimension", "target_dimension"],
}

RUBRIC_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    return logger

def load_schema(path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], path: Path) -> None:
    """Save a schema to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(raw_dir: Path) -> pd.DataFrame:
    """
    Load the raw dataset.
    T037 should have placed the raw data file in data/raw/.
    We expect a parquet or csv file.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    # Look for common file extensions
    parquet_files = list(raw_dir.glob("*.parquet"))
    csv_files = list(raw_dir.glob("*.csv"))

    if parquet_files:
        # Assume the first parquet file is the dataset
        df = pd.read_parquet(parquet_files[0])
        logging.info(f"Loaded dataset from Parquet: {parquet_files[0].name}")
    elif csv_files:
        df = pd.read_csv(csv_files[0])
        logging.info(f"Loaded dataset from CSV: {csv_files[0].name}")
    else:
        raise FileNotFoundError(
            f"No dataset file found in {raw_dir}. Expected .parquet or .csv"
        )

    return df

def discover_schema(df: pd.DataFrame, logger: logging.Logger) -> Dict[str, Any]:
    """
    Inspect the dataframe and map actual column names to logical fields.
    Returns a schema description.
    """
    actual_columns = set(df.columns)
    discovered = {}

    for logical, candidates in LOGICAL_FIELDS.items():
        matched = None
        for candidate in candidates:
            if candidate in actual_columns:
                matched = candidate
                break

        if matched:
            discovered[logical] = {
                "matched_column": matched,
                "detected": True,
            }
        else:
            discovered[logical] = {
                "matched_column": None,
                "detected": False,
                "missing": True,
            }

    # Special handling for nested structures (teacher_scores, human_annotations)
    # We check if the matched column is a dict-like object or separate columns
    for logical in ["teacher_scores", "human_annotations"]:
        if discovered[logical]["detected"]:
            col_name = discovered[logical]["matched_column"]
            # Check the type of the first non-null entry
            sample = df[col_name].dropna().iloc[0] if len(df[col_name].dropna()) > 0 else None
            if isinstance(sample, dict):
                discovered[logical]["structure"] = "nested_dict"
                discovered[logical]["keys"] = list(sample.keys())
            elif isinstance(sample, str):
                # Might be JSON string, but we assume nested for now
                discovered[logical]["structure"] = "unknown"
            else:
                discovered[logical]["structure"] = "flat_columns" # Likely separate columns exist

    return discovered

def validate_schema(discovered: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Validate that critical fields are present.
    Critical: prompt, teacher_scores, student_scalar, human_annotations, primary_dimension
    """
    critical_fields = ["prompt", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]
    missing_critical = []

    for field in critical_fields:
        if not discovered.get(field, {}).get("detected", False):
            missing_critical.append(field)

    if missing_critical:
        logger.error(f"Critical fields missing: {missing_critical}")
        return False

    return True

def update_contract(provisional_schema: Dict[str, Any], discovered: Dict[str, Any], validated_schema_path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Update the provisional schema to reflect the actual discovered schema.
    Writes to dataset.validated.schema.yaml.
    """
    validated = {
        "source": "discovered_from_raw_data",
        "logical_mapping": {},
        "validation_status": "validated",
        "warnings": []
    }

    # Reconstruct the schema structure based on discovery
    for logical, details in discovered.items():
        mapping_entry = {
            "logical_name": logical,
            "actual_column": details.get("matched_column"),
            "detected": details.get("detected", False),
        }
        if "structure" in details:
            mapping_entry["structure"] = details["structure"]
        if "keys" in details:
            mapping_entry["rubric_keys"] = details["keys"]

        validated["logical_mapping"][logical] = mapping_entry

        if not details.get("detected", False):
            validated["warnings"].append(f"Field '{logical}' was not found in the raw dataset.")

    save_schema(validated, validated_schema_path)
    logger.info(f"Validated schema written to: {validated_schema_path}")
    return validated

def parse_args():
    parser = argparse.ArgumentParser(description="Discover and validate dataset schema.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=str(DATA_RAW_DIR),
        help="Path to the raw data directory",
    )
    parser.add_argument(
        "--provisional-schema",
        type=str,
        default=str(PROVISIONAL_SCHEMA_PATH),
        help="Path to the provisional schema YAML",
    )
    parser.add_argument(
        "--validated-schema",
        type=str,
        default=str(VALIDATED_SCHEMA_PATH),
        help="Path to write the validated schema YAML",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()

    logger.info("Starting Schema Discovery and Validation...")

    try:
        # 1. Load Provisional Schema
        logger.info(f"Loading provisional schema from {args.provisional_schema}")
        provisional_schema = load_schema(Path(args.provisional_schema))
        logger.info("Provisional schema loaded.")

        # 2. Load Raw Dataset
        logger.info(f"Loading raw dataset from {args.raw_dir}")
        df = load_dataset(Path(args.raw_dir))
        logger.info(f"Dataset loaded with {len(df)} rows and {len(df.columns)} columns.")
        logger.info(f"Columns: {list(df.columns)}")

        # 3. Discover Schema
        logger.info("Performing schema discovery...")
        discovered = discover_schema(df, logger)

        # 4. Validate Schema
        logger.info("Validating schema against critical requirements...")
        is_valid = validate_schema(discovered, logger)

        if not is_valid:
            logger.critical("Schema validation failed. Critical fields are missing.")
            sys.exit(1)

        # 5. Update Contract
        logger.info("Updating contract with discovered schema...")
        final_schema = update_contract(provisional_schema, discovered, Path(args.validated_schema), logger)

        logger.info("Schema Discovery and Validation completed successfully.")

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
