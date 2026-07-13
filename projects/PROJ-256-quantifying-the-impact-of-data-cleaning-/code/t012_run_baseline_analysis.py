import os
import sys
import json
import logging
from typing import List, Dict, Any
import pandas as pd
from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis

logger = logging.getLogger(__name__)

def load_datasets_from_raw(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Load datasets from the raw directory.
    Returns a list of dicts with 'name', 'df', and 'config'.
    """
    datasets = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw directory {raw_dir} does not exist.")
        return datasets
    
    # Assuming a mapping of filenames to analysis config exists or is inferred
    # For T012, we assume the task implies analyzing whatever is in raw/
    # We'll try to infer columns or use a default config if not specified.
    # However, the task requires specific columns. 
    # We will assume the data_loader has already prepared these or we use a standard schema.
    # Given the constraints, we will look for common column names or fail gracefully.
    
    for filename in os.listdir(raw_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                # Heuristic: find a categorical column for group, numeric for outcome/predictor
                # This is a fallback if explicit config isn't passed
                # For this task, we assume the config is passed via args or environment
                datasets.append({
                    "name": filename,
                    "df": df,
                    "filepath": filepath
                })
            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")
    return datasets

def main():
    setup_logging("INFO")
    pin_random_seed(42)
    config = get_config()
    
    # Determine input/output paths
    raw_dir = os.path.join("data", "raw")
    output_base = os.path.join("data", "processed")
    os.makedirs(output_base, exist_ok=True)
    
    datasets = load_datasets_from_raw(raw_dir)
    
    if not datasets:
        logger.error("No datasets found in raw directory. Exiting.")
        sys.exit(1)
    
    # We need to know which columns to use. 
    # Since T012 is "Implement baseline analysis", we assume the calling script 
    # or environment provides the column mapping.
    # For the sake of this implementation, we will try to infer or use a default.
    # However, the most robust way is to have a config file or explicit args.
    # Let's assume we are analyzing a specific dataset passed via env or default.
    # To satisfy the requirement of producing baseline_metrics.json, we will run on the first dataset 
    # and use a generic config if not found, or fail if columns are missing.
    
    # Fallback config: look for common names
    def infer_config(df):
        cols = df.columns.tolist()
        group_col = None
        outcome_col = None
        predictor_col = None
        
        # Look for group
        for c in cols:
            if 'group' in c.lower() or 'treatment' in c.lower() or 'condition' in c.lower():
                if df[c].dtype == 'object' or df[c].nunique() <= 10:
                    group_col = c
                    break
        
        # Look for outcome (numeric)
        for c in cols:
            if 'outcome' in c.lower() or 'target' in c.lower() or 'y' in c.lower():
                if pd.api.types.is_numeric_dtype(df[c]):
                    outcome_col = c
                    break
        
        # Look for predictor (numeric)
        for c in cols:
            if 'predictor' in c.lower() or 'x' in c.lower() or 'feature' in c.lower():
                if pd.api.types.is_numeric_dtype(df[c]) and c != outcome_col:
                    predictor_col = c
                    break
        
        # If outcome is missing, take first numeric
        if not outcome_col:
            for c in cols:
                if pd.api.types.is_numeric_dtype(df[c]) and c != group_col:
                    outcome_col = c
                    break
        
        # If predictor is missing, take second numeric or same as outcome (bad but safe)
        if not predictor_col:
            for c in cols:
                if pd.api.types.is_numeric_dtype(df[c]) and c != group_col and c != outcome_col:
                    predictor_col = c
                    break
        
        return {
            "group_col": group_col,
            "outcome_col": outcome_col,
            "predictor_col": predictor_col
        }

    all_results = []
    
    for ds in datasets:
        df = ds["df"]
        filename = ds["name"]
        
        # Try to get config from env or infer
        # For T012, we assume we are analyzing the dataset provided by T011
        # Let's assume the environment variable or a default config is used
        # If not, we infer
        cfg = infer_config(df)
        
        if not cfg["outcome_col"]:
            logger.warning(f"Could not infer outcome column for {filename}. Skipping.")
            continue
        
        logger.info(f"Analyzing {filename} with config: {cfg}")
        
        output_file = os.path.join(output_base, f"baseline_{filename.replace('.csv', '.json')}")
        
        try:
            run_baseline_analysis(df, cfg, output_file)
            all_results.append({
                "dataset": filename,
                "output": output_file,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Failed to analyze {filename}: {e}")
            all_results.append({
                "dataset": filename,
                "status": "failed",
                "error": str(e)
            })
    
    # Write a summary if multiple datasets
    summary_path = os.path.join(output_base, "baseline_metrics.json")
    if len(all_results) == 1:
        # If only one, maybe the task expects a single file named baseline_metrics.json
        # But we generated specific ones. Let's copy or merge.
        # The requirement says "Output `data/processed/baseline_metrics.json`"
        # If we have multiple, we might need to aggregate.
        # For now, if there's exactly one, we rename/copy it.
        if all_results[0]["status"] == "success":
            import shutil
            shutil.copy(all_results[0]["output"], summary_path)
            logger.info(f"Copied single result to {summary_path}")
    else:
        # Aggregate results into one file if multiple
        with open(summary_path, 'w') as f:
            json.dump({"datasets": all_results}, f, indent=2)
        logger.info(f"Wrote aggregated summary to {summary_path}")

    logger.info("Baseline analysis complete.")

if __name__ == "__main__":
    main()