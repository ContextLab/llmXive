import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs(base_dir: str = "data"):
    """Ensure required directories exist."""
    Path(base_dir, "results").mkdir(parents=True, exist_ok=True)

def load_test_data(data_path: str) -> pd.DataFrame:
    """Load the preprocessed test data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Test data not found at {data_path}")
    return pd.read_csv(data_path)

def calculate_p_values(
    model: Any,
    X: pd.DataFrame,
    y: np.ndarray,
    cluster_ids: pd.Series,
    feature_name: str,
    n_permutations: int = 100
) -> float:
    """
    Calculate p-value for a single feature using cluster-aware permutation.
    
    Logic:
    1. Calculate original model performance (R2).
    2. For each permutation:
       a. Shuffle the feature values ONLY within each cluster (adsorbent_structure_id).
       b. Calculate performance on permuted data.
       c. Record the drop in performance (or the permuted score).
    3. The p-value is the proportion of permuted scores that are <= original score
       (if we are measuring performance drop, then we count how many permuted scores are >= original? 
        Actually, we want to see if the drop is significant. 
        Null hypothesis: feature has no importance. Permuting it should not change performance much.
        If the feature is important, permuting it will cause a large drop.
        So we count how many permuted drops are >= observed drop.
        Or, equivalently, how many permuted scores are <= observed score.
        Let's use the score directly: p = count(permuted_score <= original_score) / n_permutations.
    """
    # Original performance
    original_score = r2_score(y, model.predict(X))
    
    # Prepare permuted scores
    permuted_scores = []
    
    # Get unique clusters
    unique_clusters = cluster_ids.unique()
    
    for _ in range(n_permutations):
        X_perm = X.copy()
        
        # Shuffle within each cluster
        for cluster_id in unique_clusters:
            mask = cluster_ids == cluster_id
            cluster_indices = X_perm.index[mask]
            if len(cluster_indices) > 1:
                # Shuffle the feature values within this cluster
                shuffled_values = X_perm.loc[cluster_indices, feature_name].values.copy()
                np.random.shuffle(shuffled_values)
                X_perm.loc[cluster_indices, feature_name] = shuffled_values
        
        # Calculate performance on permuted data
        permuted_score = r2_score(y, model.predict(X_perm))
        permuted_scores.append(permuted_score)
    
    # Calculate p-value
    # p = proportion of permuted scores <= original score
    p_value = np.sum(np.array(permuted_scores) <= original_score) / n_permutations
    
    return float(p_value)

def run_permutation_analysis(
    model: Any,
    X: pd.DataFrame,
    y: np.ndarray,
    cluster_ids: pd.Series,
    n_permutations: int = 100
) -> Dict[str, float]:
    """
    Run cluster-aware permutation analysis for all features.
    
    Returns:
        Dictionary mapping feature names to raw p-values.
    """
    logger.info(f"Running permutation analysis with {n_permutations} permutations...")
    feature_names = X.columns.tolist()
    p_values = {}
    
    for feat in feature_names:
        logger.info(f"Calculating p-value for feature: {feat}")
        p_val = calculate_p_values(
            model=model,
            X=X,
            y=y,
            cluster_ids=cluster_ids,
            feature_name=feat,
            n_permutations=n_permutations
        )
        p_values[feat] = p_val
    
    return p_values

def run_cluster_permutation(
    model: Any,
    X: pd.DataFrame,
    y: np.ndarray,
    cluster_ids: pd.Series,
    n_permutations: int = 100
) -> Dict[str, float]:
    """
    Wrapper function to run cluster permutation analysis.
    This is the function called by T052 (evaluate.py).
    """
    return run_permutation_analysis(model, X, y, cluster_ids, n_permutations)

def main():
    """Entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run cluster permutation analysis.")
    parser.add_argument("--data-path", type=str, required=True, help="Path to test data CSV.")
    parser.add_argument("--model-path", type=str, required=True, help="Path to trained model pickle.")
    parser.add_argument("--output-path", type=str, default="data/results/permutation_pvalues.json", help="Output JSON path.")
    parser.add_argument("--n-permutations", type=int, default=100, help="Number of permutations.")
    parser.add_argument("--cluster-col", type=str, default="adsorbent_structure_id", help="Column name for cluster IDs.")
    parser.add_argument("--target-col", type=str, default="langmuir_capacity", help="Column name for target.")
    
    args = parser.parse_args()
    
    # Load data
    df = load_test_data(args.data_path)
    
    # Identify target and cluster columns
    if args.target_col not in df.columns:
        raise ValueError(f"Target column '{args.target_col}' not found in data.")
    if args.cluster_col not in df.columns:
        raise ValueError(f"Cluster column '{args.cluster_col}' not found in data.")
    
    y = df[args.target_col].values
    X = df.drop(columns=[args.target_col, args.cluster_col])
    cluster_ids = df[args.cluster_col]
    
    # Load model
    import pickle
    if not os.path.exists(args.model_path):
        raise FileNotFoundError(f"Model file not found: {args.model_path}")
    with open(args.model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Run analysis
    p_values = run_cluster_permutation(model, X, y, cluster_ids, args.n_permutations)
    
    # Save results
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    with open(args.output_path, 'w') as f:
        json.dump(p_values, f, indent=2)
    
    print(f"Permutation p-values saved to {args.output_path}")

if __name__ == "__main__":
    main()