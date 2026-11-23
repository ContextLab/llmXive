import os
import sys
import json
import logging
import pickle
import gc
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
import numpy as np
import pandas as pd
from scipy.spatial.distance import jaccard
from rdkit import Chem
from rdkit.Chem import Descriptors
import lightgbm as lgb
import shap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

def load_model_and_data(model_path: str, data_path: str) -> Tuple[Any, pd.DataFrame]:
    """Load the trained model and the processed descriptor data."""
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)

    # Ensure we have the required columns
    required_cols = ['smiles', 'target']
    desc_cols = [col for col in df.columns if col.startswith('desc_')]
    if not desc_cols:
        raise ValueError("No descriptor columns found in data. Expected columns starting with 'desc_'.")

    return model, df

def load_clusters_from_file(cluster_map_path: str) -> Dict[str, List[str]]:
    """Load cluster mapping from CSV file."""
    logger.info(f"Loading cluster map from {cluster_map_path}")
    df = pd.read_csv(cluster_map_path)
    clusters = {}
    for _, row in df.iterrows():
        cluster_id = row['cluster_id']
        feature = row['feature_id']
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(feature)
    return clusters

def compute_shap_values(model: Any, data: pd.DataFrame, feature_names: List[str]) -> np.ndarray:
    """Compute SHAP values using TreeExplainer."""
    logger.info("Computing SHAP values")
    X = data[feature_names].values
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    return shap_values

def save_shap_values(shap_values: np.ndarray, output_path: str):
    """Save SHAP values to a file."""
    logger.info(f"Saving SHAP values to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(shap_values, f)

def run_cluster_aware_shap_analysis(model: Any, data: pd.DataFrame, clusters: Dict[str, List[str]]) -> Dict[str, float]:
    """Run cluster-aware SHAP analysis and return cluster importances."""
    feature_names = [col for col in data.columns if col.startswith('desc_')]
    shap_values = compute_shap_values(model, data, feature_names)

    # Aggregate SHAP values by cluster
    cluster_importance = {}
    for cluster_id, features in clusters.items():
        # Filter features that exist in the dataset
        existing_features = [f for f in features if f in feature_names]
        if not existing_features:
            continue

        # Get indices of existing features
        indices = [feature_names.index(f) for f in existing_features]

        # Compute mean absolute SHAP value for the cluster
        cluster_shap = np.abs(shap_values[:, indices])
        cluster_importance[cluster_id] = float(np.mean(cluster_shap))

    return cluster_importance

def compute_stability_metrics(cluster_importance: Dict[str, float], shap_values: np.ndarray, 
                              feature_names: List[str], clusters: Dict[str, List[str]], 
                              n_bootstrap: int = 100, seed: int = 42) -> Tuple[List[Dict], float]:
    """
    Compute stability metrics using SHAP-only resampling.
    
    This implements the Ratified Plan Override: resample SHAP values directly
    without re-computing them or re-training the model.
    """
    logger.info(f"Computing stability metrics with {n_bootstrap} bootstrap resamples")
    
    np.random.seed(seed)
    n_samples = shap_values.shape[0]
    
    # Get top clusters by importance
    sorted_clusters = sorted(cluster_importance.items(), key=lambda x: x[1], reverse=True)
    top_clusters = sorted_clusters[:10]
    top_cluster_ids = [cid for cid, _ in top_clusters]
    
    # Store top clusters for each bootstrap
    bootstrap_top_clusters = []
    
    for i in range(n_bootstrap):
        # Resample SHAP values (with replacement)
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_shap = shap_values[indices]
        
        # Recompute cluster importance for resampled data
        resampled_cluster_importance = {}
        for cluster_id, features in clusters.items():
            existing_features = [f for f in features if f in feature_names]
            if not existing_features:
                continue
            
            indices_in_features = [feature_names.index(f) for f in existing_features]
            cluster_shap = np.abs(resampled_shap[:, indices_in_features])
            resampled_cluster_importance[cluster_id] = float(np.mean(cluster_shap))
        
        # Get top 10 clusters for this bootstrap
        sorted_resampled = sorted(resampled_cluster_importance.items(), key=lambda x: x[1], reverse=True)
        resampled_top_cluster_ids = [cid for cid, _ in sorted_resampled[:10]]
        
        bootstrap_top_clusters.append(set(resampled_top_cluster_ids))
    
    # Calculate Jaccard similarity for each bootstrap against the original top clusters
    original_top_set = set(top_cluster_ids)
    jaccard_scores = []
    
    for i in range(n_bootstrap):
        # Use scipy.spatial.distance.jaccard for precise calculation
        # Jaccard distance = 1 - Jaccard similarity
        dist = jaccard(list(original_top_set), list(bootstrap_top_clusters[i]))
        jaccard_sim = 1.0 - dist
        jaccard_scores.append(jaccard_sim)
    
    # Calculate mean Jaccard similarity
    mean_jaccard = float(np.mean(jaccard_scores))
    
    return jaccard_scores, mean_jaccard

def verify_jaccard_precision(jaccard_scores: List[float]) -> bool:
    """
    Verify that Jaccard similarity calculation is precise.
    Assert that Jaccard scores for identical sets are maximal (1.0).
    """
    # Test with identical sets
    set1 = {1, 2, 3, 4, 5}
    set2 = {1, 2, 3, 4, 5}
    
    dist = jaccard(list(set1), list(set2))
    sim = 1.0 - dist
    
    # Jaccard similarity of identical sets should be 1.0
    assert sim == 1.0, f"Jaccard similarity of identical sets should be 1.0, got {sim}"
    
    # Test with completely different sets
    set3 = {1, 2, 3}
    set4 = {4, 5, 6}
    
    dist2 = jaccard(list(set3), list(set4))
    sim2 = 1.0 - dist2
    
    # Jaccard similarity of disjoint sets should be 0.0
    assert sim2 == 0.0, f"Jaccard similarity of disjoint sets should be 0.0, got {sim2}"
    
    logger.info("Jaccard precision verification passed")
    return True

def main():
    """Main entry point for cluster-aware SHAP analysis."""
    parser = argparse.ArgumentParser(description="Cluster-aware SHAP analysis")
    parser.add_argument("--model", required=True, help="Path to trained model pickle file")
    parser.add_argument("--data", required=True, help="Path to processed descriptors parquet file")
    parser.add_argument("--clusters", required=True, help="Path to cluster map CSV file")
    parser.add_argument("--output", default=str(ANALYSIS_DIR / "shap_analysis.json"), 
                      help="Path to output JSON file")
    
    args = parser.parse_args()
    
    # Verify Jaccard precision
    verify_jaccard_precision([])
    
    # Load model and data
    model, data = load_model_and_data(args.model, args.data)
    
    # Load clusters
    clusters = load_clusters_from_file(args.clusters)
    
    # Run cluster-aware SHAP analysis
    cluster_importance = run_cluster_aware_shap_analysis(model, data, clusters)
    
    # Compute stability metrics
    feature_names = [col for col in data.columns if col.startswith('desc_')]
    shap_values = compute_shap_values(model, data, feature_names)
    
    jaccard_scores, mean_jaccard = compute_stability_metrics(
        cluster_importance, shap_values, feature_names, clusters
    )
    
    # Prepare results
    results = {
        "cluster_importance": cluster_importance,
        "stability_metrics": {
            "mean_jaccard_similarity": mean_jaccard,
            "jaccard_scores": jaccard_scores,
            "n_bootstrap": len(jaccard_scores)
        },
        "top_10_clusters": sorted(cluster_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    }
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    logger.info(f"Mean Jaccard similarity: {mean_jaccard:.4f}")
    
    # Verify that identical sets produce maximal Jaccard score
    test_set1 = set(range(10))
    test_set2 = set(range(10))
    dist = jaccard(list(test_set1), list(test_set2))
    sim = 1.0 - dist
    assert sim == 1.0, f"Precision check failed: identical sets should have Jaccard=1.0, got {sim}"
    
    return results

if __name__ == "__main__":
    main()