"""
Data Ingestion and Validation Module.
Handles loading, schema validation, variable checking, and outlier detection.
"""
import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ingest")

class RealDataFetchError(Exception):
    """Raised when real data fetch fails or is not authorized."""
    pass

def setup_paths():
    """Ensure required directory structures exist."""
    dirs = [
        "data/raw", "data/processed", "data/results", "data/config",
        "data/metadata", "data/citations", "state/projects"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    # Create __init__.py files to make them packages
    for d in dirs:
        init_path = Path(d) / "__init__.py"
        if not init_path.exists():
            init_path.touch()

def load_schema(schema_path: str) -> Dict:
    """Load a YAML schema definition."""
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> Tuple[List[str], List[str]]:
    """
    Load required predictors and outcomes from config.
    Returns (predictors, outcomes) lists.
    """
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Returning empty lists.")
        return [], []
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    predictors = config.get("required_predictors", [])
    outcomes = config.get("required_outcomes", [])
    logger.info(f"Loaded {len(predictors)} predictors and {len(outcomes)} outcomes from config.")
    return predictors, outcomes

def validate_variables(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> Dict:
    """
    Check for required predictors and outcomes in the dataframe.
    Returns a validation report dict.
    """
    missing_predictors = [p for p in predictors if p not in df.columns]
    missing_outcomes = [o for o in outcomes if o not in df.columns]
    missing_all = missing_predictors + missing_outcomes
    
    total_required = len(predictors) + len(outcomes)
    missing_count = len(missing_all)
    percentage_loaded = ((total_required - missing_count) / total_required * 100) if total_required > 0 else 100.0
    
    status = "PASS" if missing_count == 0 else "FAIL"
    
    report = {
        "status": status,
        "percentage_loaded": round(percentage_loaded, 2),
        "missing_variables": missing_all,
        "total_required": total_required,
        "missing_predictors": missing_predictors,
        "missing_outcomes": missing_outcomes
    }
    
    # ALWAYS write the metrics file
    metrics_path = Path("data/results/variable_load_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Variable load metrics written to {metrics_path}")
    
    return report

def fetch_real_data() -> pd.DataFrame:
    """
    Attempt to fetch real data from verified sources.
    Raises RealDataFetchError if no source is configured or fetch fails.
    """
    sources_file = Path("data/config/real_data_sources.yaml")
    if not sources_file.exists():
        raise RealDataFetchError("No real data sources configured. Please populate data/config/real_data_sources.yaml.")
    
    import yaml
    with open(sources_file, 'r') as f:
        sources = yaml.safe_load(f)
    
    if not sources or not sources.get("sources"):
        raise RealDataFetchError("Real data sources list is empty. Please provide a verified dataset ID.")
    
    # Placeholder for actual fetch logic (e.g., using requests or specific API)
    # For now, if no real source is found, we raise.
    # In a real implementation, this would download from NCBI/Zenodo.
    raise RealDataFetchError("Real data fetch not implemented in this stub. Please use synthetic mode or implement fetch logic.")

def load_data(input_path: Optional[str] = None, mode: str = "real") -> pd.DataFrame:
    """
    Load data from file or fetch real data.
    Validates variables immediately. Halts if validation fails.
    """
    setup_paths()
    predictors, outcomes = load_required_variables()
    
    df = None
    if mode == "synthetic":
        if not input_path:
            input_path = "data/raw/synthetic_data.csv"
        if not os.path.exists(input_path):
            logger.error(f"Synthetic data file {input_path} not found. Run generator first.")
            sys.exit(1)
        df = pd.read_csv(input_path)
    elif mode == "real":
        try:
            df = fetch_real_data()
        except RealDataFetchError as e:
            logger.error(f"Real data fetch failed: {e}")
            sys.exit(1)
    else:
        if not input_path:
            raise ValueError("Input path required for file-based mode")
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file {input_path} not found")
        df = pd.read_csv(input_path)
    
    # Validate variables
    report = validate_variables(df, predictors, outcomes)
    
    if report["status"] == "FAIL":
        # Write structured failure report
        failure_report_path = Path("data/results/validation_failure_report.json")
        with open(failure_report_path, 'w') as f:
            json.dump({
                "error": "Variable validation failed",
                "missing_variables": report["missing_variables"],
                "timestamp": pd.Timestamp.now().isoformat()
            }, f, indent=2)
        logger.error(f"Validation failed. Missing: {report['missing_variables']}")
        logger.error(f"Failure report written to {failure_report_path}")
        sys.exit(1)
    
    return df

def detect_outliers_iqr(df: pd.DataFrame, columns: List[str]) -> List[int]:
    """
    Detect outliers using IQR method (>1.5x IQR above Q3 or <1.5x IQR below Q1).
    Returns list of row indices to exclude.
    """
    excluded_indices = set()
    for col in columns:
        if col not in df.columns:
            continue
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        excluded_indices.update(df[mask].index.tolist())
    return list(excluded_indices)

def save_outlier_report(excluded_indices: List[int], output_path: str = "data/results/outlier_report.json"):
    """Save outlier report to JSON."""
    report = {
        "count": len(excluded_indices),
        "excluded_indices": excluded_indices
    }
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Outlier report saved to {output_path}")

def filter_outliers(df: pd.DataFrame, excluded_indices: List[int]) -> pd.DataFrame:
    """Remove rows with excluded indices."""
    return df.drop(index=excluded_indices).reset_index(drop=True)

def save_filtered_data(df: pd.DataFrame, output_path: str = "data/processed/filtered_data.parquet"):
    """Save filtered data to Parquet."""
    df.to_parquet(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"

def record_checksum(file_path: str, state_file: str = "state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml"):
    """Record artifact checksum in state file."""
    import yaml
    checksum = calculate_checksum(file_path)
    
    state_path = Path(state_file)
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {"artifact_hashes": {}}
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"][file_path] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    logger.info(f"Checksum recorded for {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Data Ingestion and Validation")
    parser.add_argument("--input", type=str, help="Input file path")
    parser.add_argument("--mode", type=str, default="real", choices=["real", "synthetic", "file"], help="Data mode")
    parser.add_argument("--output", type=str, help="Output path for filtered data")
    args = parser.parse_args()
    
    setup_paths()
    df = load_data(args.input, args.mode)
    
    # Detect outliers
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    excluded = detect_outliers_iqr(df, numeric_cols)
    save_outlier_report(excluded)
    
    # Filter and save
    df_clean = filter_outliers(df, excluded)
    output_path = args.output if args.output else "data/processed/filtered_data.parquet"
    save_filtered_data(df_clean, output_path)
    
    # Record checksum
    record_checksum(output_path)
    logger.info("Ingestion and validation complete.")

if __name__ == "__main__":
    main()
