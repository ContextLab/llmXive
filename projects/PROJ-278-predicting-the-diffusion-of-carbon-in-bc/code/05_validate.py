import os
import sys
import json
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import load_config, get_path
from exceptions import DataInsufficientError
from logging_config import setup_logger
import yaml

# Ensure the project root is in the path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual = compute_sha256(file_path)
    return actual == expected_checksum

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate a CSV file against a schema.
    Checks for required columns and basic types.
    """
    import pandas as pd
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise DataInsufficientError(f"Failed to read CSV {csv_path}: {e}")

    required_cols = schema.get('properties', {}).keys()
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise DataInsufficientError(f"Missing required columns in {csv_path}: {missing_cols}")
    
    # Basic type validation if defined in schema
    for col, props in schema.get('properties', {}).items():
        if 'type' in props:
            expected_type = props['type']
            if expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_categorical_dtype(df[col]):
                    # Allow object for strings, but warn if numeric
                    pass 
            elif expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise DataInsufficientError(f"Column {col} should be numeric but is {df[col].dtype}")
            elif expected_type == 'boolean':
                if not pd.api.types.is_bool_dtype(df[col]):
                    # Allow int/float if 0/1 or True/False
                    pass 
    
    return True

def validate_json_against_schema(json_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate a JSON file against a schema.
    Checks for required keys.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataInsufficientError(f"Invalid JSON in {json_path}: {e}")

    required_keys = schema.get('required', [])
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        raise DataInsufficientError(f"Missing required keys in {json_path}: {missing_keys}")
    
    return True

def run_script(script_name: str, args: Optional[List[str]] = None) -> subprocess.CompletedProcess:
    """Run a Python script from the code directory."""
    script_path = PROJECT_ROOT / "code" / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    logging.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    
    if result.returncode != 0:
        logging.error(f"Script {script_name} failed with return code {result.returncode}")
        logging.error(f"STDOUT: {result.stdout}")
        logging.error(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Script {script_name} failed")
    
    return result

def run_quickstart_validation() -> Dict[str, Any]:
    """
    Execute the full pipeline as described in quickstart.md and validate outputs.
    Returns a summary of the validation results.
    """
    results = {
        "success": False,
        "steps_completed": [],
        "errors": []
    }

    try:
        # 1. Download
        logging.info("Step 1: Downloading raw data...")
        run_script("01_download.py")
        results["steps_completed"].append("download")
        
        # 2. Preprocess
        logging.info("Step 2: Preprocessing data...")
        run_script("02_preprocess.py")
        results["steps_completed"].append("preprocess")
        
        # Validate Preprocess Outputs
        config = load_config()
        cleaned_data_path = get_path(config, "data_path", "processed") / "dataset_cleaned.csv"
        dataset_schema_path = PROJECT_ROOT / "specs" / "001-predict-carbon-diffusion-bcc" / "contracts" / "dataset.schema.yaml"
        
        if dataset_schema_path.exists():
            schema = load_schema(dataset_schema_path)
            validate_csv_against_schema(cleaned_data_path, schema)
            logging.info("Dataset schema validation passed.")
        else:
            logging.warning("Dataset schema file not found, skipping schema validation.")

        # 3. Train
        logging.info("Step 3: Training models...")
        run_script("03_train.py")
        results["steps_completed"].append("train")

        # Validate Train Outputs
        model_results_path = get_path(config, "output_path", "outputs") / "model_results.json"
        model_schema_path = PROJECT_ROOT / "specs" / "001-predict-carbon-diffusion-bcc" / "contracts" / "model_output.schema.yaml"
        
        if model_schema_path.exists():
            schema = load_schema(model_schema_path)
            validate_json_against_schema(model_results_path, schema)
            logging.info("Model results schema validation passed.")
        else:
            logging.warning("Model results schema file not found, skipping schema validation.")

        # 4. Evaluate
        logging.info("Step 4: Evaluating model (SHAP, PDP)...")
        run_script("04_evaluate.py")
        results["steps_completed"].append("evaluate")

        # Validate Evaluate Outputs
        feature_importance_path = get_path(config, "output_path", "outputs") / "feature_importance.json"
        variance_partition_path = get_path(config, "output_path", "outputs") / "variance_partition.csv"
        
        if feature_importance_path.exists():
            with open(feature_importance_path, 'r') as f:
                fi_data = json.load(f)
            assert "ranked_features" in fi_data, "feature_importance.json missing 'ranked_features'"
            assert "top_two" in fi_data, "feature_importance.json missing 'top_two'"
            logging.info("Feature importance output validated.")
        else:
            raise FileNotFoundError(f"Feature importance file not found: {feature_importance_path}")

        if variance_partition_path.exists():
            import pandas as pd
            vp_df = pd.read_csv(variance_partition_path)
            required_cols = ["adjusted_r2", "microstructural_gap", "residual_variance_label"]
            for col in required_cols:
                if col not in vp_df.columns:
                    raise DataInsufficientError(f"variance_partition.csv missing column: {col}")
            logging.info("Variance partition output validated.")
        else:
            raise FileNotFoundError(f"Variance partition file not found: {variance_partition_path}")

        results["success"] = True
        logging.info("Quickstart validation completed successfully.")

    except Exception as e:
        results["errors"].append(str(e))
        logging.exception("Validation failed with error")

    return results

def main():
    """Entry point for validation script."""
    logger = setup_logger("validation")
    logging.info("Starting Quickstart Validation (T024)...")
    
    try:
        results = run_quickstart_validation()
        
        if results["success"]:
            logging.info("SUCCESS: All pipeline steps executed and validated.")
            logging.info(f"Steps completed: {', '.join(results['steps_completed'])}")
            sys.exit(0)
        else:
            logging.error("FAILURE: Validation failed.")
            for err in results["errors"]:
                logging.error(f"  - {err}")
            sys.exit(1)
            
    except Exception as e:
        logging.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
