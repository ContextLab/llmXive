import os
import sys
import json
import logging
from typing import List, Dict, Any
from data_loader import download_dataset, load_datasets_from_raw
from analysis import run_baseline_analysis
from utils import setup_logging
from config import Config

logger = logging.getLogger(__name__)

def main():
    setup_logging("INFO")
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_path = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    os.makedirs(output_path, exist_ok=True)
    
    dfs = load_datasets_from_raw(raw_dir)
    if not dfs:
        logger.error("No datasets found. Please download data first.")
        return False
    
    all_results = []
    
    for df in dfs:
        # Heuristic: use filename without extension
        dataset_name = "dataset" # Simplified for now
        logger.info(f"Running baseline analysis on {dataset_name}")
        
        results = run_baseline_analysis(df, dataset_name=dataset_name, config=config)
        all_results.append(results)
    
    output_file = os.path.join(output_path, "baseline_metrics.json")
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Baseline metrics written to {output_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
