"""
Task T023: Re-run t-tests and linear regressions on each cleaned variant.

This script iterates over cleaned dataset files produced by User Story 2,
applies the baseline analysis logic (t-tests, linear regression) to each,
and aggregates the results into `data/processed/cleaned_metrics.json`.

It relies on the `run_baseline_analysis` function from `code/analysis.py`,
which is designed to handle both file paths and DataFrames.
"""
import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import local modules
from analysis import run_baseline_analysis
from config import Config, get_config
from utils import setup_logging, pin_random_seed

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[str]:
    """
    Find all CSV files in the processed directory that represent cleaned variants.
    Based on the naming convention from T022: `dataset_strategy.csv`.
    We exclude `baseline_metrics.json` and other non-CSV artifacts.
    """
    pattern = os.path.join(processed_dir, "*.csv")
    files = glob.glob(pattern)
    
    cleaned_files = []
    for f in files:
        filename = os.path.basename(f)
        # Skip files that are clearly not cleaned data variants (e.g., if any exist)
        # We assume any CSV in processed_dir from this pipeline is a cleaned variant
        # or raw data. T022 saves cleaned data here.
        if "baseline" not in filename and "null" not in filename:
            cleaned_files.append(f)
    
    if not cleaned_files:
        logger.warning(f"No cleaned CSV files found in {processed_dir}. "
                       "Ensure T022 (save_cleaned_datasets) has run successfully.")
    
    return cleaned_files

def analyze_cleaned_variant(filepath: str, config: Config) -> Optional[Dict[str, Any]]:
    """
    Run baseline analysis on a single cleaned dataset file.
    
    Returns a dictionary containing the analysis results for this specific file,
    including the dataset name, strategy (inferred from filename), and metrics.
    """
    filename = os.path.basename(filepath)
    dataset_name = os.path.splitext(filename)[0]
    
    logger.info(f"Analyzing cleaned variant: {dataset_name}")
    
    try:
        # Run the baseline analysis logic on the file path.
        # The run_baseline_analysis function in analysis.py is designed to accept
        # a file path (string) and return a dict of results.
        result = run_baseline_analysis(filepath, dataset_name=dataset_name, config=config)
        
        if result and isinstance(result, dict):
            # Add metadata to the result for the final aggregation
            result['source_file'] = filepath
            result['analysis_timestamp'] = datetime.now().isoformat()
            return result
        else:
            logger.error(f"Analysis returned no result or invalid type for {filepath}: {type(result)}")
            return None
    except Exception as e:
        logger.error(f"Failed to analyze {filepath}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for T023.
    1. Load configuration.
    2. Find cleaned datasets.
    3. Analyze each.
    4. Aggregate and save to data/processed/cleaned_metrics.json.
    """
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)
    
    # Pin random seed for reproducibility
    seed = int(os.getenv("RANDOM_SEED", "42"))
    pin_random_seed(seed)
    
    # Load config
    config = get_config()
    
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    logger.info(f"Starting T023: Re-analyzing cleaned variants in {processed_dir}")
    logger.info(f"Output will be written to {output_file}")
    
    # Ensure output directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    # Find cleaned datasets
    cleaned_files = find_cleaned_datasets(processed_dir)
    
    if not cleaned_files:
        logger.error("No cleaned datasets found. Cannot proceed with T023.")
        # Create an empty output file to indicate completion (with zero datasets)
        # This prevents downstream tasks from crashing on missing files
        with open(output_file, 'w') as f:
            json.dump({
                "status": "no_data",
                "message": "No cleaned datasets found to analyze.",
                "datasets": [],
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        return 1
    
    results = []
    success_count = 0
    failure_count = 0
    
    for filepath in cleaned_files:
        result = analyze_cleaned_variant(filepath, config)
        if result:
            results.append(result)
            success_count += 1
        else:
            failure_count += 1
    
    # Aggregate results
    output_data = {
        "status": "complete" if failure_count == 0 else "partial",
        "total_files_found": len(cleaned_files),
        "successful_analyses": success_count,
        "failed_analyses": failure_count,
        "timestamp": datetime.now().isoformat(),
        "datasets": results
    }
    
    # Write output
    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        logger.info(f"Successfully wrote cleaned metrics to {output_file}")
        logger.info(f"Summary: {success_count} succeeded, {failure_count} failed.")
    except Exception as e:
        logger.error(f"Failed to write output file {output_file}: {e}")
        return 1
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
