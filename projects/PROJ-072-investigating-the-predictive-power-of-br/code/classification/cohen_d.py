import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from classification.validation import run_validation_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d effect size for the difference between two groups.
    
    Parameters:
        group1: Array of values for group 1 (e.g., Controls)
        group2: Array of values for group 2 (e.g., Schizophrenia)
        
    Returns:
        Tuple of (cohen_d, pooled_std, mean_diff)
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Returning 0 for Cohen's d.")
        return 0.0, 0.0, mean2 - mean1
    
    cohen_d = (mean2 - mean1) / pooled_std
    return cohen_d, pooled_std, mean2 - mean1

def calculate_cohen_d_for_all_features(features_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cohen's d for every feature column, stratified by diagnosis label.
    
    Parameters:
        features_df: DataFrame containing feature vectors (rows=subjects, cols=features)
        labels_df: DataFrame with 'subject_id' and 'diagnosis' columns
        
    Returns:
        DataFrame with feature names and their corresponding Cohen's d, mean_diff, and pooled_std.
    """
    # Merge features and labels on subject_id
    merged = features_df.merge(labels_df, on='subject_id', how='inner')
    
    if 'diagnosis' not in merged.columns:
        raise ValueError("Labels DataFrame must contain a 'diagnosis' column.")
    
    # Identify groups (assuming binary classification for this analysis)
    unique_labels = merged['diagnosis'].unique()
    if len(unique_labels) != 2:
        logger.warning(f"Expected 2 groups for Cohen's d, found {len(unique_labels)}. Proceeding with available groups.")
    
    group_labels = list(unique_labels)
    group1_label, group2_label = group_labels[0], group_labels[1]
    
    group1_mask = merged['diagnosis'] == group1_label
    group2_mask = merged['diagnosis'] == group2_label
    
    feature_cols = [col for col in features_df.columns if col != 'subject_id']
    
    results = []
    for col in feature_cols:
        g1_vals = merged.loc[group1_mask, col].values
        g2_vals = merged.loc[group2_mask, col].values
        
        if len(g1_vals) == 0 or len(g2_vals) == 0:
            logger.warning(f"Skipping {col}: one group is empty.")
            continue
        
        d, std, diff = calculate_cohen_d(g1_vals, g2_vals)
        results.append({
            'feature': col,
            'cohen_d': d,
            'pooled_std': std,
            'mean_diff': diff,
            'group1_mean': np.mean(g1_vals),
            'group2_mean': np.mean(g2_vals),
            'group1_n': len(g1_vals),
            'group2_n': len(g2_vals)
        })
    
    return pd.DataFrame(results)

def run_cohen_d_pipeline(output_path: str = None) -> pd.DataFrame:
    """
    Main pipeline to load features and labels, compute Cohen's d, and save results.
    
    Parameters:
        output_path: Path to save the results CSV. Defaults to data/processed/cohen_d_results.csv
        
    Returns:
        DataFrame of Cohen's d results.
    """
    if output_path is None:
        output_path = str(project_root / 'data' / 'processed' / 'cohen_d_results.csv')
    
    logger.info(f"Loading features from {project_root / 'data' / 'processed' / 'features.csv'}")
    features_path = project_root / 'data' / 'processed' / 'features.csv'
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}. Run feature extraction first.")
    
    features_df = pd.read_csv(features_path)
    
    logger.info(f"Loading labels from {project_root / 'data' / 'metadata' / 'subject_labels.csv'}")
    labels_path = project_root / 'data' / 'metadata' / 'subject_labels.csv'
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found at {labels_path}. Run metadata generation first.")
    
    labels_df = pd.read_csv(labels_path)
    
    logger.info("Calculating Cohen's d for all features...")
    results_df = calculate_cohen_d_for_all_features(features_df, labels_df)
    
    # Sort by absolute Cohen's d descending
    results_df = results_df.sort_values(by='cohen_d', key=lambda x: x.abs(), ascending=False)
    
    logger.info(f"Saving Cohen's d results to {output_path}")
    results_df.to_csv(output_path, index=False)
    
    return results_df

def main():
    """Entry point for the script."""
    try:
        results = run_cohen_d_pipeline()
        logger.info(f"Pipeline completed. Results saved. Top 5 features by effect size:\n{results.head()}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
