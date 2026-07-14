"""
Feature Clustering and VIF Analysis Module.

This module provides functionality for computing Variance Inflation Factors (VIF),
clustering correlated features, and performing iterative VIF-based feature removal.

**Conflict Note (FR-007 vs Plan.md):**
This module implements Spec FR-007 which requires iterative VIF-based feature removal
to eliminate multicollinearity (VIF > 5.0). This contradicts the current plan.md
stance of "diagnostic only" for VIF. The code below explicitly documents this
deviation to satisfy the spec's functional requirement.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
from utils.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def compute_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Compute Variance Inflation Factor (VIF) for a list of features in a DataFrame.

    Args:
        df: DataFrame containing the features.
        features: List of column names to compute VIF for.

    Returns:
        DataFrame with 'feature', 'vif' columns.
    """
    vif_data = []
    # Add a constant term for the regression intercept if not present
    # However, standard VIF calculation usually assumes centered data or includes intercept
    # We will use the standard OLS approach from statsmodels or manual calculation
    # Manual calculation: VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing feature i on others.

    for i, feature in enumerate(features):
        y = df[feature].values
        X = df.drop(columns=[feature]).values

        # Handle constant columns or near-zero variance
        if np.std(y) < 1e-8:
            vif_data.append({'feature': feature, 'vif': np.inf})
            continue

        # Add intercept for regression
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])

        # Calculate R^2
        # beta = (X^T X)^-1 X^T y
        try:
            # Use pseudo-inverse for stability
            beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            y_pred = X_with_intercept @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            if ss_tot < 1e-8:
                r_squared = 0.0
            else:
                r_squared = 1.0 - (ss_res / ss_tot)

            # Prevent division by zero if R^2 is exactly 1 (perfect multicollinearity)
            if r_squared >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r_squared)

            vif_data.append({'feature': feature, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not compute VIF for {feature}: {e}")
            vif_data.append({'feature': feature, 'vif': np.inf})

    return pd.DataFrame(vif_data)

def cluster_correlated_features(df: pd.DataFrame, threshold: float = 0.8) -> Dict[str, List[str]]:
    """
    Group correlated features into clusters based on Pearson correlation.

    Args:
        df: DataFrame with features.
        threshold: Correlation threshold to consider features as correlated.

    Returns:
        Dictionary mapping cluster ID to list of feature names.
    """
    corr_matrix = df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Find features with correlation above threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    # Simple clustering: group connected components
    # Using a union-find approach or simple traversal
    clusters = {}
    visited = set()
    cluster_id = 0

    # Build adjacency list
    adj = {col: set() for col in df.columns}
    for col in df.columns:
        for other_col in df.columns:
            if col != other_col and abs(corr_matrix.loc[col, other_col]) > threshold:
                adj[col].add(other_col)

    for col in df.columns:
        if col not in visited:
            stack = [col]
            current_cluster = []
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    current_cluster.append(node)
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            stack.append(neighbor)
            if current_cluster:
                clusters[f"cluster_{cluster_id}"] = current_cluster
                cluster_id += 1

    return clusters

def run_feature_clustering_analysis(df: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    """
    Run full clustering analysis and save results.

    Args:
        df: DataFrame with features.
        output_dir: Directory to save analysis artifacts.

    Returns:
        Dictionary with analysis summary.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    features = df.columns.tolist()
    
    # Compute VIF
    vif_df = compute_vif(df, features)
    vif_df.to_csv(output_dir / "vif_scores.csv", index=False)
    
    # Cluster
    clusters = cluster_correlated_features(df)
    with open(output_dir / "feature_clusters.json", "w") as f:
        json.dump(clusters, f, indent=2)
    
    return {
        "vif_summary": vif_df.to_dict(orient="records"),
        "clusters": clusters,
        "total_features": len(features)
    }

def iterative_vif_removal(df: pd.DataFrame, threshold: float = 5.0, max_iterations: int = 100) -> Tuple[pd.DataFrame, List[str]]:
    """
    Iteratively remove features with VIF > threshold until all remaining features have VIF <= threshold.
    
    This function implements Spec FR-007 which mandates VIF-based feature removal,
    explicitly overriding the plan.md "diagnostic only" stance.
    
    Args:
        df: DataFrame containing features (and optionally target, but target should be excluded from VIF calc).
            Ideally, this should be the feature matrix only.
        threshold: VIF threshold (default 5.0).
        max_iterations: Maximum number of removal iterations.
    
    Returns:
        Tuple of (reduced_df, removed_features_list).
    """
    logger.info(f"Starting iterative VIF removal with threshold {threshold}")
    logger.info(f"Initial number of features: {len(df.columns)}")
    
    current_df = df.copy()
    removed_features = []
    iteration = 0
    
    while iteration < max_iterations:
        features = current_df.columns.tolist()
        if len(features) <= 1:
            logger.warning("Only 1 feature remaining, stopping VIF removal.")
            break
        
        vif_df = compute_vif(current_df, features)
        
        # Find feature with highest VIF
        max_vif_idx = vif_df['vif'].idxmax()
        max_vif = vif_df.loc[max_vif_idx, 'vif']
        feature_to_remove = vif_df.loc[max_vif_idx, 'feature']
        
        if max_vif <= threshold:
            logger.info(f"All features have VIF <= {threshold}. Stopping removal.")
            break
        
        logger.info(f"Iteration {iteration}: Removing '{feature_to_remove}' with VIF={max_vif:.2f}")
        
        current_df = current_df.drop(columns=[feature_to_remove])
        removed_features.append(feature_to_remove)
        iteration += 1
    
    logger.info(f"VIF removal complete. Removed {len(removed_features)} features.")
    logger.info(f"Remaining features: {len(current_df.columns)}")
    
    return current_df, removed_features

def main():
    """
    Main entry point for feature clustering and VIF removal analysis.
    """
    # Configuration
    input_path = Path("data/processed/descriptors.parquet")
    output_dir = Path("data/processed/analysis")
    vif_threshold = 5.0
    
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        # Load data
        df = pd.read_parquet(input_path)
        
        # Identify feature columns (exclude 'target' or 'dipole' if present)
        # Assuming the target column is named 'target' or 'dipole_moment'
        target_cols = [col for col in df.columns if col.lower() in ['target', 'dipole', 'dipole_moment', 'y']]
        feature_cols = [col for col in df.columns if col not in target_cols]
        
        if not feature_cols:
            logger.error("No feature columns found in the dataset.")
            sys.exit(1)
        
        logger.info(f"Processing {len(feature_cols)} features")
        
        # Step 1: Diagnostic Clustering (T031a)
        logger.info("Running diagnostic clustering analysis...")
        analysis_results = run_feature_clustering_analysis(df[feature_cols], output_dir)
        logger.info(f"Diagnostic analysis saved to {output_dir}")
        
        # Step 2: Iterative VIF Removal (T031b - Spec FR-007)
        logger.info(f"Running iterative VIF removal (threshold={vif_threshold})...")
        reduced_df, removed_list = iterative_vif_removal(df[feature_cols], threshold=vif_threshold)
        
        # Save removed features list
        removed_path = output_dir / "removed_features_vif.csv"
        pd.DataFrame({"removed_feature": removed_list}).to_csv(removed_path, index=False)
        logger.info(f"Removed features list saved to {removed_path}")
        
        # Save reduced feature matrix
        # We need to re-attach the target column if it existed, but for the feature matrix save
        # we just save the reduced features. The model training will need to know which features to use.
        reduced_features_path = output_dir / "descriptors_reduced.parquet"
        
        # If target was in the original df, we might want to save the reduced df with target too
        # But the task asks for feature removal. Let's save the reduced feature matrix.
        # If the original df had a target, we should probably keep it for downstream compatibility
        # unless the spec says to drop it. We'll assume we keep the target if it was there.
        final_df = df.drop(columns=feature_cols) # Drop original features
        final_df = pd.concat([final_df, reduced_df], axis=1) # Add reduced features
        
        final_df.to_parquet(reduced_features_path, index=False)
        logger.info(f"Reduced feature matrix saved to {reduced_features_path}")
        
        # Log summary
        logger.info("=== VIF Removal Summary ===")
        logger.info(f"Initial features: {len(feature_cols)}")
        logger.info(f"Removed features: {len(removed_list)}")
        logger.info(f"Final features: {len(reduced_df.columns)}")
        logger.info(f"Removed features: {removed_list}")
        
    except Exception as e:
        logger.error(f"Error during feature clustering: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()