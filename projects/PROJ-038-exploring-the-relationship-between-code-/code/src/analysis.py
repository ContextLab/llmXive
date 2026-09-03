import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
import numpy as np
from scipy.stats import pointbiserialr, spearmanr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_features_csv(file_path: str) -> pd.DataFrame:
    """
    Load the features CSV file.
    
    Args:
        file_path: Path to the features.csv file.
        
    Returns:
        DataFrame containing the features.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    required_columns = {'file_path', 'cc', 'halstead', 'loc', 'is_buggy'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    logger.info(f"Loaded features from {file_path} with shape {df.shape}")
    return df

def compute_point_biserial(df: pd.DataFrame, metric: str, target: str = 'is_buggy') -> Tuple[float, float]:
    """
    Compute the Point-Biserial correlation coefficient and p-value between a metric and the binary target.
    
    Args:
        df: DataFrame containing the data.
        metric: Name of the metric column.
        target: Name of the binary target column.
        
    Returns:
        Tuple of (correlation coefficient, p-value).
        
    Raises:
        ValueError: If the target column is not binary or metric is missing.
    """
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in DataFrame")
    if target not in df.columns:
        raise ValueError(f"Target '{target}' not found in DataFrame")
    
    # Drop rows with NaN in the metric or target
    valid_data = df[[metric, target]].dropna()
    
    if len(valid_data) == 0:
        logger.warning(f"No valid data for metric '{metric}' and target '{target}'")
        return 0.0, 1.0
    
    # Check if target is binary
    unique_targets = valid_data[target].unique()
    if len(unique_targets) != 2:
        raise ValueError(f"Target column '{target}' must be binary (0 and 1), found: {unique_targets}")
    
    # Compute Point-Biserial correlation
    r_pb, p_val = pointbiserialr(valid_data[target], valid_data[metric])
    
    logger.info(f"Point-Biserial correlation for '{metric}': r={r_pb:.4f}, p={p_val:.4f}")
    return r_pb, p_val

def compute_spearman(df: pd.DataFrame, metric: str, target: str = 'is_buggy') -> Tuple[float, float]:
    """
    Compute the Spearman rank correlation coefficient and p-value between a metric and the target.
    
    Args:
        df: DataFrame containing the data.
        metric: Name of the metric column.
        target: Name of the target column.
        
    Returns:
        Tuple of (correlation coefficient, p-value).
        
    Raises:
        ValueError: If the metric or target is missing.
    """
    if metric not in df.columns:
        raise ValueError(f"Metric '{metric}' not found in DataFrame")
    if target not in df.columns:
        raise ValueError(f"Target '{target}' not found in DataFrame")
    
    # Drop rows with NaN in the metric or target
    valid_data = df[[metric, target]].dropna()
    
    if len(valid_data) == 0:
        logger.warning(f"No valid data for metric '{metric}' and target '{target}'")
        return 0.0, 1.0
    
    # Compute Spearman correlation
    rho, p_val = spearmanr(valid_data[metric], valid_data[target])
    
    logger.info(f"Spearman correlation for '{metric}': rho={rho:.4f}, p={p_val:.4f}")
    return rho, p_val

def run_correlation_analysis(df: pd.DataFrame, metrics: Optional[List[str]] = None, target: str = 'is_buggy') -> List[Dict[str, Any]]:
    """
    Run correlation analysis for all specified metrics against the target.
    
    Args:
        df: DataFrame containing the data.
        metrics: List of metric column names to analyze. If None, uses ['cc', 'halstead', 'loc'].
        target: Name of the target column.
        
    Returns:
        List of dictionaries containing correlation results for each metric.
    """
    if metrics is None:
        metrics = ['cc', 'halstead', 'loc']
    
    results = []
    for metric in metrics:
        try:
            pb_r, pb_p = compute_point_biserial(df, metric, target)
            sp_r, sp_p = compute_spearman(df, metric, target)
            
            results.append({
                'metric': metric,
                'point_biserial_r': float(pb_r),
                'point_biserial_p': float(pb_p),
                'spearman_rho': float(sp_r),
                'spearman_p': float(sp_p)
            })
        except Exception as e:
            logger.error(f"Error computing correlations for metric '{metric}': {e}")
            # Continue with other metrics
            continue
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save correlation results to a JSON file.
    
    Args:
        results: List of correlation result dictionaries.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved correlation results to {output_path}")

def main():
    """
    Main function to run the correlation analysis.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    features_path = project_root / 'code' / 'data' / 'processed' / 'features.csv'
    output_path = project_root / 'code' / 'data' / 'results' / 'correlation_report.json'
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Features file: {features_path}")
    logger.info(f"Output file: {output_path}")
    
    # Load features
    try:
        df = load_features_csv(str(features_path))
    except Exception as e:
        logger.error(f"Failed to load features: {e}")
        return
    
    # Run correlation analysis
    results = run_correlation_analysis(df)
    
    if not results:
        logger.warning("No correlation results generated.")
        return
    
    # Save results
    save_results(results, str(output_path))
    
    logger.info("Correlation analysis completed successfully.")

if __name__ == '__main__':
    main()