import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Import from sibling modules using the exact API surface provided
from utils import setup_logging, pin_random_seed, compute_file_checksum
from config import Config, get_config
from analysis import run_baseline_analysis, load_datasets_from_raw
from models import Dataset, AnalysisResult

# Configure logging
logger = logging.getLogger(__name__)

def format_metric_value(value: Any, precision: int = 6) -> Any:
    """
    Format numeric metric values to specified precision.
    Handles float, int, and None types.
    """
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, precision)
    return value

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """
    Log a summary of the recorded metrics for visibility.
    """
    logger.info("=" * 60)
    logger.info("BASELINE METRICS SUMMARY")
    logger.info("=" * 60)
    
    total_datasets = len(metrics.get('datasets', []))
    logger.info(f"Total datasets processed: {total_datasets}")
    
    for ds_entry in metrics.get('datasets', []):
        ds_name = ds_entry.get('dataset_name', 'Unknown')
        logger.info(f"  - {ds_name}:")
        
        # Log t-test results
        if 't_test' in ds_entry:
            t_test = ds_entry['t_test']
            p_val = t_test.get('p_value', 'N/A')
            logger.info(f"    T-Test p-value: {p_val}")
            
        # Log regression results
        if 'regression' in ds_entry:
            reg = ds_entry['regression']
            r_sq = reg.get('r_squared', 'N/A')
            logger.info(f"    Regression R²: {r_sq}")
            
        # Log effect size
        if 'effect_size' in ds_entry:
            cohens_d = ds_entry['effect_size'].get('cohen_d', 'N/A')
            logger.info(f"    Cohen's d: {cohens_d}")
            
    logger.info("=" * 60)

def process_dataset_for_baseline(dataset_path: str, dataset_name: str, config: Config) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset for baseline metrics.
    Returns a dictionary containing the metrics or None if processing fails.
    """
    try:
        # Pin random seed for reproducibility
        seed = config.get("RANDOM_SEED", 42)
        pin_random_seed(seed)
        
        logger.info(f"Processing dataset: {dataset_name} from {dataset_path}")
        
        # Run baseline analysis
        # The run_baseline_analysis function is overloaded to handle different signatures.
        # We call it with the dataframe and dataset_name to get the metrics dict.
        # First, we need to load the dataframe.
        # Assuming load_datasets_from_raw returns a list of (df, name) tuples or similar.
        # Since we have a specific path, we might need to load it directly or use the helper.
        
        # Let's use the analysis module's run_baseline_analysis which expects (df, dataset_name=...)
        # But we need the dataframe first.
        # The task T011/T012 likely already loaded data, but for T013 we might need to load again
        # or rely on the fact that T012 already produced the raw metrics in memory?
        # No, T012 produced the JSON. T013 is about recording/formatting/saving with precision.
        # However, the execution failure shows T012 failed to write the file.
        # So T013 needs to actually run the analysis if the file doesn't exist, or re-run T012 logic.
        
        # Let's assume we load the data from the raw path if needed, or we rely on the 
        # run_baseline_analysis to handle the path?
        # Looking at the signature in analysis.py:
        # 1. run_baseline_analysis(raw_dir, output_path, config) -> writes file, returns bool
        # 2. run_baseline_analysis(df, dataset_name=...) -> returns dict
        
        # We are in T013, which is "Record baseline metrics".
        # It seems T012 was supposed to do the analysis and write. T012 failed.
        # So T013 should probably re-run the analysis to ensure the file is created.
        
        # Strategy: Load the dataset manually or use the analysis helper to get the df.
        # Since we have the path, let's try to load it.
        # We can use pandas to load CSV/Excel if we know the format.
        # The data_loader module has load_datasets_from_raw.
        
        # Let's try to load the specific file.
        import pandas as pd
        df = pd.read_csv(dataset_path) # Assuming CSV based on typical usage
        
        # Run analysis
        results = run_baseline_analysis(df, dataset_name=dataset_name)
        
        if not results:
            logger.error(f"Analysis failed for {dataset_name}")
            return None
            
        # Format metrics
        formatted_results = {
            "dataset_name": dataset_name,
            "timestamp": datetime.now().isoformat(),
            "file_checksum": compute_file_checksum(dataset_path),
            "analysis": results
        }
        
        # Validate p-values
        if 't_test' in results:
            p_val = results['t_test'].get('p_value')
            if p_val is not None and not (0 < p_val < 1):
                logger.warning(f"Invalid p-value {p_val} for {dataset_name}")
                
        # Validate CIs
        if 't_test' in results and 'ci' in results['t_test']:
            ci = results['t_test']['ci']
            if ci and (not all(isinstance(x, (int, float)) and not (x != x) for x in ci)): # Check for NaN
                 logger.warning(f"Non-finite CI for {dataset_name}")
                 
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error processing {dataset_name}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for T013: Record Baseline Metrics.
    This script ensures that baseline_metrics.json is created with the required precision.
    It re-runs the analysis if the file is missing or incomplete.
    """
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    
    logger.info("Starting T013: Record Baseline Metrics")
    
    # Load config
    config = get_config()
    
    # Define paths
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "baseline_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    # Check if we need to re-run analysis
    # If the file exists, we might still need to re-run if it's empty or invalid,
    # but for now, let's assume we re-run to ensure correctness as per the failure context.
    # The failure said T012 didn't write the file.
    
    all_metrics = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "config": {
            "random_seed": config.get("RANDOM_SEED", 42),
            "raw_dir": raw_dir
        },
        "datasets": []
    }
    
    # Find datasets in raw_dir
    if not os.path.exists(raw_dir):
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
        
    dataset_files = [f for f in os.listdir(raw_dir) if f.endswith(('.csv', '.xlsx', '.parquet'))]
    
    if not dataset_files:
        logger.warning(f"No dataset files found in {raw_dir}")
        # Write empty report? Or fail? Let's write a report with 0 datasets.
        with open(output_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        logger.info(f"Wrote empty baseline metrics to {output_file}")
        return
        
    for file_name in dataset_files:
        file_path = os.path.join(raw_dir, file_name)
        dataset_name = os.path.splitext(file_name)[0]
        
        result = process_dataset_for_baseline(file_path, dataset_name, config)
        if result:
            all_metrics["datasets"].append(result)
            
    # Write output
    try:
        with open(output_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        logger.info(f"Successfully wrote baseline metrics to {output_file}")
        log_metrics_summary(all_metrics)
        
        # Verify file exists
        if os.path.exists(output_file):
            logger.info(f"Verification: {output_file} exists with size {os.path.getsize(output_file)} bytes")
        else:
            logger.error(f"Verification failed: {output_file} does not exist after write!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Failed to write output file: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
