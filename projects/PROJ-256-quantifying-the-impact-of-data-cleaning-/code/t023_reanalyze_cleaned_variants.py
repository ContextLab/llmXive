import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
from analysis import run_baseline_analysis
from utils import setup_logging
from config import Config

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[str]:
    pattern = os.path.join(processed_dir, "*_outlier_removed.csv")
    return glob.glob(pattern)

def extract_strategy_from_filename(filename: str) -> str:
    # Simple extraction
    return "outlier_removed"

def analyze_cleaned_variant(filepath: str) -> Dict[str, Any]:
    import pandas as pd
    df = pd.read_csv(filepath)
    dataset_name = os.path.basename(filepath).replace(".csv", "")
    return run_baseline_analysis(df, dataset_name=dataset_name)

def main():
    setup_logging("INFO")
    config = Config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    cleaned_files = find_cleaned_datasets(processed_dir)
    if not cleaned_files:
        logger.warning("No cleaned datasets found to re-analyze.")
        # Write empty or placeholder if none found? No, just empty list.
        with open(output_file, 'w') as f:
            json.dump([], f)
        return True
    
    all_results = []
    for f in cleaned_files:
        logger.info(f"Analyzing cleaned variant: {f}")
        try:
            res = analyze_cleaned_variant(f)
            all_results.append(res)
        except Exception as e:
            logger.error(f"Failed to analyze {f}: {e}")
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Cleaned metrics written to {output_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
