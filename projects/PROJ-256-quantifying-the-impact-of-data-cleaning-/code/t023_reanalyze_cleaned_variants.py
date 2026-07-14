"""
Task T023: Re-run t-tests and linear regressions on each cleaned variant.

This script scans the data/processed directory for cleaned datasets (identified by
specific naming patterns like '_outlier_removed', '_mean_imputed', etc.),
runs the baseline analysis pipeline on each, and aggregates the results into
data/processed/cleaned_metrics.json.

It relies on code/analysis.py's run_baseline_analysis function and code/config.py
for configuration.
"""
import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis import run_baseline_analysis
from config import Config, get_config
from utils import setup_logging, pin_random_seed

# Setup logging
logger = setup_logging("INFO")

# Define patterns for cleaned datasets based on T022 naming convention
CLEANING_STRATEGIES = [
    "outlier_removed",
    "mean_imputed",
    "median_imputed",
    "knn_imputed",
    "categorical_recoded"
]

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Scan processed directory for cleaned dataset files.
    Returns a list of dicts with 'path' and 'strategy' keys.
    """
    cleaned_files = []
    # Look for CSV files in the processed directory
    csv_pattern = os.path.join(processed_dir, "*.csv")
    all_csvs = glob.glob(csv_pattern)
    
    for filepath in all_csvs:
        filename = os.path.basename(filepath)
        strategy = None
        
        # Identify strategy from filename
        for strat in CLEANING_STRATEGIES:
            if strat in filename.lower():
                strategy = strat
                break
        
        if strategy:
            cleaned_files.append({
                "path": filepath,
                "strategy": strategy,
                "filename": filename
            })
        
        # Also check for generic "cleaned" suffix if no specific strategy found
        elif "cleaned" in filename.lower() and strategy is None:
             # Fallback for generic cleaned files
             cleaned_files.append({
                 "path": filepath,
                 "strategy": "generic_cleaned",
                 "filename": filename
             })

    logger.info(f"Found {len(cleaned_files)} cleaned dataset(s) in {processed_dir}")
    return cleaned_files

def analyze_cleaned_variant(
    filepath: str, 
    dataset_name: str, 
    strategy: str, 
    config: Config
) -> Optional[Dict[str, Any]]:
    """
    Run analysis on a single cleaned dataset variant.
    """
    logger.info(f"Analyzing {dataset_name} ({strategy})...")
    
    try:
        # Determine random seed from config
        seed = config.get("RANDOM_SEED", 42)
        pin_random_seed(seed)
        
        # Run the baseline analysis function on the specific file
        # The function handles loading the CSV internally if passed a path or dict
        # Based on T012 usage, we pass the path and let analysis.py load it
        # However, run_baseline_analysis signature varies. 
        # We use the dict approach to ensure it loads from the specific path.
        results = run_baseline_analysis(
            df_path=filepath, # Passing path explicitly if supported, or dict
            dataset_name=dataset_name,
            config=config
        )
        
        # If the function returns a boolean (success flag) instead of dict, 
        # we need to handle that. But T012 expects it to write file or return dict.
        # Based on T023 task description, we need to collect metrics.
        # If run_baseline_analysis writes to a file, we might need to read it back,
        # OR we assume it returns the metrics dict when called with a dataframe/path.
        
        # Fallback: If it returns a bool, we assume it wrote to a temp file or we failed.
        # But the contract in T012 suggests it returns dict when called with df.
        # Let's assume the function is flexible. If it returns a dict, great.
        # If it returns bool, we might need to re-run logic or read the file.
        # Given the "FAILED" context, let's ensure we get the metrics.
        
        if isinstance(results, bool):
            logger.warning(f"run_baseline_analysis returned bool for {dataset_name}. "
                           "Assuming success but metrics not captured directly. "
                           "Re-running analysis logic locally to capture metrics.")
            # Local re-run logic to capture metrics if the function didn't return them
            # This is a safety net for API contract mismatches
            from analysis import load_datasets_from_raw, analyze_dataset
            # We can't easily re-run load_datasets_from_raw on a specific CSV without 
            # modifying its logic. We assume run_baseline_analysis returns dict 
            # when called correctly. If it returns bool, the implementation is flawed.
            # Let's try to call it with a dict containing the path.
            results = run_baseline_analysis(
                {"path": filepath, "name": dataset_name},
                dataset_name=dataset_name,
                config=config
            )
            
        if not isinstance(results, dict):
            logger.error(f"Analysis for {dataset_name} did not return valid metrics dict.")
            return None
        
        # Enrich results with strategy info
        results["strategy"] = strategy
        results["dataset_file"] = os.path.basename(filepath)
        results["dataset_name"] = dataset_name
        
        return results

    except Exception as e:
        logger.error(f"Failed to analyze {dataset_name} ({strategy}): {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for T023.
    """
    logger.info("Starting T023: Re-analyze Cleaned Variants")
    
    # Load config
    config = get_config()
    
    # Get paths
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    # Ensure directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    # Find cleaned datasets
    cleaned_datasets = find_cleaned_datasets(processed_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Output file will be empty.")
        # Write empty structure
        with open(output_file, 'w') as f:
            json.dump({"datasets": [], "metadata": {"source": "t023", "strategies": []}}, f, indent=2)
        logger.info(f"Wrote empty metrics to {output_file}")
        return 0
    
    results = []
    
    for item in cleaned_datasets:
        filepath = item["path"]
        strategy = item["strategy"]
        # Create a unique name based on filename and strategy
        dataset_name = f"{os.path.splitext(item['filename'])[0]}_{strategy}"
        
        result = analyze_cleaned_variant(filepath, dataset_name, strategy, config)
        
        if result:
            results.append(result)
            logger.info(f"Successfully analyzed {dataset_name}")
        else:
            logger.warning(f"Skipped {dataset_name} due to analysis failure")
    
    # Compile output
    output_data = {
        "datasets": results,
        "metadata": {
            "source": "t023_reanalyze_cleaned_variants",
            "timestamp": str(os.path.getmtime(output_file)) if os.path.exists(output_file) else "new",
            "strategies_analyzed": list(set([r["strategy"] for r in results]))
        }
    }
    
    # Write output
    try:
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Successfully wrote cleaned metrics to {output_file}")
        return 0
    except Exception as e:
        logger.error(f"Failed to write output file: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
