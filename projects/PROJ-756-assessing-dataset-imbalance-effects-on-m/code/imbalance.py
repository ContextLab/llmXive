import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a parquet file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    try:
        df = pd.read_parquet(file_path)
        logger.info(f"Loaded data from {file_path}: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data from {file_path}: {e}")
        raise

def identify_target_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify target property columns in the dataframe.
    Heuristic: Look for columns that are numeric and likely represent properties.
    In a real scenario, this might be defined by a schema or config.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Filter out common feature columns if known, or just assume all numeric are targets for this step
    # Based on context, we assume the merged dataset has specific target columns.
    # For robustness, we'll filter out 'composition' if it exists as a string/object column.
    potential_targets = [col for col in numeric_cols if col not in ['composition_id', 'material_id', 'element_counts']]
    logger.info(f"Identified potential target columns: {potential_targets}")
    return potential_targets

def calculate_gini(values: pd.Series) -> float:
    """
    Calculate the Gini coefficient for a series of values.
    Handles negative values by taking absolute values or shifting.
    The Gini coefficient is defined for non-negative values.
    """
    if len(values) == 0:
        return 0.0
    
    # Handle negative values: shift to make all non-negative if necessary
    # Or take absolute value if the distribution shape is what matters.
    # Standard Gini requires non-negative. We'll shift by min if min < 0.
    vals = values.values
    if np.min(vals) < 0:
        vals = vals - np.min(vals) + 1e-9 # Ensure strictly positive if min is 0 after shift
    
    # Gini calculation: 2 * A / (n * sum(y)) - (n+1)/n
    # Where A is the area under the Lorenz curve.
    # Formula: G = (2 * sum(i * y_i) / (n * sum(y_i))) - (n + 1) / n
    # Sort values
    sorted_vals = np.sort(vals)
    n = len(sorted_vals)
    if np.sum(sorted_vals) == 0:
        return 0.0
    
    x = np.arange(1, n + 1)
    gini = (2 * np.sum(x * sorted_vals)) / (n * np.sum(sorted_vals)) - (n + 1) / n
    return float(gini)

def calculate_target_imbalance(df: pd.DataFrame, target_col: str) -> float:
    """
    Calculate Target Imbalance Score (Gini coefficient) for a specific target property.
    Skips properties with < 100 samples.
    """
    if target_col not in df.columns:
        logger.warning(f"Target column {target_col} not found in dataframe.")
        return np.nan
    
    values = df[target_col].dropna()
    if len(values) < 100:
        logger.info(f"Skipping {target_col}: only {len(values)} samples (need >= 100).")
        return np.nan
    
    return calculate_gini(values)

def calculate_target_imbalance_score(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Target Imbalance Score for all valid target columns.
    Returns a dictionary mapping column name to Gini score.
    """
    targets = identify_target_columns(df)
    scores = {}
    for target in targets:
        score = calculate_target_imbalance(df, target)
        scores[target] = score
        logger.info(f"Target Imbalance Score for {target}: {score:.4f}")
    return scores

def calculate_compositional_imbalance_score(df: pd.DataFrame, n_clusters: int = 50) -> float:
    """
    Calculate Compositional Imbalance Score.
    1. Perform K-Means clustering (k=50) on compositional features.
    2. Calculate Gini coefficient of the frequency of samples assigned to each cluster.
    """
    # Identify compositional features (exclude target columns and IDs)
    targets = identify_target_columns(df)
    # Assume compositional features are all numeric columns excluding targets and known IDs
    exclude_cols = set(targets + ['composition', 'material_id', 'composition_id'])
    feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col not in exclude_cols]
    
    if len(feature_cols) == 0:
        logger.warning("No compositional features found for clustering.")
        return np.nan
    
    X = df[feature_cols].dropna()
    if len(X) < n_clusters:
        logger.warning(f"Not enough samples ({len(X)}) for {n_clusters} clusters.")
        return np.nan
    
    from sklearn.cluster import KMeans
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    # Fit on the data, handling any remaining NaNs by dropping or imputing if necessary
    # For simplicity, we drop rows with NaNs in features for this step
    X_clean = X.dropna()
    if len(X_clean) < n_clusters:
        logger.warning(f"After dropping NaNs, too few samples ({len(X_clean)}) for clustering.")
        return np.nan
    
    labels = kmeans.fit_predict(X_clean)
    
    # Count frequency of each cluster
    unique, counts = np.unique(labels, return_counts=True)
    cluster_counts = pd.Series(counts)
    
    # Calculate Gini of cluster counts
    return calculate_gini(cluster_counts)

def analyze_all_properties(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze all properties for imbalance.
    Returns a dictionary with target and compositional imbalance scores.
    """
    target_scores = calculate_target_imbalance_score(df)
    compositional_score = calculate_compositional_imbalance_score(df)
    
    return {
        "target_imbalance_scores": target_scores,
        "compositional_imbalance_score": compositional_score
    }

def save_results(results: Dict[str, Any], output_path: str):
    """
    Save imbalance scores to a CSV file.
    Expected output format for target_imbalance_scores: property, score
    """
    target_scores = results.get("target_imbalance_scores", {})
    
    if not target_scores:
        logger.warning("No target imbalance scores to save.")
        return
    
    # Convert to DataFrame
    data = []
    for prop, score in target_scores.items():
        data.append({"property": prop, "score": score})
    
    df_out = pd.DataFrame(data)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_out.to_csv(output_path, index=False)
    logger.info(f"Saved target imbalance scores to {output_path}")

def main():
    """
    Main entry point for calculating target imbalance.
    Loads preprocessed data, calculates scores, and saves to results/target_imbalance_scores.csv.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "processed" / "descriptors.parquet"
    output_path = project_root / "results" / "target_imbalance_scores.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load data
    try:
        df = load_data(str(input_path))
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        sys.exit(1)
    
    # Calculate scores
    results = analyze_all_properties(df)
    
    # Save results
    save_results(results, str(output_path))
    
    logger.info("Target imbalance calculation completed.")

if __name__ == "__main__":
    main()