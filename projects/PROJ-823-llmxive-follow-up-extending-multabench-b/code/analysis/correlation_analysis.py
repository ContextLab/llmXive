import os
import sys
import json
import csv
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple, List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def load_correlation_data(
    recovery_ratio_path: Path,
    metadata_stats_path: Path
) -> pd.DataFrame:
    """
    Load Recovery Ratio and Metadata Stats, merge them, and filter for complete data.
    
    Args:
        recovery_ratio_path: Path to the JSON containing recovery ratios (from T031)
        metadata_stats_path: Path to the metadata stats CSV (from T024)
        
    Returns:
        DataFrame with merged data for datasets having both metrics and metadata.
    """
    log_info(logger, f"Loading recovery ratios from {recovery_ratio_path}")
    if not recovery_ratio_path.exists():
        raise FileNotFoundError(f"Recovery ratio file not found: {recovery_ratio_path}")
        
    with open(recovery_ratio_path, 'r') as f:
        recovery_data = json.load(f)
    
    # Convert recovery data to DataFrame
    # Expected structure: {"metrics": [{"dataset_id": "...", "recovery_ratio": float, ...}]}
    # Adjust based on actual T031 output structure if different
    if "metrics" in recovery_data:
        df_recovery = pd.DataFrame(recovery_data["metrics"])
    else:
        # Fallback: assume top-level list or dict
        df_recovery = pd.DataFrame(recovery_data)
        
    log_info(logger, f"Loading metadata stats from {metadata_stats_path}")
    if not metadata_stats_path.exists():
        raise FileNotFoundError(f"Metadata stats file not found: {metadata_stats_path}")
        
    df_metadata = pd.read_csv(metadata_stats_path)
    
    # Merge on dataset_id
    # Ensure column names match
    if "dataset_id" not in df_recovery.columns:
        raise ValueError("Recovery ratio data must contain 'dataset_id' column")
    if "dataset_id" not in df_metadata.columns:
        raise ValueError("Metadata stats must contain 'dataset_id' column")
        
    merged_df = pd.merge(
        df_recovery,
        df_metadata,
        on="dataset_id",
        how="inner"
    )
    
    # Filter for complete data (no NaN in key columns)
    key_cols = ["recovery_ratio", "cardinality", "missingness", "sparsity", "variance"]
    # Handle case where columns might have different names or types
    available_cols = [c for c in key_cols if c in merged_df.columns]
    
    if len(available_cols) < 2:
        raise ValueError(f"Missing required columns for correlation. Available: {merged_df.columns.tolist()}")
        
    merged_df = merged_df.dropna(subset=available_cols)
    
    log_info(logger, f"Merged dataset size: {len(merged_df)} rows with complete data")
    return merged_df

def calculate_pearson_correlations(
    df: pd.DataFrame,
    target_col: str = "recovery_ratio",
    feature_cols: List[str] = ["cardinality", "missingness", "sparsity", "variance"]
) -> List[Dict[str, Any]]:
    """
    Calculate Pearson correlation between target and each feature.
    
    Args:
        df: DataFrame with merged data
        target_col: Name of the target column (Recovery Ratio)
        feature_cols: List of metadata feature columns to correlate
        
    Returns:
        List of dicts containing correlation stats for each feature
    """
    results = []
    
    for feature in feature_cols:
        if feature not in df.columns:
            log_warning(logger, f"Feature column '{feature}' not found in data, skipping.")
            continue
            
        if df[target_col].nunique() < 2 or df[feature].nunique() < 2:
            log_warning(logger, f"Insufficient variance in '{target_col}' or '{feature}', skipping.")
            continue
            
        try:
            corr, p_value = stats.pearsonr(df[target_col], df[feature])
            
            results.append({
                "feature": feature,
                "correlation_coefficient": float(corr),
                "p_value": float(p_value),
                "sample_size": int(len(df)),
                "method": "pearson"
            })
            log_info(logger, f"Pearson r={corr:.4f}, p={p_value:.4f} for {feature}")
            
        except Exception as e:
            log_error(logger, f"Error calculating correlation for {feature}: {e}")
            
    return results

def save_correlation_results(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save correlation results to a JSON file.
    
    Args:
        results: List of correlation result dicts
        output_path: Path to save the JSON file
    """
    ensure_directories([output_path.parent])
    
    output_data = {
        "analysis_type": "pearson_correlation",
        "target_variable": "recovery_ratio",
        "timestamp": pd.Timestamp.now().isoformat(),
        "correlations": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    log_info(logger, f"Saved correlation results to {output_path}")

def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main entry point for T033: Pearson Correlation Analysis.
    """
    parser = argparse.ArgumentParser(description="Perform Pearson correlation between Recovery Ratio and metadata features.")
    parser.add_argument(
        "--recovery-ratio-path",
        type=str,
        default="data/artifacts/recovery_ratio_metrics.json",
        help="Path to the recovery ratio metrics JSON file (output of T031)"
    )
    parser.add_argument(
        "--metadata-stats-path",
        type=str,
        default="data/processed/metadata_stats_summary.csv",
        help="Path to the metadata stats CSV file (output of T024)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/artifacts/correlation_results_t033.json",
        help="Path to save the correlation results JSON"
    )
    
    if args is None:
        args = parser.parse_args()
        
    log_info(logger, "Starting T033: Pearson Correlation Analysis")
    
    try:
        # Load and merge data
        df = load_correlation_data(
            Path(args.recovery_ratio_path),
            Path(args.metadata_stats_path)
        )
        
        if df.empty:
            log_error(logger, "No valid data found for correlation analysis.")
            return 1
            
        # Calculate correlations
        results = calculate_pearson_correlations(df)
        
        if not results:
            log_warning(logger, "No correlations could be calculated.")
            
        # Save results
        save_correlation_results(results, Path(args.output_path))
        
        log_info(logger, "T033 completed successfully.")
        return 0
        
    except Exception as e:
        log_error(logger, f"Error during T033 execution: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
