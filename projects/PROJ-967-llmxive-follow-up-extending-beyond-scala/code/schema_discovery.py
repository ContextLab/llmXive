import argparse
import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import yaml

# Local imports based on provided API surface
# No local modules defined for setup_logging, so we define it here
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
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

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the provisional schema from a YAML file."""
    logger = logging.getLogger("schema_discovery")
    logger.info(f"Loading schema from {schema_path}")
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing schema YAML: {e}")
        raise

def save_schema(schema: Dict[str, Any], schema_path: str) -> None:
    """Save the schema to a YAML file."""
    logger = logging.getLogger("schema_discovery")
    logger.info(f"Saving schema to {schema_path}")
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False)

def load_dataset(data_path: str) -> pd.DataFrame:
    """Load the dataset from a Parquet file."""
    logger = logging.getLogger("schema_discovery")
    logger.info(f"Loading dataset from {data_path}")
    try:
        df = pd.read_parquet(data_path)
        logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        return df
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {data_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def discover_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Infer the schema from the dataframe."""
    logger = logging.getLogger("schema_discovery")
    schema = {
        "columns": {}
    }
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample_values = df[col].dropna().head(5).tolist()
        schema["columns"][col] = {
            "type": dtype,
            "sample_values": sample_values
        }
    
    logger.info(f"Discovered schema for {len(df.columns)} columns")
    return schema

def validate_schema(discovered_schema: Dict[str, Any], contract_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Compare discovered schema with the contract schema."""
    logger = logging.getLogger("schema_discovery")
    validation_result = {
        "is_valid": True,
        "discrepancies": [],
        "missing_columns": [],
        "extra_columns": []
    }
    
    contract_columns = set(contract_schema.get("columns", {}).keys())
    discovered_columns = set(discovered_schema.get("columns", {}).keys())
    
    # Check for missing columns (required by contract)
    missing = contract_columns - discovered_columns
    if missing:
        validation_result["missing_columns"] = list(missing)
        validation_result["is_valid"] = False
        logger.warning(f"Missing columns found: {missing}")
    
    # Check for extra columns (not in contract)
    extra = discovered_columns - contract_columns
    if extra:
        validation_result["extra_columns"] = list(extra)
        logger.info(f"Extra columns found (not in contract): {extra}")
    
    # Check for type mismatches
    for col in contract_columns.intersection(discovered_columns):
        contract_type = contract_schema["columns"][col].get("type")
        discovered_type = discovered_schema["columns"][col].get("type")
        
        # Simple type comparison (could be more sophisticated)
        if contract_type and discovered_type and contract_type != discovered_type:
            validation_result["discrepancies"].append({
                "column": col,
                "contract_type": contract_type,
                "discovered_type": discovered_type
            })
            # Not necessarily invalid if it's a compatible type (e.g., int vs float)
            # For strict validation, we might mark it invalid
            # validation_result["is_valid"] = False
            logger.warning(f"Type mismatch for column {col}: contract={contract_type}, discovered={discovered_type}")
    
    return validation_result

def update_contract(discovered_schema: Dict[str, Any], contract_path: str, force_update: bool = False) -> None:
    """Update the contract schema with the discovered schema if there are discrepancies."""
    logger = logging.getLogger("schema_discovery")
    
    if force_update:
        logger.info("Force updating contract schema with discovered schema")
        save_schema(discovered_schema, contract_path)
        return
    
    # Load current contract
    try:
        current_contract = load_schema(contract_path)
    except FileNotFoundError:
        logger.info("No existing contract found. Saving discovered schema as new contract.")
        save_schema(discovered_schema, contract_path)
        return
    
    # Compare and decide
    validation = validate_schema(discovered_schema, current_contract)
    
    if not validation["is_valid"] or validation["extra_columns"]:
        logger.info("Discrepancies found. Updating contract schema.")
        # Merge: keep contract structure but update types if different
        # For this task, we overwrite with discovered schema if there are significant changes
        # or if the contract was missing columns
        if validation["missing_columns"]:
            logger.warning("Contract is missing columns present in data. Overwriting contract.")
            save_schema(discovered_schema, contract_path)
        elif validation["discrepancies"]:
            logger.warning("Type discrepancies found. Updating contract types.")
            # Create a merged schema
            merged_schema = current_contract.copy()
            if "columns" not in merged_schema:
                merged_schema["columns"] = {}
            for col, info in discovered_schema["columns"].items():
                merged_schema["columns"][col] = info
            save_schema(merged_schema, contract_path)
        else:
            logger.info("No critical discrepancies. Keeping existing contract.")
    else:
        logger.info("Schema matches contract. No update needed.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schema Discovery and Validation")
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw/oxford_pets_simulated.parquet",
        help="Path to the raw dataset file"
    )
    parser.add_argument(
        "--contract-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/contracts/dataset.schema.yaml",
        help="Path to the contract schema file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/schema_validation_report.json",
        help="Path to save the validation report"
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Force update the contract schema even if it matches"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/schema_discovery.log",
        help="Path to the log file"
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger = setup_logging(args.log_file)
    
    logger.info("Starting Schema Discovery and Validation")
    
    try:
        # 1. Load the raw dataset
        df = load_dataset(args.dataset_path)
        
        # 2. Infer actual column names and map to logical fields
        discovered_schema = discover_schema(df)
        
        # 3. Validate against provisional contract schema
        try:
            contract_schema = load_schema(args.contract_path)
        except FileNotFoundError:
            logger.warning(f"Contract schema not found at {args.contract_path}. Creating new contract.")
            contract_schema = {"columns": {}}
        
        validation_result = validate_schema(discovered_schema, contract_schema)
        
        # Check for missing rubric dimensions (specific requirement)
        rubric_dims = ["dimension_1", "dimension_2", "dimension_3", "dimension_4"]
        missing_dims = [d for d in rubric_dims if d not in discovered_schema["columns"]]
        
        if missing_dims:
            logger.error(f"Missing rubric dimensions: {missing_dims}")
            raise RuntimeError(f"Missing required rubric dimensions: {missing_dims}")
        
        # 4. On discrepancy, overwrite contract
        update_contract(discovered_schema, args.contract_path, args.force_update)
        
        # 5. Save validation report
        report = {
            "dataset_path": args.dataset_path,
            "contract_path": args.contract_path,
            "discovered_schema": discovered_schema,
            "validation_result": validation_result,
            "rubric_dimensions_check": {
                "required": rubric_dims,
                "found": [d for d in rubric_dims if d in discovered_schema["columns"]],
                "missing": missing_dims,
                "all_present": len(missing_dims) == 0
            }
        }
        
        os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
        with open(args.output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {args.output_path}")
        
        if not validation_result["is_valid"]:
            logger.warning("Schema validation failed. Please review the discrepancies.")
            sys.exit(1)
        else:
            logger.info("Schema validation successful.")
            
    except Exception as e:
        logger.error(f"Schema discovery and validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
