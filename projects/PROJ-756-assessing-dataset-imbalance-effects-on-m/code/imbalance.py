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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/imbalance.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """Load the processed descriptors parquet file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")
    return df

def identify_target_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns that are likely target properties (numeric, not descriptors)."""
    # Heuristic: exclude known descriptor prefixes or specific columns
    exclude_cols = {'composition', 'material_id', 'entry_id', 'formula'}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter out non-property columns if we know them
    # Assuming descriptors are computed and stored, we look for remaining numeric cols
    # that aren't the index or known metadata.
    target_cols = [col for col in numeric_cols if col not in exclude_cols]
    return target_cols

def calculate_gini(values: np.ndarray) -> float:
    """
    Calculate the Gini coefficient for a 1D array of values.
    Handles negative values by shifting them to be non-negative.
    """
    if len(values) == 0:
        return 0.0
    
    # Ensure non-negative for Gini calculation
    # If values are negative, shift by absolute min
    if np.any(values < 0):
        min_val = np.min(values)
        values = values - min_val + 1e-6  # Ensure strictly positive if min was 0
    
    # Gini calculation
    sorted_values = np.sort(values)
    n = len(sorted_values)
    cumsum = np.cumsum(sorted_values)
    
    gini = (2 * np.sum((np.arange(1, n + 1) * sorted_values))) / (n * np.sum(sorted_values)) - (n + 1) / n
    return float(gini)

def calculate_target_imbalance_score(df: pd.DataFrame, target_cols: List[str], min_samples: int = 100) -> Dict[str, float]:
    """
    Calculate Gini coefficient of target property values for properties with >= min_samples.
    """
    scores = {}
    for col in target_cols:
        data = df[col].dropna().values
        if len(data) < min_samples:
            logger.info(f"Skipping {col}: only {len(data)} samples (min={min_samples})")
            continue
        scores[col] = calculate_gini(data)
        logger.info(f"Target Imbalance Score for {col}: {scores[col]:.4f}")
    return scores

def calculate_compositional_imbalance_score(df: pd.DataFrame, n_clusters: int = 50) -> Dict[str, float]:
    """
    Calculate Compositional Imbalance Score:
    1. Perform K-Means clustering (k=50) on compositional features.
    2. Calculate Gini coefficient of the frequency of samples assigned to each cluster.
    
    Args:
        df: DataFrame containing compositional descriptors.
        n_clusters: Number of clusters for K-Means.
    
    Returns:
        Dict with a single key 'compositional_imbalance_score' and the calculated Gini value.
    """
    # Select numeric columns for clustering (excluding metadata)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = {'composition', 'material_id', 'entry_id', 'formula'}
    feature_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if not feature_cols:
        raise ValueError("No numeric feature columns found for clustering.")
    
    logger.info(f"Using {len(feature_cols)} feature columns for K-Means clustering: {feature_cols[:5]}...")
    
    X = df[feature_cols].values
    
    # Handle potential NaN/Inf
    if np.any(np.isnan(X)) or np.any(np.isinf(X)):
        logger.warning("NaN or Inf values detected. Filling NaN with 0 and clipping Inf.")
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
    
    logger.info(f"Running K-Means clustering with k={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    cluster_labels = kmeans.fit_predict(X)
    
    # Count samples per cluster
    unique, counts = np.unique(cluster_labels, return_counts=True)
    logger.info(f"Cluster distribution: {dict(zip(unique, counts))}")
    
    # Calculate Gini of the counts
    # If all samples fall into one cluster, Gini is high.
    # If evenly distributed, Gini is low.
    gini_score = calculate_gini(counts)
    
    logger.info(f"Compositional Imbalance Score (Gini of cluster counts): {gini_score:.4f}")
    return {"compositional_imbalance_score": gini_score}

def analyze_all_properties(df: pd.DataFrame, min_samples: int = 100, n_clusters: int = 50) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Analyze both target and compositional imbalance.
    """
    target_cols = identify_target_columns(df)
    logger.info(f"Identified {len(target_cols)} potential target columns.")
    
    target_scores = calculate_target_imbalance_score(df, target_cols, min_samples)
    compositional_scores = calculate_compositional_imbalance_score(df, n_clusters)
    
    return target_scores, compositional_scores

def save_results(target_scores: Dict[str, float], compositional_scores: Dict[str, float], output_path: str):
    """
    Save the compositional imbalance score to a CSV file.
    Format: property, score_type, score_value
    """
    results = []
    
    # Save target scores
    for prop, score in target_scores.items():
        results.append({"property": prop, "score_type": "target", "score_value": score})
    
    # Save compositional score
    for prop, score in compositional_scores.items():
        results.append({"property": "compositional", "score_type": "compositional", "score_value": score})
    
    df_results = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved imbalance scores to {output_path}")

def main():
    """Main entry point for T008b."""
    input_path = "data/processed/descriptors.parquet"
    output_path = "results/compositional_imbalance_score.csv"
    
    logger.info("Starting Compositional Imbalance Score Calculation (T008b)")
    
    try:
        df = load_data(input_path)
        target_scores, compositional_scores = analyze_all_properties(df)
        save_results(target_scores, compositional_scores, output_path)
        logger.info("T008b completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Input data missing: {e}")
        logger.error("Ensure T007 (Descriptors) and T006 (Data Fetch) have completed successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during imbalance calculation: {e}")
        raise

if __name__ == "__main__":
    main()
