import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.cluster import KMeans

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """
    Load the processed descriptors dataset.
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def identify_target_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify target property columns.
    Heuristic: Columns starting with 'target_' or 'formation_energy', 'band_gap', etc.
    Adjust based on actual schema if needed, but for now we assume standard naming.
    """
    # Filter out descriptor columns (usually numeric features) and non-targets
    # We look for columns that are likely target properties based on common naming
    potential_targets = [
        'formation_energy_per_atom', 'band_gap', 'e_hull', 
        'target_energy', 'target_gap'
    ]
    
    # If specific naming convention 'target_*' is used
    target_cols = [col for col in df.columns if col.startswith('target_')]
    
    # Add common physical properties if they exist and aren't descriptors
    for col in potential_targets:
        if col in df.columns and col not in target_cols:
            target_cols.append(col)
    
    # Remove any columns that look like metadata (id, formula, etc.)
    # Assuming descriptors are numeric and targets are numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Filter out known non-target numeric columns if any (e.g., cluster_id if added)
    
    logger.info(f"Identified target columns: {target_cols}")
    return target_cols

def calculate_gini(values: np.ndarray) -> float:
    """
    Calculate the Gini coefficient for an array of values.
    Handles negative values by taking absolute value or offset if necessary,
    but Gini is typically defined for non-negative values.
    """
    if len(values) == 0:
        return 0.0
    
    # Ensure non-negative for Gini calculation
    # If values are counts, they should be non-negative.
    # If they are properties, we might need absolute or offset.
    # For cluster counts, they are non-negative integers.
    x = np.array(values)
    if np.any(x < 0):
        logger.warning("Negative values detected in Gini calculation. Using absolute values.")
        x = np.abs(x)
    
    # Sort the values
    x = np.sort(x)
    n = len(x)
    
    # Calculate the Gini coefficient
    # G = (2 * sum(i * x_i) - (n + 1) * sum(x_i)) / (n * sum(x_i))
    # Or using the formula: G = 1 - (2 / (n + 1)) * (sum((n - i + 1) * x_i) / sum(x_i))
    # Standard formula for non-negative sorted data:
    # G = (2 * sum_{i=1}^n i * x_i) / (n * sum_{i=1}^n x_i) - (n + 1) / n
    
    if np.sum(x) == 0:
        return 0.0
    
    cumsum = np.cumsum(x)
    gini = (2.0 * np.sum((np.arange(1, n + 1) * x))) / (n * np.sum(x)) - (n + 1) / n
    
    return float(gini)

def calculate_target_imbalance_score(df: pd.DataFrame, target_cols: List[str]) -> Dict[str, float]:
    """
    Calculate the Gini coefficient for each target property.
    Skip properties with < 100 samples.
    """
    scores = {}
    for col in target_cols:
        if col not in df.columns:
            continue
        
        # Drop NaNs
        values = df[col].dropna().values
        
        if len(values) < 100:
            logger.info(f"Skipping {col}: only {len(values)} samples (< 100)")
            continue
        
        # Gini is typically for non-negative. If property can be negative, we might need to adjust.
        # However, for imbalance in distribution, absolute values or a shift might be needed.
        # The task says "handling negative values via absolute transformation or offset".
        # Let's use absolute value if there are negatives, otherwise raw.
        if np.any(values < 0):
            values = np.abs(values)
        
        score = calculate_gini(values)
        scores[col] = score
        logger.info(f"Target Imbalance Score for {col}: {score:.4f}")
    
    return scores

def calculate_compositional_imbalance_score(df: pd.DataFrame, k: int = 50) -> float:
    """
    Calculate the Compositional Imbalance Score.
    1. Perform K-Means clustering (k=50) on compositional features.
    2. Calculate Gini coefficient of the frequency of samples assigned to each cluster.
    
    Args:
        df: DataFrame with compositional descriptors.
        k: Number of clusters.
        
    Returns:
        Gini coefficient of cluster assignment counts.
    """
    # Select feature columns (exclude target columns and metadata)
    # Assume all numeric columns except targets are descriptors
    target_cols = identify_target_columns(df)
    feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                   if col not in target_cols]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found for K-Means clustering.")
    
    logger.info(f"Using {len(feature_cols)} feature columns for clustering: {feature_cols[:5]}...")
    
    X = df[feature_cols].values
    
    # Handle potential NaNs in features
    if np.any(np.isnan(X)):
        logger.warning("NaN values found in features. Dropping rows with NaNs.")
        valid_mask = ~np.isnan(X).any(axis=1)
        X = X[valid_mask]
        if len(X) < k:
            raise ValueError(f"Not enough valid samples ({len(X)}) for K-Means with k={k}.")
    
    # Perform K-Means clustering
    logger.info(f"Running K-Means clustering with k={k}...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    
    # Calculate frequency of samples in each cluster
    unique, counts = np.unique(cluster_labels, return_counts=True)
    
    # Ensure we have counts for all k clusters (some might be empty if k > unique)
    # But KMeans usually assigns all points, so unique should be <= k.
    # We need the distribution of counts across the k clusters.
    # If some clusters are empty, their count is 0.
    cluster_counts = np.zeros(k, dtype=int)
    for label, count in zip(unique, counts):
        cluster_counts[label] = count
    
    # Calculate Gini coefficient of the cluster counts
    score = calculate_gini(cluster_counts)
    logger.info(f"Compositional Imbalance Score (Gini of cluster counts): {score:.4f}")
    
    return score

def analyze_all_properties(df: pd.DataFrame) -> Tuple[Dict[str, float], float]:
    """
    Analyze all target properties and compositional imbalance.
    
    Returns:
        Tuple of (target_scores_dict, compositional_score_float)
    """
    target_cols = identify_target_columns(df)
    target_scores = calculate_target_imbalance_score(df, target_cols)
    compositional_score = calculate_compositional_imbalance_score(df, k=50)
    
    return target_scores, compositional_score

def save_results(target_scores: Dict[str, float], compositional_score: float, output_path: str):
    """
    Save the imbalance scores to CSV.
    
    Args:
        target_scores: Dict of target property names to scores.
        compositional_score: The compositional imbalance score.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a DataFrame for the results
    results_data = []
    
    # Add target scores
    for prop, score in target_scores.items():
        results_data.append({
            'score_type': 'target_imbalance',
            'property': prop,
            'score': score
        })
    
    # Add compositional score
    results_data.append({
        'score_type': 'compositional_imbalance',
        'property': 'all_features',
        'score': compositional_score
    })
    
    df_results = pd.DataFrame(results_data)
    df_results.to_csv(path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for T008b: Compositional Imbalance Score calculation.
    Loads data from data/processed/descriptors.parquet and outputs to results/compositional_imbalance_score.csv.
    """
    # Define paths
    input_path = "data/processed/descriptors.parquet"
    output_path = "results/compositional_imbalance_score.csv"
    
    # Check if input exists
    if not Path(input_path).exists():
        logger.error(f"Input file {input_path} not found. Cannot proceed.")
        sys.exit(1)
    
    try:
        # Load data
        df = load_data(input_path)
        
        # Analyze
        target_scores, compositional_score = analyze_all_properties(df)
        
        # Save results
        save_results(target_scores, compositional_score, output_path)
        
        logger.info("Task T008b completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T008b execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()