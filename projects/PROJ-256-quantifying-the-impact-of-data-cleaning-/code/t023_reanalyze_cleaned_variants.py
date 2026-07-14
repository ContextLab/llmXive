import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
import pandas as pd

from utils import setup_logging, pin_random_seed
from config import Config, get_config
from analysis import run_baseline_analysis

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[str]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Naming convention: <dataset_name>_<strategy>.csv
    """
    pattern = os.path.join(processed_dir, "*.csv")
    files = glob.glob(pattern)
    # Filter out files that are not cleaned variants (e.g., original baselines if mixed)
    # We assume cleaned files have a strategy suffix like '_outlier_removed', '_mean_imputed', etc.
    cleaned_files = [f for f in files if any(s in os.path.basename(f) for s in ['_outlier_', '_mean_', '_median_', '_knn_', '_recoded_'])]
    return cleaned_files

def analyze_cleaned_variant(filepath: str, config: Optional[Config] = None) -> Optional[Dict[str, Any]]:
    """
    Analyze a single cleaned dataset file.
    Returns a result dictionary compatible with baseline metrics.
    """
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    
    # Extract strategy from filename if possible
    strategy = "unknown"
    if "_outlier_" in name_without_ext:
        strategy = "outlier_removal"
    elif "_mean_" in name_without_ext:
        strategy = "mean_imputation"
    elif "_median_" in name_without_ext:
        strategy = "median_imputation"
    elif "_knn_" in name_without_ext:
        strategy = "knn_imputation"
    elif "_recoded_" in name_without_ext:
        strategy = "categorical_recoding"
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Analyzing cleaned variant: {name_without_ext} (strategy: {strategy})")
        
        # Run analysis using the flexible run_baseline_analysis function
        # We pass the dataframe directly to get a result dict
        result = run_baseline_analysis(df, dataset_name=name_without_ext)
        
        if result and result.get('t_test') or result.get('regression'):
            result['strategy'] = strategy
            result['file_path'] = filepath
            return result
        else:
            logger.warning(f"No valid results for {name_without_ext}")
            return None
    except Exception as e:
        logger.error(f"Failed to analyze {filepath}: {e}")
        return None

def main():
    """
    Main entry point for T023: Re-run t-tests and linear regressions on cleaned variants.
    Output: data/processed/cleaned_metrics.json
    """
    setup_logging("INFO")
    config = get_config()
    
    # Ensure random seed for reproducibility
    seed = config.get("RANDOM_SEED", 42)
    pin_random_seed(seed)
    
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    logger.info(f"Scanning for cleaned datasets in {processed_dir}")
    cleaned_files = find_cleaned_datasets(processed_dir)
    
    if not cleaned_files:
        logger.warning("No cleaned dataset files found. Creating empty metrics file.")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump({"datasets": [], "metadata": {"source": "cleaned_variants", "strategy": "all"}}, f, indent=2)
        return

    all_results = []
    for filepath in cleaned_files:
        res = analyze_cleaned_variant(filepath, config)
        if res:
            all_results.append(res)
    
    report = {
        "datasets": all_results,
        "metadata": {
            "source": "cleaned_variants",
            "timestamp": str(pd.Timestamp.now()),
            "total_processed": len(all_results)
        }
    }
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Successfully wrote cleaned metrics to {output_file}")

if __name__ == "__main__":
    main()