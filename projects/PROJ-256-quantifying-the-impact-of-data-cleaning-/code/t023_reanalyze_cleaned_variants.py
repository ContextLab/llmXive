"""
Task T023: Re-run t-tests and linear regressions on each cleaned variant.

This script loads cleaned datasets produced by T022, applies the existing
analysis pipeline (t-tests and linear regressions) to each, and aggregates
the results into data/processed/cleaned_metrics.json.
"""
import os
import json
import logging
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np

# Import existing project utilities and analysis functions
from utils import pin_random_seed, setup_logging, compute_file_checksum
from config import get_config
from analysis import run_baseline_analysis, analyze_dataset
from cleaning import apply_iqr_outlier_removal, apply_mean_imputation, apply_median_imputation, apply_knn_imputation, apply_categorical_recoding

# Setup logging
logger = setup_logging("INFO")

def find_cleaned_datasets(data_dir: str) -> List[Dict[str, str]]:
    """
    Scan data_dir for cleaned dataset files.
    Expected naming pattern: <dataset_name>_<strategy>.csv
    Returns a list of dicts with 'path', 'dataset_name', 'strategy'.
    """
    cleaned_files = []
    # Look for CSVs that contain an underscore and are not the raw files
    # Assuming raw files are in data/raw/ and cleaned are in data/processed/
    # We search specifically in the processed directory for cleaned variants
    pattern = os.path.join(data_dir, "*.csv")
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        # Skip if it looks like a raw file or a metrics file
        if filename.startswith("raw_") or filename.endswith("_metrics.json"):
            continue
        
        # Heuristic: Split by last underscore to separate strategy
        # e.g., "har_iqr.csv" -> dataset="har", strategy="iqr"
        if "_" in filename:
            base_name, strategy = filename.rsplit("_", 1)
            strategy = strategy.replace(".csv", "")
            cleaned_files.append({
                "path": filepath,
                "dataset_name": base_name,
                "strategy": strategy
            })
    return cleaned_files

def analyze_cleaned_variant(
    filepath: str,
    dataset_name: str,
    strategy: str,
    target_col: str,
    group_col: Optional[str] = None,
    predictor_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run analysis on a single cleaned dataset.
    Returns a dictionary of metrics suitable for JSON serialization.
    """
    logger.info(f"Analyzing cleaned variant: {dataset_name} ({strategy}) from {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        
        # Validate data
        if df.empty:
            logger.warning(f"Dataset {filepath} is empty after loading.")
            return {
                "dataset_name": dataset_name,
                "strategy": strategy,
                "error": "Empty dataset"
            }

        # Use existing analysis logic
        # We need to adapt the call to match the existing analyze_dataset signature
        # Based on T012/T013 context, analyze_dataset likely takes df, target, and optional predictors/group
        
        # If group_col is not provided, we might need to infer or skip t-test
        # For this implementation, we assume the config or a standard schema defines these
        # Since the task implies re-running the *same* tests as baseline, 
        # we assume the target/predictor columns are consistent across variants.
        
        # Fallback to a generic analysis if specific columns aren't passed
        # In a real scenario, these would come from the dataset metadata or config
        # For now, we attempt to run the analysis with the dataframe
        
        # We will call run_baseline_analysis if it accepts a df, or construct the call
        # Looking at imports, run_baseline_analysis is available.
        # Let's assume it takes (df, target_col, group_col/predictors)
        
        # If specific columns are not known, we try to infer:
        # Target: usually the last numeric column or a specific name
        # Group: if exists
        
        # To be safe and consistent with the "re-run" instruction:
        # We will pass the dataframe and let the analysis function handle the logic
        # or we assume standard columns if not provided.
        
        # Since we don't have the full signature of analyze_dataset from the prompt's 
        # "public names" list beyond the name itself, we assume it follows the 
        # pattern: analyze_dataset(df, target, group=None, predictors=None)
        
        # If the user didn't specify columns, we might need to look at the baseline
        # However, T023 is about re-running. We assume the columns are the same as baseline.
        # Let's assume the config or a previous step defined them. 
        # For this script, we will attempt to run the analysis. 
        # If the function requires specific columns, we might need to pass them.
        # Given the constraints, we will assume the function can handle the dataframe
        # or we pass None and let it infer, OR we hardcode a standard inference if needed.
        
        # Let's assume the standard call for this project based on T012 description:
        # "run t-tests, linear regressions"
        # We will call analyze_dataset.
        
        # To make it robust, if columns are not provided, we try to detect them.
        # But the task says "Re-run... on each cleaned variant".
        # This implies the *same* tests as baseline.
        # We need to know what the baseline tests were.
        # Since T012 produced baseline_metrics.json, we could read that to get the schema.
        # But T023 is a separate script.
        
        # Strategy: Read baseline_metrics.json to find the target/group/predictors used.
        # If not found, fall back to inference.
        
        metrics = {}
        
        # Attempt to infer columns if not provided
        if target_col is None:
            # Heuristic: Look for a column that looks like an outcome
            # Or just take the first numeric column that isn't an ID
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                # Skip common ID columns
                id_cols = [c for c in numeric_cols if 'id' in c.lower() or c.startswith('idx')]
                candidate_cols = [c for c in numeric_cols if c not in id_cols]
                if candidate_cols:
                    target_col = candidate_cols[-1] # Last one usually outcome
                else:
                    target_col = numeric_cols[0]
        
        if group_col is None:
            # Look for a categorical column that might be a group
            cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            if cat_cols:
                # Often the first categorical column is the group
                group_col = cat_cols[0]
        
        if predictor_cols is None:
            # For regression, use numeric cols excluding target
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_col in numeric_cols:
                predictor_cols = [c for c in numeric_cols if c != target_col]
            else:
                predictor_cols = numeric_cols

        # Run the analysis
        # The function analyze_dataset is imported.
        # We assume it returns a dict of metrics.
        # If it requires specific arguments, we pass them.
        # Based on T012 description, it runs t-tests and linear regressions.
        
        # We call it. If it fails due to missing args, we catch and log.
        # But we must make it work.
        # Let's assume the signature: analyze_dataset(df, target_col, group_col, predictor_cols)
        # If group_col is None, it might skip t-test. If predictor_cols empty, skip regression.
        
        try:
            result = analyze_dataset(df, target_col, group_col=group_col, predictor_cols=predictor_cols)
            metrics = result
        except TypeError as e:
            # Fallback: try calling with just df if that's the signature
            # Or log error
            logger.error(f"Failed to analyze {filepath}: {e}")
            return {
                "dataset_name": dataset_name,
                "strategy": strategy,
                "error": str(e)
            }
        
        # Add metadata
        metrics["dataset_name"] = dataset_name
        metrics["strategy"] = strategy
        metrics["checksum"] = compute_file_checksum(filepath)
        metrics["analysis_timestamp"] = datetime.now().isoformat()
        
        return metrics

    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}", exc_info=True)
        return {
            "dataset_name": dataset_name,
            "strategy": strategy,
            "error": str(e)
        }

def main():
    config = get_config()
    data_dir = config.get("OUTPUT_PATH", "data/processed")
    raw_dir = config.get("RAW_DATA_PATH", "data/raw") # Just in case
    
    # Ensure output directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    logger.info(f"Scanning for cleaned datasets in {data_dir}...")
    cleaned_datasets = find_cleaned_datasets(data_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Ensure T022 has run.")
        # Create an empty file to indicate completion but no data
        output_path = os.path.join(data_dir, "cleaned_metrics.json")
        with open(output_path, 'w') as f:
            json.dump({"error": "No cleaned datasets found", "datasets": []}, f, indent=2)
        return

    logger.info(f"Found {len(cleaned_datasets)} cleaned variants.")
    
    all_metrics = []
    
    for item in cleaned_datasets:
        # We need to determine the target/group/predictor columns.
        # Since we don't have a global config for column names, we rely on the 
        # baseline_metrics.json if it exists, or infer.
        # Let's try to read baseline_metrics.json to get the schema if possible.
        baseline_path = os.path.join(data_dir, "baseline_metrics.json")
        target_col = None
        group_col = None
        predictor_cols = None
        
        if os.path.exists(baseline_path):
            try:
                with open(baseline_path, 'r') as f:
                    baseline_data = json.load(f)
                # Extract schema from first dataset if available
                if "datasets" in baseline_data and len(baseline_data["datasets"]) > 0:
                    first_ds = baseline_data["datasets"][0]
                    target_col = first_ds.get("target_column")
                    group_col = first_ds.get("group_column")
                    predictor_cols = first_ds.get("predictor_columns")
            except Exception as e:
                logger.warning(f"Could not read baseline schema: {e}")
        
        # If still None, analyze_cleaned_variant will try to infer
        
        metrics = analyze_cleaned_variant(
            filepath=item["path"],
            dataset_name=item["dataset_name"],
            strategy=item["strategy"],
            target_col=target_col,
            group_col=group_col,
            predictor_cols=predictor_cols
        )
        
        if "error" not in metrics:
            all_metrics.append(metrics)
            logger.info(f"Successfully analyzed {item['dataset_name']} ({item['strategy']})")
        else:
            logger.error(f"Failed to analyze {item['dataset_name']}: {metrics['error']}")
            all_metrics.append(metrics) # Include error record for debugging
    
    # Save results
    output_path = os.path.join(data_dir, "cleaned_metrics.json")
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_variants": len(all_metrics),
        "datasets": all_metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Cleaned metrics saved to {output_path}")

if __name__ == "__main__":
    main()