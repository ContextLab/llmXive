import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Import from local modules
from analysis import run_baseline_analysis
from config import get_config

logger = logging.getLogger(__name__)

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Returns list of dicts with 'path' and 'strategy'.
    """
    pattern = os.path.join(processed_dir, "*.csv")
    files = glob.glob(pattern)
    
    cleaned_files = []
    if not os.path.exists(processed_dir):
        logger.warning(f"Processed directory {processed_dir} does not exist.")
        return cleaned_files

    # Look for files with specific patterns indicating cleaning
    patterns = [
        "outlier_removed.csv",
        "mean_imputed.csv",
        "median_imputed.csv",
        "knn_imputed.csv",
        "recoded.csv"
    ]

    for pattern in patterns:
        matches = glob.glob(os.path.join(processed_dir, f"*{pattern}"))
        for match in matches:
            filename = os.path.basename(match)
            # Infer strategy from filename
            strategy = "unknown"
            if "outlier" in filename: strategy = "outlier_removal"
            elif "mean" in filename: strategy = "mean_imputation"
            elif "median" in filename: strategy = "median_imputation"
            elif "knn" in filename: strategy = "knn_imputation"
            elif "recoded" in filename: strategy = "categorical_recoding"
            
            cleaned_files.append({
                "path": match,
                "strategy": strategy,
                "name": os.path.splitext(filename)[0]
            })
    
    return cleaned_files

def analyze_cleaned_variant(df: pd.DataFrame, dataset_name: str, strategy: str, config: Dict) -> Dict[str, Any]:
    """
    Analyze a single cleaned dataset variant.
    """
    result = run_baseline_analysis(
        df,
        dataset_name=dataset_name,
        config=config
    )
    
    if isinstance(result, dict) and "success" in result:
        return {
            "dataset_name": dataset_name,
            "cleaning_strategy": strategy,
            "analysis": result.get("result", {})
        }
    elif isinstance(result, dict):
        return {
            "dataset_name": dataset_name,
            "cleaning_strategy": strategy,
            "analysis": result
        }
    return {"error": "Analysis failed", "dataset_name": dataset_name, "cleaning_strategy": strategy}

def main():
    """
    Main entry point for T023: Re-run t-tests and linear regressions on cleaned variants.
    Output: data/processed/cleaned_metrics.json
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    seed = config.get("RANDOM_SEED", 42)
    
    # Pin random seed
    import numpy as np
    np.random.seed(seed)
    
    logger.info(f"Scanning for cleaned datasets in {processed_dir}")
    cleaned_files = find_cleaned_datasets(processed_dir)
    
    if not cleaned_files:
        logger.warning("No cleaned datasets found. Skipping analysis.")
        # Write empty result to satisfy artifact requirement
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "datasets": [],
            "note": "No cleaned datasets found to analyze."
        }
        os.makedirs(os.path.dirname("data/processed/cleaned_metrics.json"), exist_ok=True)
        with open("data/processed/cleaned_metrics.json", 'w') as f:
            json.dump(output_data, f, indent=2)
        return 0

    results = []
    for file_info in cleaned_files:
        logger.info(f"Analyzing: {file_info['name']} ({file_info['strategy']})")
        try:
            df = pd.read_csv(file_info['path'])
            result = analyze_cleaned_variant(df, file_info['name'], file_info['strategy'], config)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to analyze {file_info['path']}: {e}")
            results.append({
                "error": str(e),
                "dataset_name": file_info['name'],
                "cleaning_strategy": file_info['strategy']
            })

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "datasets": results,
        "total_analyzed": len([r for r in results if "error" not in r])
    }

    output_path = "data/processed/cleaned_metrics.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Wrote cleaned metrics to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
