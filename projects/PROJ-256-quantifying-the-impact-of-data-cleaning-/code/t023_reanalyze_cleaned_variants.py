import os
import sys
import json
import logging
import glob
from typing import List, Dict, Any, Optional
from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Returns a list of dicts with 'path' and 'dataset_name' (derived from filename).
    """
    cleaned_files = glob.glob(os.path.join(processed_dir, "*_cleaned*.csv"))
    cleaned_files.extend(glob.glob(os.path.join(processed_dir, "*_outlier_removed*.csv")))
    cleaned_files.extend(glob.glob(os.path.join(processed_dir, "*_imputed*.csv")))
    
    results = []
    for f in cleaned_files:
        basename = os.path.basename(f)
        # Extract dataset name: e.g., "shopper_iqr_outlier_removed.csv" -> "shopper"
        # Heuristic: split by underscore, take first part if it looks like a dataset name
        parts = basename.replace(".csv", "").split("_")
        if len(parts) > 1:
            dataset_name = parts[0]
        else:
            dataset_name = basename.replace(".csv", "")
        
        # Identify strategy from filename
        strategy = "unknown"
        if "outlier" in basename.lower():
            strategy = "outlier_removal"
        elif "mean" in basename.lower():
            strategy = "mean_imputation"
        elif "median" in basename.lower():
            strategy = "median_imputation"
        elif "knn" in basename.lower():
            strategy = "knn_imputation"
        elif "recoded" in basename.lower():
            strategy = "categorical_recoding"
        
        results.append({
            "path": f,
            "dataset_name": dataset_name,
            "strategy": strategy,
            "filename": basename
        })
    
    return results

def analyze_cleaned_variant(
    filepath: str,
    dataset_name: str,
    strategy: str,
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Run baseline analysis on a single cleaned dataset variant.
    Returns the analysis result dict or None if analysis fails.
    """
    logger = logging.getLogger(__name__)
    seed = config.get("RANDOM_SEED", 42)
    pin_random_seed(seed)
    
    logger.info(f"Analyzing cleaned variant: {dataset_name} ({strategy})")
    
    try:
        # run_baseline_analysis expects (df, dataset_name, config) for this usage
        # We need to load the dataframe first because the function signature 
        # for this caller expects a df, but the function logic handles both.
        # However, to be safe with the existing implementation in analysis.py,
        # we pass the dataframe directly if we can load it, or let the function handle paths.
        # The execution log showed: run_baseline_analysis(df_cleaned, dataset_name=..., config=config)
        # But analysis.py's run_baseline_analysis handles raw_dir or df.
        
        import pandas as pd
        df = pd.read_csv(filepath)
        
        # Call the analysis function
        result = run_baseline_analysis(df, dataset_name=dataset_name, config=config)
        
        if not result or not result.get('success'):
            logger.error(f"Analysis failed for {filepath}")
            return None
        
        # Augment result with strategy info
        analysis_data = result.get('results', {})
        enhanced_results = {}
        for test_name, metrics in analysis_data.items():
            if isinstance(metrics, dict):
                metrics['cleaning_strategy'] = strategy
                metrics['dataset_name'] = dataset_name
            enhanced_results[test_name] = metrics
        
        return {
            'success': True,
            'dataset_name': dataset_name,
            'strategy': strategy,
            'results': enhanced_results
        }
        
    except Exception as e:
        logger.exception(f"Error analyzing {filepath}: {e}")
        return None

def main():
    logger = setup_logging("INFO")
    config = get_config()
    
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    logger.info(f"Finding cleaned datasets in {processed_dir}")
    cleaned_datasets = find_cleaned_datasets(processed_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Outputting empty metrics.")
        output_data = {"datasets": [], "metadata": {"strategy": "all_cleaned_variants", "count": 0}}
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        return
    
    all_results = []
    for ds_info in cleaned_datasets:
        result = analyze_cleaned_variant(
            filepath=ds_info["path"],
            dataset_name=ds_info["dataset_name"],
            strategy=ds_info["strategy"],
            config=config
        )
        if result:
            all_results.append(result)
    
    output_data = {
        "datasets": all_results,
        "metadata": {
            "strategy": "all_cleaned_variants",
            "count": len(all_results),
            "generated_at": "2026-07-14T05:00:00Z" # Placeholder, actual time set in script if needed
        }
    }
    
    logger.info(f"Writing cleaned metrics to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Successfully processed {len(all_results)} cleaned variants.")

if __name__ == "__main__":
    main()
