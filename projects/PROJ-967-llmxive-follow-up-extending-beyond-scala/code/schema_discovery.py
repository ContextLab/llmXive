import argparse
import json
import logging
import sys
import os
from pathlib import Path
import pandas as pd
import yaml
from typing import Dict, Any, List, Optional

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging to both console and file if provided."""
    logger = logging.getLogger("schema_discovery")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
    return logger

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the provisional schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def save_schema(schema: Dict[str, Any], schema_path: Path) -> None:
    """Save the updated schema to YAML file."""
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(data_path: Path) -> pd.DataFrame:
    """Load the raw dataset from parquet file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")
    try:
        df = pd.read_parquet(data_path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset from {data_path}: {e}")

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Infer actual column names and data types from the dataset."""
    schema = {
        "columns": []
    }
    for col in df.columns:
        col_schema = {
            "name": col,
            "dtype": str(df[col].dtype),
            "non_null_count": int(df[col].notna().sum()),
            "null_count": int(df[col].isna().sum())
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            col_schema["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
            col_schema["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
            col_schema["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
        schema["columns"].append(col_schema)
    return schema

def validate_schema(discovered: Dict[str, Any], contract: Dict[str, Any]) -> List[str]:
    """Compare discovered schema with contract and return discrepancies."""
    discrepancies = []
    contract_cols = {c["name"]: c for c in contract.get("columns", [])}
    discovered_cols = {c["name"]: c for c in discovered.get("columns", [])}

    # Check for missing required columns
    required = contract.get("required_columns", [])
    for req_col in required:
        if req_col not in discovered_cols:
            discrepancies.append(f"Missing required column: {req_col}")

    # Check for missing rubric dimensions
    rubric_dims = contract.get("rubric_dimensions", [])
    for dim in rubric_dims:
        if dim not in discovered_cols:
            discrepancies.append(f"Missing rubric dimension column: {dim}")

    # Check for extra columns not in contract (optional warning)
    for col in discovered_cols:
        if col not in contract_cols and col not in ["image_path", "species_id", "prompt_text", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]:
            discrepancies.append(f"Unexpected column in dataset: {col}")

    return discrepancies

def update_contract(contract: Dict[str, Any], discovered: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Update the contract with discovered schema if discrepancies exist."""
    if not contract.get("columns"):
        contract["columns"] = discovered["columns"]
        logger.info("Contract updated with discovered schema (initial population).")
        return contract

    # Update column details
    contract_cols = {c["name"]: c for c in contract["columns"]}
    for disc_col in discovered["columns"]:
        col_name = disc_col["name"]
        if col_name in contract_cols:
            # Update dtype and stats if they differ significantly
            if contract_cols[col_name].get("dtype") != disc_col["dtype"]:
                contract_cols[col_name]["dtype"] = disc_col["dtype"]
                logger.info(f"Updated dtype for column {col_name}: {disc_col['dtype']}")
            # Update sample stats
            contract_cols[col_name]["non_null_count"] = disc_col["non_null_count"]
            contract_cols[col_name]["null_count"] = disc_col["null_count"]
            if "min" in disc_col:
                contract_cols[col_name]["min"] = disc_col["min"]
            if "max" in disc_col:
                contract_cols[col_name]["max"] = disc_col["max"]
            if "mean" in disc_col:
                contract_cols[col_name]["mean"] = disc_col["mean"]
        else:
            # Add new column to contract
            contract["columns"].append(disc_col)
            logger.info(f"Added new column to contract: {col_name}")

    return contract

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument("--data-path", type=str, required=True, help="Path to the raw dataset parquet file")
    parser.add_argument("--contract-path", type=str, default="specs/001-llmxive-follow-up-extending-beyond-scala/contracts/dataset.schema.yaml", help="Path to the contract schema YAML file")
    parser.add_argument("--output-path", type=str, default="data/processed/schema_discovery_report.json", help="Path to save the discovery report")
    parser.add_argument("--log-file", type=str, default="data/processed/schema_discovery.log", help="Path to log file")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger = setup_logging(args.log_file)
    logger.info("Starting schema discovery and validation.")

    data_path = Path(args.data_path)
    contract_path = Path(args.contract_path)
    output_path = Path(args.output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load contract
        logger.info(f"Loading contract from {contract_path}")
        contract = load_schema(contract_path)
        logger.info("Contract loaded successfully.")

        # Load dataset
        logger.info(f"Loading dataset from {data_path}")
        df = load_dataset(data_path)
        logger.info(f"Dataset loaded with {len(df)} rows and {len(df.columns)} columns.")

        # Discover schema
        logger.info("Discovering schema from dataset...")
        discovered = discover_schema(df)
        logger.info(f"Discovered {len(discovered['columns'])} columns.")

        # Validate schema
        logger.info("Validating discovered schema against contract...")
        discrepancies = validate_schema(discovered, contract)
        if discrepancies:
            logger.warning(f"Found {len(discrepancies)} discrepancies:")
            for disc in discrepancies:
                logger.warning(f"  - {disc}")
        else:
            logger.info("No discrepancies found. Schema matches contract.")

        # Update contract if needed
        if discrepancies:
            logger.info("Updating contract with discovered schema...")
            updated_contract = update_contract(contract, discovered, logger)
            save_schema(updated_contract, contract_path)
            logger.info(f"Contract updated and saved to {contract_path}")
        else:
            # Still save the discovered schema for reference
            logger.info("No update needed, but saving discovery report.")

        # Save discovery report
        report = {
            "data_path": str(data_path),
            "contract_path": str(contract_path),
            "discovered_schema": discovered,
            "discrepancies": discrepancies,
            "contract_updated": bool(discrepancies),
            "sample_count": len(df),
            "column_count": len(df.columns)
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Discovery report saved to {output_path}")

        logger.info("Schema discovery and validation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
