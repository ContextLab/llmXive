import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import pandas as pd

# Setup logging
def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(log_level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger

logger = setup_logging()

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the provisional schema from a YAML file."""
    logger.info(f"Loading schema from {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], schema_path: str) -> None:
    """Save the updated schema to a YAML file."""
    logger.info(f"Saving schema to {schema_path}")
    with open(schema_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(data_path: str) -> pd.DataFrame:
    """Load the dataset from a Parquet file."""
    logger.info(f"Loading dataset from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset file not found: {data_path}")
    return pd.read_parquet(data_path)

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Discover the schema of the loaded DataFrame."""
    fields = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        field_info = {
            "name": col,
            "type": dtype,
        }
        # Handle nested structures if present
        if df[col].apply(lambda x: isinstance(x, dict)).any():
            field_info["type"] = "object"
            # Attempt to extract properties if it's a dict column
            sample = df[col].dropna().iloc[0]
            if isinstance(sample, dict):
                props = {}
                for k, v in sample.items():
                    props[k] = type(v).__name__
                field_info["properties"] = props
        fields.append(field_info)
    
    return {
        "schema_version": "1.0",
        "fields": fields
    }

def validate_schema(discovered: Dict[str, Any], provisional: Dict[str, Any]) -> List[str]:
    """Compare discovered schema against provisional schema and return discrepancies."""
    discrepancies = []
    discovered_fields = {f["name"]: f for f in discovered["fields"]}
    provisional_fields = {f["name"]: f for f in provisional["fields"]}

    # Check for missing required fields
    for name, prov_field in provisional_fields.items():
        if name not in discovered_fields:
            discrepancies.append(f"Missing required field: {name}")
        else:
            disc_field = discovered_fields[name]
            # Type check (simple string comparison for now)
            if disc_field["type"] != prov_field["type"]:
                discrepancies.append(f"Type mismatch for {name}: discovered '{disc_field['type']}', expected '{prov_field['type']}'")
            
            # Check properties if object type
            if prov_field.get("properties"):
                disc_props = disc_field.get("properties", {})
                for prop_name in prov_field["properties"]:
                    if prop_name not in disc_props:
                        discrepancies.append(f"Missing property '{prop_name}' in object field '{name}'")

    # Check for extra fields (optional, but good to log)
    for name in discovered_fields:
        if name not in provisional_fields:
            logger.warning(f"Extra field found in dataset: {name}")

    return discrepancies

def update_contract(discovered: Dict[str, Any], contract_path: str) -> None:
    """Overwrite the contract file with the discovered schema."""
    logger.info(f"Overwriting contract at {contract_path} with discovered schema.")
    save_schema(discovered, contract_path)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation Tool")
    parser.add_argument(
        "--input-data",
        type=str,
        required=True,
        help="Path to the input Parquet file (output of T037 or T037b)"
    )
    parser.add_argument(
        "--contract-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/contracts/dataset.schema.yaml",
        help="Path to the provisional schema contract file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        help="Optional path to save the final discovered schema (if different from contract)"
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    
    # 1. Load Provisional Schema
    try:
        provisional_schema = load_schema(args.contract_path)
    except FileNotFoundError:
        logger.error(f"Provisional schema not found at {args.contract_path}. Cannot proceed.")
        sys.exit(1)

    # 2. Load Dataset
    try:
        df = load_dataset(args.input_data)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # 3. Discover Schema
    discovered_schema = discover_schema(df)
    logger.info(f"Discovered {len(discovered_schema['fields'])} fields.")

    # 4. Validate
    discrepancies = validate_schema(discovered_schema, provisional_schema)
    
    if discrepancies:
        logger.warning("Schema discrepancies found:")
        for d in discrepancies:
            logger.warning(f"  - {d}")
        
        # Check for critical mismatches (missing rubric dimensions)
        critical_fields = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
        # We need to check if these are inside teacher_scores or human_annotations
        # Based on T001d, they are properties of 'teacher_scores' object.
        # If the object exists but properties are missing, it's critical.
        
        teacher_scores_field = next((f for f in discovered_schema["fields"] if f["name"] == "teacher_scores"), None)
        if teacher_scores_field:
            props = teacher_scores_field.get("properties", {})
            missing_dims = [dim for dim in critical_fields if dim not in props]
            if missing_dims:
                logger.critical(f"Critical mismatch: Missing rubric dimensions in teacher_scores: {missing_dims}")
                raise RuntimeError(f"Critical Schema Mismatch: Missing dimensions {missing_dims}")
        else:
            logger.critical("Critical mismatch: Missing 'teacher_scores' field entirely.")
            raise RuntimeError("Critical Schema Mismatch: Missing 'teacher_scores' field.")

        # If we have discrepancies but no critical errors, we proceed to update.
        logger.info("Overwriting contract with discovered schema to resolve discrepancies.")
        target_path = args.output_path if args.output_path else args.contract_path
        update_contract(discovered_schema, target_path)
    else:
        logger.info("Schema validation successful. No discrepancies found.")

    logger.info("Schema Discovery and Validation completed successfully.")

if __name__ == "__main__":
    main()
