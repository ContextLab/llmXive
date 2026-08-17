import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml
import json

# Constants for paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-entanglement-analysis" / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"

def setup_logging() -> logging.Logger:
    """Configure and return a logger for the script."""
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def load_schema(path: Path) -> Dict[str, Any]:
    """Load the provisional schema from a YAML file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], path: Path) -> None:
    """Save the updated schema to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(raw_dir: Path) -> pd.DataFrame:
    """
    Load the raw dataset produced by T037/T037b.
    Priority:
    1. z_reward.parquet
    2. z_reward_synthetic.parquet
    3. mock_z_reward.parquet
    """
    candidates = [
        raw_dir / "z_reward.parquet",
        raw_dir / "z_reward_synthetic.parquet",
        raw_dir / "mock_z_reward.parquet",
    ]
    
    for candidate in candidates:
        if candidate.exists():
            logging.info(f"Loading dataset from: {candidate}")
            if candidate.suffix == ".parquet":
                return pd.read_parquet(candidate)
            elif candidate.suffix == ".csv":
                return pd.read_csv(candidate)
            elif candidate.suffix == ".json":
                return pd.read_json(candidate)
    
    raise FileNotFoundError(
        "No raw dataset found in data/raw/. "
        "Expected one of: z_reward.parquet, z_reward_synthetic.parquet, mock_z_reward.parquet"
    )

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform schema discovery on the DataFrame.
    Returns a schema structure compatible with the provisional template.
    """
    fields = []
    for col in df.columns:
        dtype = df[col].dtype
        sample_val = df[col].iloc[0] if len(df) > 0 else None
        
        # Map pandas dtypes to logical types
        if pd.api.types.is_integer_dtype(dtype):
            logical_type = "integer"
        elif pd.api.types.is_float_dtype(dtype):
            logical_type = "float"
        elif pd.api.types.is_bool_dtype(dtype):
            logical_type = "boolean"
        elif pd.api.types.is_string_dtype(dtype) or dtype == object:
            # Check if it looks like a JSON object stored as string
            if isinstance(sample_val, str) and sample_val.startswith("{"):
                try:
                    json.loads(sample_val)
                    logical_type = "object"
                except json.JSONDecodeError:
                    logical_type = "string"
            else:
                logical_type = "string"
        else:
            logical_type = "string" # Default fallback

        field_def = {
            "name": col,
            "type": logical_type
        }
        
        # Handle nested objects if detected (e.g., teacher_scores)
        if logical_type == "object" and isinstance(sample_val, dict):
            props = {}
            for key, val in sample_val.items():
                val_type = "float" if isinstance(val, (int, float)) else "string"
                props[key] = {"type": val_type}
            field_def["properties"] = props
        
        fields.append(field_def)

    return {
        "schema_version": "1.0",
        "fields": fields
    }

def validate_schema(discovered: Dict[str, Any], provisional: Dict[str, Any]) -> List[str]:
    """
    Validate discovered schema against provisional template.
    Returns a list of errors. Critical errors include missing rubric dimensions.
    """
    errors = []
    discovered_names = {f["name"] for f in discovered["fields"]}
    provisional_names = {f["name"] for f in provisional["fields"]}
    
    # Check for critical missing columns
    critical_columns = ["prompt", "image_url", "student_scalar", "primary_dimension"]
    for col in critical_columns:
        if col not in discovered_names:
            errors.append(f"CRITICAL: Missing required column '{col}'")

    # Check for teacher_scores structure
    if "teacher_scores" in discovered_names:
        t_field = next((f for f in discovered["fields"] if f["name"] == "teacher_scores"), None)
        if t_field and "properties" in t_field:
            required_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
            found_dims = set(t_field["properties"].keys())
            for dim in required_dims:
                if dim not in found_dims:
                    errors.append(f"CRITICAL: Missing rubric dimension '{dim}' in teacher_scores")
        else:
            errors.append("CRITICAL: 'teacher_scores' exists but is not a structured object with dimensions")
    else:
        errors.append("CRITICAL: Missing 'teacher_scores' column")

    # Check for human_annotations structure
    if "human_annotations" in discovered_names:
        h_field = next((f for f in discovered["fields"] if f["name"] == "human_annotations"), None)
        if h_field and "properties" in h_field:
            required_dims = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
            found_dims = set(h_field["properties"].keys())
            for dim in required_dims:
                if dim not in found_dims:
                    errors.append(f"WARNING: Missing human annotation dimension '{dim}'")
    
    return errors

def update_contract(discovered: Dict[str, Any], contract_path: Path) -> None:
    """Overwrite the contract file with the discovered schema."""
    save_schema(discovered, contract_path)
    logging.info(f"Schema contract updated at {contract_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=str(DATA_RAW_DIR),
        help="Path to the raw data directory"
    )
    parser.add_argument(
        "--contract-path",
        type=str,
        default=str(SCHEMA_PATH),
        help="Path to the schema contract file"
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Raise error if critical schema mismatches are found"
    )
    return parser.parse_args()

def main() -> int:
    logger = setup_logging()
    args = parse_args()
    
    raw_dir = Path(args.raw_dir)
    contract_path = Path(args.contract_path)

    try:
        # 1. Load Provisional Schema
        logger.info(f"Loading provisional schema from {contract_path}")
        provisional_schema = load_schema(contract_path)
        
        # 2. Load Dataset
        logger.info("Loading raw dataset for schema discovery")
        df = load_dataset(raw_dir)
        logger.info(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # 3. Discover Schema
        logger.info("Performing schema discovery")
        discovered_schema = discover_schema(df)
        
        # 4. Validate
        logger.info("Validating discovered schema against provisional template")
        errors = validate_schema(discovered_schema, provisional_schema)
        
        if errors:
            for err in errors:
                if "CRITICAL" in err:
                    logger.error(err)
                else:
                    logger.warning(err)
            
            if args.fail_on_missing:
                logger.critical("Critical schema mismatches found. Aborting.")
                return 1
            else:
                logger.warning("Schema mismatches found but proceeding with update.")
        else:
            logger.info("Schema validation passed.")
        
        # 5. Update Contract
        logger.info("Overwriting contract with discovered schema")
        update_contract(discovered_schema, contract_path)
        
        # 6. Log Summary
        logger.info("Schema Discovery Complete.")
        logger.info(f"Final schema fields: {[f['name'] for f in discovered_schema['fields']]}")
        
        return 0

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
