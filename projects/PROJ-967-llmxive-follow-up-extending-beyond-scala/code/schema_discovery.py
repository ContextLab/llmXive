import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Project root relative to script location
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis"
CONTRACTS_DIR = SPECS_DIR / "contracts"

REQUIRED_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
REQUIRED_HUMAN_ANNOTATION_PREFIX = "human_annotation_"

def setup_logging() -> logging.Logger:
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger

def load_schema(schema_path: Path) -> Dict[str, Any]:
    logger = logging.getLogger("schema_discovery")
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], schema_path: Path) -> None:
    with open(schema_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(parquet_path: Path) -> pd.DataFrame:
    logger = logging.getLogger("schema_discovery")
    if not parquet_path.exists():
        logger.error(f"Dataset file not found: {parquet_path}")
        raise FileNotFoundError(f"Dataset file not found: {parquet_path}")
    logger.info(f"Loading dataset from {parquet_path}...")
    try:
        df = pd.read_parquet(parquet_path)
        logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspect the DataFrame to map actual columns to logical fields.
    Returns a schema dictionary reflecting the actual structure.
    """
    logger = logging.getLogger("schema_discovery")
    columns = list(df.columns)
    logger.info(f"Discovered columns: {columns}")

    # Identify potential mappings based on common naming conventions
    # We look for columns that likely contain the teacher scores (dict or separate cols)
    # and human annotations.

    schema = {
        "logical_fields": {
            "prompt": None,
            "image_url": None,
            "teacher_scores": None,
            "student_scalar": None,
            "human_annotations": {},
            "primary_dimension": None
        },
        "actual_columns": columns,
        "discrepancies": []
    }

    # Heuristics for mapping
    # 1. Prompt
    for col in columns:
        if col.lower() in ["prompt", "text", "question"]:
            schema["logical_fields"]["prompt"] = col
            break
    
    # 2. Image URL
    for col in columns:
        if "image" in col.lower() or "url" in col.lower():
            schema["logical_fields"]["image_url"] = col
            break

    # 3. Teacher Scores
    # Check if there is a column that is a dict or json string, or specific dimension columns
    # Z-Reward often has columns like 'teacher_scores_alignment', etc. or a single 'teacher_scores' dict
    teacher_score_cols = [c for c in columns if "teacher" in c.lower() and ("score" in c.lower() or "reward" in c.lower())]
    if len(teacher_score_cols) == 4:
        # Likely separate columns for each dimension
        schema["logical_fields"]["teacher_scores"] = {
            "type": "separate_columns",
            "columns": teacher_score_cols
        }
    elif len(teacher_score_cols) == 1:
        # Likely a single column containing a dict
        schema["logical_fields"]["teacher_scores"] = {
            "type": "single_column",
            "column": teacher_score_cols[0]
        }
    else:
        # Try to find columns matching the required dimensions
        dim_cols = [c for c in columns if any(d.lower() in c.lower() for d in REQUIRED_DIMENSIONS)]
        if dim_cols:
            schema["logical_fields"]["teacher_scores"] = {
                "type": "dimensional_columns",
                "columns": dim_cols
            }
        else:
            schema["logical_fields"]["teacher_scores"] = None
            schema["discrepancies"].append("Could not identify teacher score columns")

    # 4. Student Scalar
    for col in columns:
        if "student" in col.lower() and ("scalar" in col.lower() or "score" in col.lower()):
            schema["logical_fields"]["student_scalar"] = col
            break

    # 5. Human Annotations
    human_cols = [c for c in columns if "human" in c.lower() or "annotation" in c.lower()]
    if human_cols:
        for col in human_cols:
            # Try to extract dimension name
            for dim in REQUIRED_DIMENSIONS:
                if dim.lower() in col.lower():
                    schema["logical_fields"]["human_annotations"][dim] = col
                    break
    else:
        schema["discrepancies"].append("Could not identify human annotation columns")

    # 6. Primary Dimension
    if "primary_dimension" in columns:
        schema["logical_fields"]["primary_dimension"] = "primary_dimension"
    
    return schema

def validate_schema(discovered_schema: Dict[str, Any], df: pd.DataFrame) -> bool:
    """
    Validate that all required rubric dimensions and human annotation columns exist.
    """
    logger = logging.getLogger("schema_discovery")
    valid = True

    # Check Teacher Scores
    teacher_scores_info = discovered_schema["logical_fields"]["teacher_scores"]
    if teacher_scores_info is None:
        logger.error("CRITICAL: Teacher scores not found in dataset.")
        valid = False
    else:
        if teacher_scores_info.get("type") == "separate_columns":
            cols = teacher_scores_info["columns"]
            # Check if all required dimensions are represented in these columns
            # We assume the column names contain the dimension names
            found_dims = []
            for col in cols:
                for dim in REQUIRED_DIMENSIONS:
                    if dim.lower() in col.lower():
                        found_dims.append(dim)
                        break
            missing = set(REQUIRED_DIMENSIONS) - set(found_dims)
            if missing:
                logger.error(f"CRITICAL: Missing teacher score dimensions: {missing}")
                valid = False
        elif teacher_scores_info.get("type") == "single_column":
            col = teacher_scores_info["column"]
            # We need to inspect the first row to see if it's a dict with required keys
            try:
                val = df[col].iloc[0]
                if isinstance(val, dict):
                    missing = set(REQUIRED_DIMENSIONS) - set(val.keys())
                    if missing:
                        logger.error(f"CRITICAL: Teacher scores dict missing dimensions: {missing}")
                        valid = False
                else:
                    logger.error(f"CRITICAL: Teacher scores column '{col}' is not a dict.")
                    valid = False
            except Exception as e:
                logger.error(f"CRITICAL: Could not inspect teacher scores column: {e}")
                valid = False

    # Check Human Annotations
    human_annos = discovered_schema["logical_fields"]["human_annotations"]
    for dim in REQUIRED_DIMENSIONS:
        if dim not in human_annos or human_annos[dim] is None:
            logger.error(f"CRITICAL: Human annotation for dimension '{dim}' not found.")
            valid = False

    # Check Primary Dimension
    if discovered_schema["logical_fields"]["primary_dimension"] is None:
        logger.warning("WARNING: 'primary_dimension' metadata column not found. This is required for T014.")
        # This is a warning, but T014 requires it to raise an error. 
        # We flag it as a discrepancy but not necessarily a hard failure for schema discovery itself,
        # though T014 will fail later.
        discovered_schema["discrepancies"].append("Missing 'primary_dimension' column")

    return valid

def update_contract(discovered_schema: Dict[str, Any], contract_path: Path) -> None:
    """
    Update the contract file with the discovered schema.
    """
    logger = logging.getLogger("schema_discovery")
    logger.info(f"Updating contract at {contract_path}...")
    
    # Load existing contract
    contract = load_schema(contract_path)
    
    # Merge discovered schema into contract
    # The contract structure might be different, so we update the 'fields' or 'structure' section
    # For this task, we assume the contract has a 'schema' or 'structure' key we can update.
    # If the contract is just a placeholder, we replace the content with the discovered schema.
    
    if "schema" in contract:
        contract["schema"] = discovered_schema
    else:
        contract["discovered_schema"] = discovered_schema

    # Add validation status
    contract["validation_status"] = "validated" if validate_schema(discovered_schema, pd.DataFrame()) else "failed" 
    # Note: We can't validate against an empty DF here, but we update the contract with the structure.
    # The actual validation happens in the function above.

    save_schema(contract, contract_path)
    logger.info("Contract updated successfully.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=str(DATA_RAW_DIR / "imagenet_rewards.parquet"),
        help="Path to the raw dataset parquet file"
    )
    parser.add_argument(
        "--contract-path",
        type=str,
        default=str(CONTRACTS_DIR / "dataset.schema.yaml"),
        help="Path to the dataset schema contract file"
    )
    return parser.parse_args()

def main() -> None:
    logger = setup_logging()
    args = parse_args()

    dataset_path = Path(args.dataset_path)
    contract_path = Path(args.contract_path)

    try:
        # 1. Load Dataset
        df = load_dataset(dataset_path)

        # 2. Discover Schema
        discovered_schema = discover_schema(df)

        # 3. Validate Schema
        is_valid = validate_schema(discovered_schema, df)

        if is_valid:
            logger.info("Schema validation PASSED. All required dimensions and annotations found.")
        else:
            logger.error("Schema validation FAILED. Critical mismatches detected.")
            # We still update the contract to reflect reality, but the process fails
            # The task description says "Raise error if critical mismatch".
            # However, T038 is about discovery and updating the contract. 
            # We raise an error to stop the pipeline if critical data is missing.
            raise RuntimeError("Schema validation failed: Critical mismatches detected.")

        # 4. Update Contract
        update_contract(discovered_schema, contract_path)

    except FileNotFoundError as e:
        logger.critical(f"File not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
