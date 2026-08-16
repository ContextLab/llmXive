import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from utils.logging_config import get_logger

logger = get_logger(__name__)

def compute_vif(features: pd.DataFrame) -> pd.Series:
    """Compute Variance Inflation Factor for each feature."""
    vif_data = pd.Series(dtype=float)
    for i, col in enumerate(features.columns):
        X = features.drop(columns=[col])
        y = features[col]
        if X.shape[1] == 0:
            vif_data[col] = 1.0
            continue
        # Simple linear regression to compute R^2
        # Using numpy for speed
        try:
            coeffs = np.linalg.lstsq(X.values, y.values, rcond=None)[0]
            y_pred = X.values @ coeffs
            ss_res = np.sum((y.values - y_pred) ** 2)
            ss_tot = np.sum((y.values - np.mean(y.values)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            vif = 1 / (1 - r_squared) if r_squared < 1 else np.inf
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_data[col] = np.nan
    return vif_data

def cluster_correlated_features(features: pd.DataFrame, threshold: float = 0.8) -> List[List[str]]:
    """Group features with |correlation| > threshold into clusters."""
    corr_matrix = features.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    # Build clusters
    clusters = []
    visited = set()
    
    for col in corr_matrix.columns:
        if col in visited:
            continue
        cluster = [col]
        visited.add(col)
        for other_col in corr_matrix.columns:
            if other_col == col or other_col in visited:
                continue
            if abs(corr_matrix.loc[col, other_col]) > threshold:
                cluster.append(other_col)
                visited.add(other_col)
        if len(cluster) > 1:
            clusters.append(cluster)
    
    return clusters

def run_feature_clustering_analysis(data_path: Path, output_path: Path) -> Dict[str, Any]:
    """Run full feature clustering analysis."""
    logger.info(f"Loading data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Filter out non-feature columns
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    features = df[feature_cols].dropna()
    
    if features.empty:
        logger.warning("No features to analyze")
        return {"clusters": [], "vif": {}}
    
    vif_results = compute_vif(features)
    clusters = cluster_correlated_features(features)
    
    report = {
        "clusters": clusters,
        "vif": vif_results.to_dict(),
        "summary": {
            "total_features": len(feature_cols),
            "clusters_found": len(clusters),
            "avg_cluster_size": np.mean([len(c) for c in clusters]) if clusters else 0
        }
    }
    
    logger.info(f"Saving report to {output_path}")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    return report

def iterative_vif_removal(features: pd.DataFrame, threshold: float = 10.0) -> pd.DataFrame:
    """Iteratively remove features with VIF > threshold."""
    # Note: T031 says DO NOT implement iterative removal, but the function exists in API
    # We keep it as a stub or minimal implementation to satisfy API surface
    logger.info("Iterative VIF removal not implemented per T031 constraints")
    return features

def main() -> None:
    """Main entry point."""
    data_path = Path("data/processed/descriptors.parquet")
    output_path = Path("data/processed/analysis/feature_clusters.json")
    run_feature_clustering_analysis(data_path, output_path)

if __name__ == "__main__":
    main()
