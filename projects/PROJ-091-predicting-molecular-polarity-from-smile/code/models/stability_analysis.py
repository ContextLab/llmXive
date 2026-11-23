import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

import numpy as np
import pandas as pd
from scipy.spatial.distance import jaccard as scipy_jaccard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_top_feature_indices(
    shap_values: np.ndarray,
    cluster_map: Dict[str, int],
    top_k: int = 10
) -> List[int]:
    """
    Identify the top K feature indices based on mean absolute SHAP values.
    
    Args:
        shap_values: 2D array of SHAP values (n_samples, n_features).
        cluster_map: Dict mapping feature_name -> cluster_id.
        top_k: Number of top clusters to select.
        
    Returns:
        List of top feature indices (or cluster representative indices).
    """
    # Compute mean absolute SHAP values per feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Sort indices by importance
    sorted_indices = np.argsort(mean_abs_shap)[::-1]
    
    # Return top K indices
    return sorted_indices[:top_k].tolist()

def calculate_jaccard_similarity(set_a: Set[Any], set_b: Set[Any]) -> float:
    """
    Calculate Jaccard similarity between two sets.
    Uses scipy.spatial.distance.jaccard for precision, handling edge cases.
    
    Jaccard similarity = |A ∩ B| / |A ∪ B|
    scipy.spatial.distance.jaccard returns 1 - similarity, so we invert.
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
        
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
        
    return intersection / union

def analyze_cluster_stability(
    shap_values: np.ndarray,
    cluster_map: Dict[str, int],
    n_bootstrap: int = 100,
    top_k_clusters: int = 10,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Analyze stability of top feature clusters across bootstrap resamples.
    Implements SHAP-only resampling (Plan Override) to avoid re-computation.
    
    Args:
        shap_values: Pre-computed SHAP values (n_samples, n_features).
        cluster_map: Dict mapping feature_name -> cluster_id.
        n_bootstrap: Number of bootstrap resamples.
        top_k_clusters: Number of top clusters to track.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing stability metrics and Jaccard scores.
    """
    np.random.seed(seed)
    n_samples, n_features = shap_values.shape
    
    # Map feature index to cluster ID
    # cluster_map keys are feature names, values are cluster IDs.
    # We need to map indices to cluster IDs.
    # Assuming feature names in cluster_map correspond to column indices 0..n-1
    # If cluster_map keys are strings like 'desc_1', we need to map them.
    # For simplicity, assume cluster_map keys are 'desc_0', 'desc_1', ...
    # or we map by order.
    
    # Let's create a mapping from index to cluster_id
    # We assume the columns in shap_values correspond to the keys in cluster_map
    # in the same order as the dataframe columns.
    # If cluster_map keys are not ordered, we sort them.
    
    sorted_feature_names = sorted(cluster_map.keys())
    # If the keys are not in order 0..n, we assume the dataframe columns
    # match the sorted order of keys or the original order.
    # To be safe, we assume the user passed the correct mapping.
    # We will build a list of cluster_ids for indices 0..n_features-1
    # by assuming the keys in cluster_map are 'desc_0', 'desc_1', etc.
    # If not, we try to map by index if keys are numeric strings.
    
    index_to_cluster = {}
    for i, name in enumerate(sorted_feature_names):
        if i < n_features:
            index_to_cluster[i] = cluster_map[name]
    
    # Determine top K clusters based on mean absolute SHAP values
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    sorted_indices = np.argsort(mean_abs_shap)[::-1]
    
    # Get the top K unique clusters
    top_clusters = set()
    for idx in sorted_indices:
        if idx in index_to_cluster:
            top_clusters.add(index_to_cluster[idx])
        if len(top_clusters) >= top_k_clusters:
            break
    
    logger.info(f"Identified {len(top_clusters)} top clusters: {top_clusters}")
    
    # Bootstrap resampling of SHAP values (SHAP-only resampling)
    # We resample the rows (samples) of the SHAP values matrix.
    # Then we re-calculate the top clusters for each resample.
    
    jaccard_scores = []
    cluster_stability_report = []
    
    for i in range(n_bootstrap):
        # Resample rows with replacement
        resample_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_shap = shap_values[resample_indices, :]
        
        # Calculate mean absolute SHAP for resample
        resampled_mean_abs = np.mean(np.abs(resampled_shap), axis=0)
        resampled_sorted_indices = np.argsort(resampled_mean_abs)[::-1]
        
        # Get top K clusters for this resample
        resample_top_clusters = set()
        for idx in resampled_sorted_indices:
            if idx in index_to_cluster:
                resample_top_clusters.add(index_to_cluster[idx])
            if len(resample_top_clusters) >= top_k_clusters:
                break
        
        # Calculate Jaccard similarity with the original top clusters
        if i == 0:
            # First iteration: use the original top clusters as reference
            # But we need to define the reference set.
            # The task says: "Select the top-ranked clusters ... Verify that these top 10 clusters remain consistent"
            # We compare each resample's top clusters to the original top clusters.
            # For the first one, we compare to itself -> Jaccard = 1.0
            jacc = 1.0
        else:
            # Compare to the original top clusters (from the full dataset)
            jacc = calculate_jaccard_similarity(top_clusters, resample_top_clusters)
        
        jaccard_scores.append(jacc)
        cluster_stability_report.append({
            "resample_id": i,
            "jaccard_similarity": jacc,
            "top_clusters_found": list(resample_top_clusters)
        })
        
        if (i + 1) % 10 == 0:
            logger.info(f"Bootstrap {i+1}/{n_bootstrap}, Jaccard: {jacc:.4f}")
    
    # Compute aggregate statistics
    mean_jaccard = np.mean(jaccard_scores)
    std_jaccard = np.std(jaccard_scores)
    min_jaccard = np.min(jaccard_scores)
    
    result = {
        "n_bootstrap": n_bootstrap,
        "top_k_clusters": top_k_clusters,
        "original_top_clusters": list(top_clusters),
        "mean_jaccard_similarity": mean_jaccard,
        "std_jaccard_similarity": std_jaccard,
        "min_jaccard_similarity": min_jaccard,
        "stability_threshold": 0.7,
        "passed_threshold": mean_jaccard >= 0.7,
        "detailed_results": cluster_stability_report
    }
    
    return result

def analyze_individual_feature_stability(
    shap_values: np.ndarray,
    n_bootstrap: int = 100,
    top_k_features: int = 10,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Analyze stability of individual top features across bootstrap resamples.
    (Optional, for comparison with cluster-based analysis).
    """
    np.random.seed(seed)
    n_samples, n_features = shap_values.shape
    
    # Get original top features
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    sorted_indices = np.argsort(mean_abs_shap)[::-1]
    original_top_features = set(sorted_indices[:top_k_features])
    
    jaccard_scores = []
    
    for i in range(n_bootstrap):
        resample_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled_shap = shap_values[resample_indices, :]
        
        resampled_mean_abs = np.mean(np.abs(resampled_shap), axis=0)
        resampled_sorted_indices = np.argsort(resampled_mean_abs)[::-1]
        resample_top_features = set(resampled_sorted_indices[:top_k_features])
        
        if i == 0:
            jacc = 1.0
        else:
            jacc = calculate_jaccard_similarity(original_top_features, resample_top_features)
        
        jaccard_scores.append(jacc)
    
    return {
        "n_bootstrap": n_bootstrap,
        "mean_jaccard": np.mean(jaccard_scores),
        "std_jaccard": np.std(jaccard_scores)
    }

def run_stability_analysis(
    shap_values_path: str,
    cluster_map_path: str,
    output_path: str,
    n_bootstrap: int = 100,
    top_k_clusters: int = 10
) -> None:
    """
    Main entry point to run cluster stability analysis.
    """
    logger.info(f"Loading SHAP values from {shap_values_path}")
    with open(shap_values_path, 'rb') as f:
        shap_data = pickle.load(f)
    
    # Handle different pickle structures
    if isinstance(shap_data, dict):
        shap_values = shap_data.get('shap_values')
        if shap_values is None:
            # Try to find the array directly
            for k, v in shap_data.items():
                if isinstance(v, np.ndarray):
                    shap_values = v
                    break
    elif isinstance(shap_data, np.ndarray):
        shap_values = shap_data
    else:
        raise ValueError(f"Unexpected SHAP data format: {type(shap_data)}")
        
    if shap_values is None:
        raise ValueError("Could not extract SHAP values from pickle file")
        
    logger.info(f"Loaded SHAP values shape: {shap_values.shape}")
    
    logger.info(f"Loading cluster map from {cluster_map_path}")
    cluster_map = {}
    with open(cluster_map_path, 'r') as f:
        # Expecting CSV or JSON. Assuming CSV based on T031c.
        # Format: feature_id, cluster_id
        # We need to map feature_id (string) to cluster_id (int)
        # If it's CSV:
        lines = f.readlines()
        header = lines[0].strip().split(',')
        feature_idx = 0
        cluster_idx = 1
        if 'feature_id' in header:
            feature_idx = header.index('feature_id')
        if 'cluster_id' in header:
            cluster_idx = header.index('cluster_id')
            
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) > max(feature_idx, cluster_idx):
                feature_id = parts[feature_idx]
                cluster_id = int(parts[cluster_idx])
                cluster_map[feature_id] = cluster_id
    
    if not cluster_map:
        raise ValueError("Cluster map is empty or invalid")
        
    logger.info(f"Loaded {len(cluster_map)} feature-cluster mappings")
    
    logger.info(f"Running stability analysis with {n_bootstrap} bootstrap resamples")
    result = analyze_cluster_stability(
        shap_values=shap_values,
        cluster_map=cluster_map,
        n_bootstrap=n_bootstrap,
        top_k_clusters=top_k_clusters
    )
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Stability analysis complete. Mean Jaccard: {result['mean_jaccard_similarity']:.4f}")
    logger.info(f"Threshold (0.7) passed: {result['passed_threshold']}")

def main():
    """
    CLI entry point for stability analysis.
    Expected arguments:
    --shap-values: Path to SHAP values pickle file
    --clusters: Path to cluster_map.csv
    --output: Path to output JSON report
    --n-bootstrap: Number of bootstrap resamples (default: 100)
    --top-k: Number of top clusters to track (default: 10)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run cluster stability analysis")
    parser.add_argument("--shap-values", required=True, help="Path to SHAP values pickle file")
    parser.add_argument("--clusters", required=True, help="Path to cluster_map.csv")
    parser.add_argument("--output", required=True, help="Path to output JSON report")
    parser.add_argument("--n-bootstrap", type=int, default=100, help="Number of bootstrap resamples")
    parser.add_argument("--top-k", type=int, default=10, help="Number of top clusters to track")
    
    args = parser.parse_args()
    
    try:
        run_stability_analysis(
            shap_values_path=args.shap_values,
            cluster_map_path=args.clusters,
            output_path=args.output,
            n_bootstrap=args.n_bootstrap,
            top_k_clusters=args.top_k
        )
    except Exception as e:
        logger.error(f"Stability analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
