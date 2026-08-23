import os
import sys
import json
import logging
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest")

class RealDataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

def setup_paths(output_dir: str) -> Path:
    """Setup output paths."""
    return Path(output_dir)

def load_schema(schema_path: str) -> Dict:
    """Load dataset schema."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def load_required_variables(config_path: str) -> Tuple[List[str], List[str]]:
    """Load required predictors and outcomes from config."""
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        predictors = config.get('required_predictors', [])
        outcomes = config.get('required_outcomes', [])
        return predictors, outcomes
    except FileNotFoundError:
        logger.warning(f"Config file not found: {config_path}. Returning empty lists.")
        return [], []

def validate_variables(df: pd.DataFrame, predictors: List[str], outcomes: List[str]) -> Dict:
    """Validate that required variables are present in the dataframe."""
    missing_predictors = [p for p in predictors if p not in df.columns]
    missing_outcomes = [o for o in outcomes if o not in df.columns]
    
    metrics = {
        "total_predictors_requested": len(predictors),
        "predictors_found": len(predictors) - len(missing_predictors),
        "total_outcomes_requested": len(outcomes),
        "outcomes_found": len(outcomes) - len(missing_outcomes),
        "missing_predictors": missing_predictors,
        "missing_outcomes": missing_outcomes,
        "validation_passed": len(missing_predictors) == 0 and len(outcomes) == 0
    }
    
    # Save metrics
    metrics_path = "data/results/variable_load_metrics.json"
    Path("data/results").mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    if not metrics["validation_passed"]:
        error_msg = f"Validation failed. Missing predictors: {missing_predictors}, Missing outcomes: {missing_outcomes}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Validation passed. Found {metrics['predictors_found']} predictors and {metrics['outcomes_found']} outcomes.")
    return metrics

def fetch_real_data(source_config: str) -> pd.DataFrame:
    """Fetch real data from configured source."""
    # This would implement real data fetching logic
    raise RealDataFetchError("Real data fetching not implemented or source unavailable.")

def detect_outliers_iqr(df: pd.DataFrame) -> List[Dict]:
    """Detect outliers using IQR method."""
    outliers = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_indices = df[(df[col] < lower_bound) | (df[col] > upper_bound)].index
        
        for idx in outlier_indices:
            outliers.append({
                "subject_id": df.loc[idx, 'subject_id'] if 'subject_id' in df.columns else idx,
                "metric": col,
                "value": float(df.loc[idx, col]),
                "is_outlier": True
            })
    
    return outliers

def save_outlier_report(outliers: List[Dict], output_path: str):
    """Save outlier report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(outliers, f, indent=2)

def filter_outliers(df: pd.DataFrame, outliers: List[Dict]) -> Tuple[pd.DataFrame, Dict]:
    """Filter outliers from dataframe."""
    if not outliers:
        return df, {"exclusion_count": 0, "excluded_subjects": []}
    
    excluded_subjects = list(set([o['subject_id'] for o in outliers]))
    filtered_df = df[~df['subject_id'].isin(excluded_subjects)]
    
    exclusion_log = {
        "exclusion_count": len(excluded_subjects),
        "excluded_subjects": excluded_subjects,
        "filtered_data_path": "data/processed/filtered_data.parquet"
    }
    
    return filtered_df, exclusion_log

def save_filtered_data(df: pd.DataFrame, output_path: str):
    """Save filtered data to parquet."""
    df.to_parquet(output_path, index=False)

def record_artifact_checksum(file_path: str, state_file: str):
    """Record checksum of an artifact."""
    import hashlib
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found for checksum: {file_path}")
        return
    
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    state_dir = os.path.dirname(state_file)
    if state_dir:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            import yaml
            state = yaml.safe_load(f) or {}
    else:
        state = {"artifact_hashes": {}}
    
    state["artifact_hashes"][file_path] = file_hash
    
    with open(state_file, 'w') as f:
        import yaml
        yaml.dump(state, f)

def load_data(data_path: str) -> pd.DataFrame:
    """Load data and validate variables."""
    logger.info(f"Loading data from {data_path}")
    
    # Load required variables config
    config_path = "data/config/required_variables.yaml"
    predictors, outcomes = load_required_variables(config_path)
    
    # Load data
    if data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    elif data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path}")
    
    # Validate variables
    validate_variables(df, predictors, outcomes)
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Data ingestion and validation")
    parser.add_argument("--input", required=True, help="Input data file path")
    parser.add_argument("--output", default="data", help="Output directory")
    parser.add_argument("--mode", choices=["real", "synthetic"], default="synthetic", help="Data mode")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        df = load_data(args.input)
        print(f"Successfully loaded {len(df)} rows with {len(df.columns)} columns.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
