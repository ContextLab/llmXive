import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import run_baseline_analysis, write_output
from config import get_config

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Find all cleaned dataset files in the processed directory.
    Returns a list of dicts with 'path' and 'strategy'.
    """
    cleaned_files = []
    patterns = [
        os.path.join(processed_dir, "*_outlier_removed.csv"),
        os.path.join(processed_dir, "*_mean_imputed.csv"),
        os.path.join(processed_dir, "*_median_imputed.csv"),
        os.path.join(processed_dir, "*_knn_imputed.csv"),
        os.path.join(processed_dir, "*_recoded.csv")
    ]

    for pattern in patterns:
        matches = glob.glob(pattern)
        for match in matches:
            filename = os.path.basename(match)
            # Infer strategy from filename
            strategy = "unknown"
            if "outlier" in filename:
                strategy = "outlier_removal"
            elif "mean" in filename:
                strategy = "mean_imputation"
            elif "median" in filename:
                strategy = "median_imputation"
            elif "knn" in filename:
                strategy = "knn_imputation"
            elif "recoded" in filename:
                strategy = "categorical_recoding"

            cleaned_files.append({
                "path": match,
                "filename": filename,
                "strategy": strategy
            })

    return cleaned_files

def analyze_cleaned_variant(
    filepath: str,
    strategy: str,
    config: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Analyze a single cleaned dataset variant.
    """
    try:
        df = pd.read_csv(filepath)
        dataset_name = os.path.splitext(os.path.basename(filepath))[0]
        
        # Run analysis
        result = run_baseline_analysis(
            df,
            dataset_name=dataset_name,
            config=config
        )
        
        # Add strategy info to result
        if isinstance(result, dict) and "results" in result:
            for res in result["results"]:
                res["cleaning_strategy"] = strategy
        
        return result
    except Exception as e:
        logger.error(f"Failed to analyze {filepath}: {e}")
        return {"error": str(e), "strategy": strategy, "file": filepath}

def main():
    """
    Main entry point: Find cleaned datasets, analyze them, and save metrics.
    """
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO),
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Load config
    config_obj = get_config()
    config = {
        "RANDOM_SEED": config_obj.get("RANDOM_SEED", 42),
        "PROCESSED_DATA_PATH": config_obj.get("PROCESSED_DATA_PATH", "data/processed")
    }

    processed_dir = config["PROCESSED_DATA_PATH"]
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")

    logger.info(f"Searching for cleaned datasets in {processed_dir}")
    cleaned_files = find_cleaned_datasets(processed_dir)

    if not cleaned_files:
        logger.warning("No cleaned datasets found. Skipping analysis.")
        # Write empty result to satisfy output requirement
        write_output({
            "analysis_timestamp": None,
            "datasets_analyzed": 0,
            "results": [],
            "note": "No cleaned datasets found in processed directory."
        }, output_file)
        return True

    all_results = []
    for file_info in cleaned_files:
        logger.info(f"Analyzing: {file_info['filename']} (Strategy: {file_info['strategy']})")
        result = analyze_cleaned_variant(file_info['path'], file_info['strategy'], config)
        if result and "results" in result:
            all_results.extend(result["results"])
        elif result:
            # Single result case
            all_results.append(result)

    # Aggregate results
    output_data = {
        "analysis_timestamp": None, # Will be set by run_baseline_analysis if called as dict, but here we aggregate
        "datasets_analyzed": len(all_results),
        "results": all_results
    }

    output_path = "data/processed/cleaned_metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Set timestamp manually for the aggregate
    from datetime import datetime
    output_data["analysis_timestamp"] = datetime.now().isoformat()

    success = write_output(output_data, output_file)
    
    if success:
        logger.info(f"Cleaned metrics written to {output_file}")
    else:
        logger.error("Failed to write cleaned metrics.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
