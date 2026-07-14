import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
from utils import setup_logging
from config import get_config
from analysis import run_baseline_analysis
import pandas as pd

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, Any]]:
    """Find all cleaned dataset CSVs in the processed directory."""
    cleaned_files = []
    pattern = os.path.join(processed_dir, "*_cleaned*.csv")
    files = glob.glob(pattern)
    
    for f in files:
        cleaned_files.append({
            "path": f,
            "name": os.path.basename(f).replace(".csv", "")
        })
    
    # Also look for generic cleaned patterns
    pattern2 = os.path.join(processed_dir, "*_outlier_removed*.csv")
    files2 = glob.glob(pattern2)
    for f in files2:
        cleaned_files.append({
            "path": f,
            "name": os.path.basename(f).replace(".csv", "")
        })
    
    return cleaned_files

def analyze_cleaned_variant(filepath: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze a single cleaned dataset variant."""
    try:
        df = pd.read_csv(filepath)
        dataset_name = os.path.basename(filepath).replace(".csv", "")
        
        # Run analysis
        result = run_baseline_analysis(df=df, dataset_name=dataset_name, config=config)
        
        if result:
            return {
                "dataset": dataset_name,
                "path": filepath,
                "analysis": result
            }
        return None
    except Exception as e:
        logger.error(f"Failed to analyze {filepath}: {e}")
        return None

def main():
    setup_logging("INFO")
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    logger.info(f"Searching for cleaned datasets in {processed_dir}")
    cleaned_datasets = find_cleaned_datasets(processed_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Creating placeholder output.")
        # Create placeholder if no cleaned data exists
        with open(output_file, 'w') as f:
            json.dump({"cleaned": {"datasets": []}}, f, indent=2)
        return 0
    
    all_results = {"cleaned": {"datasets": []}}
    
    for ds in cleaned_datasets:
        logger.info(f"Analyzing {ds['name']}")
        result = analyze_cleaned_variant(ds['path'], config)
        if result:
            all_results["cleaned"]["datasets"].append(result)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Cleaned metrics written to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())