"""
Stratified Analysis by Alloy Type (US2 - T029)

Performs confounder sensitivity analysis by grouping processed data by 'alloy_type',
calculating descriptive statistics for mechanical properties within each group,
and assessing variance heterogeneity. This task consumes the processed CSV from
T014/T015A and does NOT require the trained GPR model.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

# Import path utilities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import (
    get_processed_data_dir,
    get_results_dir,
    ensure_directories,
    get_logger
)
from utils.logger import setup_logging

# Constants
PROCESSED_CSV_FILENAME = "processed_data.csv"
STRATIFIED_RESULTS_FILENAME = "stratified_analysis.json"
LOG_FILENAME = "stratified_analysis.log"

def load_processed_data(filepath: str) -> pd.DataFrame:
    """
    Load the preprocessed CSV file.
    
    Args:
        filepath: Path to the processed CSV.
        
    Returns:
        DataFrame with preprocessed data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Identify target columns (mechanical properties)
    # Based on schema: yield_strength, ductility, (optional fatigue_life)
    target_cols = [col for col in ['yield_strength', 'ductility', 'fatigue_life'] 
                   if col in df.columns]
    
    if not target_cols:
        raise ValueError("No target mechanical property columns found in processed data.")
    
    if 'alloy_type' not in df.columns:
        raise ValueError("Column 'alloy_type' not found in processed data. "
                         "Ensure one-hot encoding was not applied to drop this column entirely, "
                         "or that a grouping key exists.")
    
    return df, target_cols

def calculate_group_stats(df: pd.DataFrame, group_col: str, target_cols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate descriptive statistics for each group (alloy type).
    
    Args:
        df: DataFrame containing the data.
        group_col: Name of the column to group by (e.g., 'alloy_type').
        target_cols: List of target columns to analyze.
        
    Returns:
        Dictionary with statistics per group.
    """
    stats = {}
    
    groups = df.groupby(group_col)
    
    for name, group in groups:
        group_stats = {
            "count": len(group),
            "properties": {}
        }
        
        for col in target_cols:
            values = group[col].dropna()
            if len(values) > 0:
                group_stats["properties"][col] = {
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "median": float(np.median(values))
                }
            else:
                group_stats["properties"][col] = {
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                    "median": None
                }
        
        stats[str(name)] = group_stats
        
    return stats

def assess_variance_heterogeneity(df: pd.DataFrame, group_col: str, target_cols: List[str]) -> Dict[str, Any]:
    """
    Assess if variance in mechanical properties differs significantly between alloy types.
    Uses Levene's test for equality of variances.
    
    Args:
        df: DataFrame containing the data.
        group_col: Name of the grouping column.
        target_cols: List of target columns to test.
        
    Returns:
        Dictionary with test results.
    """
    results = {}
    groups = df.groupby(group_col)
    group_names = list(groups.groups.keys())
    
    if len(group_names) < 2:
        return {"status": "insufficient_groups", "message": "Need at least 2 groups for variance test"}
    
    try:
        from scipy import stats as scipy_stats
        
        for col in target_cols:
            # Extract arrays for each group
            arrays = [group[col].dropna().values for _, group in groups]
            arrays = [arr for arr in arrays if len(arr) > 0]
            
            if len(arrays) < 2:
                results[col] = {"status": "insufficient_data", "message": "Not enough data points across groups"}
                continue
            
            # Levene's test (robust to non-normality)
            statistic, p_value = scipy_stats.levene(*arrays, center='median')
            
            results[col] = {
                "statistic": float(statistic),
                "p_value": float(p_value),
                "significant": p_value < 0.05,
                "interpretation": "Variance differs significantly" if p_value < 0.05 else "Variances are homogeneous"
            }
            
    except ImportError:
        logging.warning("scipy not available. Skipping variance heterogeneity test.")
        results = {"status": "skipped", "message": "scipy not installed"}
        
    return results

def run_stratified_analysis(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Main function to run the full stratified analysis pipeline.
    
    Args:
        output_dir: Directory to save results. If None, uses default from config.
        
    Returns:
        Dictionary containing the analysis results.
    """
    # Setup logging
    log_dir = os.path.dirname(output_dir) if output_dir else None
    if not log_dir:
        from config import get_logs_dir
        log_dir = get_logs_dir()
    ensure_directories(log_dir)
    
    logger = setup_logging(LOG_FILENAME, log_dir)
    logger.info("Starting Stratified Analysis by Alloy Type (T029)")
    
    # Determine paths
    if output_dir is None:
        processed_dir = get_processed_data_dir()
        results_dir = get_results_dir()
    else:
        processed_dir = os.path.dirname(output_dir)
        results_dir = output_dir
    
    ensure_directories(results_dir)
    
    input_path = os.path.join(processed_dir, PROCESSED_CSV_FILENAME)
    output_path = os.path.join(results_dir, STRATIFIED_RESULTS_FILENAME)
    
    logger.info(f"Loading processed data from: {input_path}")
    
    try:
        df, target_cols = load_processed_data(input_path)
        logger.info(f"Loaded {len(df)} rows. Target columns: {target_cols}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    # Check if we have enough data per group
    group_counts = df['alloy_type'].value_counts()
    logger.info(f"Group counts: {group_counts.to_dict()}")
    
    if group_counts.min() < 5:
        logger.warning("Some groups have fewer than 5 samples. Statistical significance may be limited.")
    
    # Calculate group statistics
    logger.info("Calculating group statistics...")
    group_stats = calculate_group_stats(df, 'alloy_type', target_cols)
    
    # Assess variance heterogeneity
    logger.info("Assessing variance heterogeneity...")
    variance_test_results = assess_variance_heterogeneity(df, 'alloy_type', target_cols)
    
    # Compile results
    analysis_results = {
        "total_samples": len(df),
        "groups_analyzed": list(group_counts.index),
        "group_counts": group_counts.to_dict(),
        "statistics_by_group": group_stats,
        "variance_heterogeneity_test": variance_test_results,
        "conclusion": ""
    }
    
    # Generate conclusion
    if variance_test_results and "status" not in variance_test_results:
        significant_vars = [col for col, res in variance_test_results.items() 
                          if res.get("significant", False)]
        if significant_vars:
            analysis_results["conclusion"] = (
                f"Significant variance heterogeneity found for: {significant_vars}. "
                "This suggests 'alloy_type' is a confounder that affects the spread of mechanical properties."
            )
        else:
            analysis_results["conclusion"] = (
                "No significant variance heterogeneity detected. "
                "The spread of mechanical properties appears consistent across alloy types."
            )
    else:
        analysis_results["conclusion"] = "Variance analysis could not be completed."
    
    # Save results
    logger.info(f"Saving results to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info("Stratified analysis completed successfully.")
    return analysis_results

def main():
    """Entry point for the script."""
    try:
        results = run_stratified_analysis()
        print(json.dumps(results, indent=2))
        sys.exit(0)
    except Exception as e:
        logging.error(f"Stratified analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
