import os
import sys
import json
import logging
import glob
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from local modules
from analysis import analyze_dataset, save_json_file
from config import Config, get_config
from utils import setup_logging, compute_file_checksum

def find_cleaned_datasets(processed_dir: str) -> List[Dict[str, str]]:
    """
    Find all cleaned dataset CSVs in the processed directory.
    Returns a list of dicts with dataset info.
    """
    logger = logging.getLogger(__name__)
    cleaned_datasets = []
    
    # Pattern to match cleaned datasets (e.g., *_outlier_removed.csv, *_mean_imputed.csv)
    patterns = [
        os.path.join(processed_dir, "*_outlier_removed.csv"),
        os.path.join(processed_dir, "*_mean_imputed.csv"),
        os.path.join(processed_dir, "*_median_imputed.csv"),
        os.path.join(processed_dir, "*_knn_imputed.csv"),
        os.path.join(processed_dir, "*_recoded.csv")
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for filepath in files:
            filename = os.path.basename(filepath)
            # Extract dataset name and strategy from filename
            # Expected format: datasetname_strategy.csv
            name_part = filename.replace(".csv", "")
            parts = name_part.rsplit("_", 1)
            
            if len(parts) >= 2:
                dataset_name = parts[0]
                strategy = parts[1]
            else:
                dataset_name = name_part
                strategy = "unknown"
            
            cleaned_datasets.append({
                "filepath": filepath,
                "dataset_name": dataset_name,
                "strategy": strategy,
                "filename": filename
            })
    
    logger.info(f"Found {len(cleaned_datasets)} cleaned datasets in {processed_dir}")
    return cleaned_datasets

def analyze_cleaned_variant(
    dataset_info: Dict[str, str],
    config: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single cleaned dataset variant.
    Runs t-tests and linear regressions on the cleaned data.
    """
    logger = logging.getLogger(__name__)
    
    try:
        filepath = dataset_info["filepath"]
        dataset_name = dataset_info["dataset_name"]
        strategy = dataset_info["strategy"]
        
        # Load the cleaned dataset
        logger.info(f"Loading cleaned dataset: {filepath}")
        df = pd.read_csv(filepath)
        
        # Determine columns for analysis based on dataset type
        # Default configuration for common datasets
        outcome_col = config.get("outcome_col") if config else None
        group_col = config.get("group_col") if config else None
        
        # Try to infer columns if not provided
        if not outcome_col or not group_col:
            logger.warning("Outcome or group column not specified, attempting to infer...")
            # Simple inference: look for common column names
            if "activity" in df.columns:
                outcome_col = "activity"
            elif "purchase" in df.columns:
                outcome_col = "purchase"
            else:
                # Use first categorical column as outcome if available
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                if categorical_cols:
                    outcome_col = categorical_cols[0]
                else:
                    logger.error("Could not determine outcome column")
                    return None
            
            if "subject" in df.columns:
                group_col = "subject"
            elif "gender" in df.columns:
                group_col = "gender"
            else:
                # Use second categorical column or first numeric if no categorical
                categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                if len(categorical_cols) > 1:
                    group_col = categorical_cols[1]
                else:
                    numeric_cols = df.select_dtypes(include=[pd.api.types.is_numeric_dtype]).columns.tolist()
                    if numeric_cols:
                        group_col = numeric_cols[0]
                    else:
                        logger.error("Could not determine group column")
                        return None
        
        logger.info(f"Using outcome_col={outcome_col}, group_col={group_col}")
        
        # Run analysis
        result = analyze_dataset(df, dataset_name, outcome_col, group_col)
        
        if result:
            # Add strategy info to result
            result["strategy"] = strategy
            result["dataset_path"] = filepath
            result["n_rows"] = len(df)
            result["n_columns"] = len(df.columns)
            result["outcome_col"] = outcome_col
            result["group_col"] = group_col
            result["analysis_timestamp"] = datetime.now().isoformat()
            
            logger.info(f"Analysis complete for {dataset_name} ({strategy}): p-value={result.get('t_test', {}).get('p_value', 'N/A')}")
            return result
        else:
            logger.error(f"Analysis failed for {dataset_name} ({strategy})")
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing {dataset_info.get('filepath', 'unknown')}: {str(e)}", exc_info=True)
        return None

def main():
    """
    Main entry point for T023: Re-analyze cleaned variants.
    Finds all cleaned datasets, runs analysis, and outputs cleaned_metrics.json.
    """
    logger = setup_logging("INFO")
    logger.info("Starting T023: Re-analyze cleaned variants")
    
    # Load configuration
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_file = os.path.join(processed_dir, "cleaned_metrics.json")
    
    # Find all cleaned datasets
    cleaned_datasets = find_cleaned_datasets(processed_dir)
    
    if not cleaned_datasets:
        logger.warning("No cleaned datasets found. Output will be empty.")
        output_data = {
            "status": "success",
            "total_datasets_analyzed": 0,
            "total_datasets_attempted": 0,
            "generated_at": datetime.now().isoformat(),
            "datasets": []
        }
        save_json_file(output_file, output_data)
        logger.info(f"Wrote empty results to {output_file}")
        return 0
    
    # Analyze each cleaned variant
    results = []
    for dataset_info in cleaned_datasets:
        result = analyze_cleaned_variant(dataset_info, config)
        if result:
            results.append(result)
    
    # Compile output
    output_data = {
        "status": "success",
        "total_datasets_analyzed": len(results),
        "total_datasets_attempted": len(cleaned_datasets),
        "generated_at": datetime.now().isoformat(),
        "datasets": results
    }
    
    # Write output
    save_json_file(output_file, output_data)
    logger.info(f"Wrote results to {output_file}")
    logger.info(f"Successfully analyzed {len(results)} out of {len(cleaned_datasets)} datasets")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
