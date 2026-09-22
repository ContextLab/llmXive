import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.linear_model import LinearRegression

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """
    Compute Variance Inflation Factor (VIF) for each feature.
    Does NOT remove features; returns scores for all.
    """
    if not feature_cols:
        return pd.DataFrame(columns=['feature', 'vif'])

    vif_data = []
    for i, feature in enumerate(feature_cols):
        X = df[feature_cols].values
        y = df[feature].values
        
        # Fit linear model to predict this feature from others
        model = LinearRegression()
        model.fit(X, y)
        r_squared = model.score(X, y)
        
        # VIF = 1 / (1 - R^2)
        if r_squared >= 1.0:
            vif = np.inf
        else:
            vif = 1.0 / (1.0 - r_squared)
        
        vif_data.append({'feature': feature, 'vif': vif})
        logger.debug(f"Computed VIF for {feature}: {vif:.4f}")

    return pd.DataFrame(vif_data)

def cluster_correlated_features(df: pd.DataFrame, feature_cols: List[str], threshold: float = 0.8) -> Dict[int, List[str]]:
    """
    Group features with |correlation| > threshold into clusters.
    Uses hierarchical clustering on correlation distance.
    """
    if len(feature_cols) < 2:
        return {0: feature_cols} if feature_cols else {}

    # Compute correlation matrix
    corr_matrix = df[feature_cols].corr().abs()
    
    # Convert to distance (1 - correlation)
    dist_matrix = 1 - corr_matrix.values
    
    # Use linkage to cluster (ward or average)
    from scipy.cluster.hierarchy import linkage, fcluster
    
    # Flatten distance matrix for linkage
    condensed_dist = squareform(dist_matrix, checks=False)
    Z = linkage(condensed_dist, method='average')
    
    # Form flat clusters with a threshold on distance (1 - 0.8 = 0.2)
    # We want correlation > 0.8, so distance < 0.2
    cluster_labels = fcluster(Z, t=0.2, criterion='distance')
    
    # Group features by cluster label
    clusters = {}
    for label, feature in zip(cluster_labels, feature_cols):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(feature)
    
    # Re-index clusters to be 0-based consecutive
    new_clusters = {}
    for new_id, old_id in enumerate(sorted(clusters.keys())):
        new_clusters[new_id] = clusters[old_id]
    
    logger.info(f"Identified {len(new_clusters)} feature clusters with |r| > 0.8")
    return new_clusters

def save_vif_scores(vif_df: pd.DataFrame, output_path: Path) -> None:
    """Save VIF scores to CSV."""
    vif_df.to_csv(output_path, index=False)
    logger.info(f"Saved VIF scores to {output_path}")

def save_cluster_map(clusters: Dict[int, List[str]], output_path: Path) -> None:
    """
    Save cluster mapping to CSV.
    Format: feature_id, cluster_id
    """
    records = []
    for cluster_id, features in clusters.items():
        for feature in features:
            records.append({'feature_id': feature, 'cluster_id': cluster_id})
    
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cluster map to {output_path} with {len(records)} entries")

def run_feature_clustering_analysis(
    data_path: Path,
    vif_output_path: Path,
    cluster_output_path: Path,
    correlation_threshold: float = 0.8
) -> None:
    """
    Main entry point for feature clustering analysis.
    Computes VIF and clusters correlated features.
    """
    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_parquet(data_path)
    except FileNotFoundError:
        logger.error(f"Input file not found: {data_path}")
        sys.exit(1)
    
    # Identify feature columns (exclude 'smiles' and 'target')
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    logger.info(f"Found {len(feature_cols)} feature columns")
    
    if not feature_cols:
        logger.warning("No feature columns found. Exiting.")
        return
    
    # Compute VIF
    logger.info("Computing VIF scores...")
    vif_df = compute_vif(df, feature_cols)
    save_vif_scores(vif_df, vif_output_path)
    
    # Cluster correlated features
    logger.info(f"Clustering features with |r| > {correlation_threshold}...")
    clusters = cluster_correlated_features(df, feature_cols, threshold=correlation_threshold)
    save_cluster_map(clusters, cluster_output_path)
    
    logger.info("Feature clustering analysis complete.")

def iterative_vif_removal(df: pd.DataFrame, feature_cols: List[str], threshold: float = 10.0) -> List[str]:
    """
    Placeholder for iterative VIF removal (NOT implemented per Plan Override).
    This function exists for API compatibility but does nothing.
    """
    logger.warning("iterative_vif_removal is disabled per Plan Override. Returning all features.")
    return feature_cols

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Feature Clustering Analysis")
    parser.add_argument("--data", type=str, required=True, help="Path to input parquet file")
    parser.add_argument("--vif-output", type=str, required=True, help="Path for VIF scores CSV")
    parser.add_argument("--cluster-output", type=str, required=True, help="Path for cluster map CSV")
    parser.add_argument("--threshold", type=float, default=0.8, help="Correlation threshold for clustering")
    
    args = parser.parse_args()
    
    data_path = Path(args.data)
    vif_output_path = Path(args.vif_output)
    cluster_output_path = Path(args.cluster_output)
    
    # Ensure output directories exist
    vif_output_path.parent.mkdir(parents=True, exist_ok=True)
    cluster_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    run_feature_clustering_analysis(
        data_path,
        vif_output_path,
        cluster_output_path,
        args.threshold
    )

if __name__ == "__main__":
    main()