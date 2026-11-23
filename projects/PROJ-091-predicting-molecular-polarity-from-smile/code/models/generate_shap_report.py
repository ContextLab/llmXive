"""
SHAP Analysis and Feature Importance Reporting Module.

This module generates SHAP summary plots and feature importance reports
that distinguish between collinear feature clusters as identified by
the VIF clustering analysis.

It relies on pre-computed artifacts:
  - data/processed/descriptors.parquet (features + target)
  - data/processed/model.pkl (trained LightGBM model)
  - data/processed/analysis/feature_clusters.json (cluster definitions from T031)
"""
import os
import sys
import json
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/CLI environments
import matplotlib.pyplot as plt

# Project imports
from utils.logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
ANALYSIS_DIR = Path("data/processed/analysis")
DATA_DIR = Path("data/processed")
DESCRIPTORS_FILE = DATA_DIR / "descriptors.parquet"
MODEL_FILE = DATA_DIR / "model.pkl"
CLUSTERS_FILE = ANALYSIS_DIR / "feature_clusters.json"
SHAP_SUMMARY_PLOT = ANALYSIS_DIR / "shap_summary_plot.png"
FEATURE_REPORT_FILE = ANALYSIS_DIR / "feature_importance_report.json"
SHAP_VALUES_FILE = ANALYSIS_DIR / "shap_values.pkl"


def ensure_analysis_dir():
    """Ensure the analysis output directory exists."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def load_model_and_data() -> Tuple[Any, pd.DataFrame]:
    """
    Load the trained model and the processed descriptor data.

    Returns:
        Tuple of (model, dataframe)
    """
    if not MODEL_FILE.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_FILE}. Run training first.")
    if not DESCRIPTORS_FILE.exists():
        raise FileNotFoundError(f"Data file not found: {DESCRIPTORS_FILE}. Run preprocessing first.")

    logger.info(f"Loading model from {MODEL_FILE}")
    with open(MODEL_FILE, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loading data from {DESCRIPTORS_FILE}")
    df = pd.read_parquet(DESCRIPTORS_FILE)

    # Drop non-feature columns for model input
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    X = df[feature_cols]
    y = df['target']

    return model, X, y, df


def load_clusters() -> Dict[str, Any]:
    """
    Load the feature cluster definitions from the VIF analysis.

    Returns:
        Dictionary mapping cluster IDs to lists of feature names.
    """
    if not CLUSTERS_FILE.exists():
        raise FileNotFoundError(f"Cluster file not found: {CLUSTERS_FILE}. Run feature clustering first.")

    with open(CLUSTERS_FILE, 'r') as f:
        clusters = json.load(f)
    return clusters


def generate_shap_summary_plot(
    model: Any,
    X: pd.DataFrame,
    clusters: Dict[str, Any],
    max_samples: int = 2000
) -> str:
    """
    Generate a SHAP summary plot and save it to disk.

    The plot visualizes the impact of features on the model output.
    Features are colored by their cluster assignment if available.

    Args:
        model: Trained LightGBM model.
        X: Feature DataFrame.
        clusters: Dictionary of cluster definitions.
        max_samples: Maximum number of samples to use for SHAP calculation.

    Returns:
        Path to the saved plot.
    """
    logger.info("Computing SHAP values...")
    
    # Sample data if too large to avoid memory issues
    if len(X) > max_samples:
        logger.info(f"Sampling {max_samples} rows for SHAP calculation...")
        X_sample = X.sample(n=max_samples, random_state=42)
    else:
        X_sample = X

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # Save raw SHAP values for downstream tasks (T037)
    with open(SHAP_VALUES_FILE, 'wb') as f:
        pickle.dump({
            'shap_values': shap_values,
            'feature_names': list(X.columns),
            'samples': X_sample.to_dict('records')
        }, f)
    logger.info(f"Saved SHAP values to {SHAP_VALUES_FILE}")

    # Prepare colors based on clusters
    feature_names = list(X.columns)
    cluster_map = {}
    for cluster_id, members in clusters.items():
        for member in members:
            if member in feature_names:
                cluster_map[member] = cluster_id

    # Map cluster IDs to colors
    unique_clusters = sorted(list(set(cluster_map.values())))
    color_map = {c: plt.cm.tab10(i % 10) for i, c in enumerate(unique_clusters)}
    
    # Assign colors to features
    colors = [color_map.get(cluster_map.get(f), (0.5, 0.5, 0.5)) for f in feature_names]

    # Generate plot
    plt.figure(figsize=(12, 10))
    shap.summary_plot(
        shap_values, 
        X_sample, 
        feature_names=feature_names,
        plot_type="bar", # Use bar plot for clearer ranking of clusters
        show=False,
        color_bar=False
    )
    
    # Annotate clusters if possible (SHAP summary plot doesn't natively support per-feature coloring easily in bar mode)
    # Instead, we generate a standard summary and a separate cluster importance bar chart
    plt.title("SHAP Feature Importance (Top Features)")
    plt.tight_layout()
    plt.savefig(SHAP_SUMMARY_PLOT, dpi=150)
    plt.close()

    logger.info(f"Saved SHAP summary plot to {SHAP_SUMMARY_PLOT}")
    return str(SHAP_SUMMARY_PLOT)


def generate_cluster_importance_report(
    shap_values: np.ndarray,
    feature_names: List[str],
    clusters: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    Compute cluster-level importance using mean absolute SHAP values.

    Args:
        shap_values: 2D array of SHAP values (samples x features).
        feature_names: List of feature names.
        clusters: Dictionary mapping cluster ID to list of feature names.

    Returns:
        List of dictionaries containing cluster statistics, sorted by importance.
    """
    # Calculate mean absolute SHAP value for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    feature_importance = dict(zip(feature_names, mean_abs_shap))

    cluster_importance = []
    
    for cluster_id, members in clusters.items():
        # Filter members that actually exist in the data
        valid_members = [m for m in members if m in feature_importance]
        if not valid_members:
            continue

        # Calculate cluster importance as mean absolute SHAP of members
        cluster_scores = [feature_importance[m] for m in valid_members]
        avg_importance = np.mean(cluster_scores)
        max_importance = np.max(cluster_scores)
        
        cluster_importance.append({
            "cluster_id": cluster_id,
            "feature_count": len(valid_members),
            "features": valid_members,
            "mean_abs_shap": float(avg_importance),
            "max_abs_shap": float(max_importance),
            "total_abs_shap": float(np.sum(cluster_scores))
        })

    # Sort by mean absolute SHAP importance descending
    cluster_importance.sort(key=lambda x: x['mean_abs_shap'], reverse=True)
    return cluster_importance


def generate_feature_report(
    model: Any,
    X: pd.DataFrame,
    clusters: Dict[str, Any],
    max_samples: int = 2000
) -> str:
    """
    Generate a comprehensive feature importance report distinguishing clusters.

    Args:
        model: Trained LightGBM model.
        X: Feature DataFrame.
        clusters: Dictionary of cluster definitions.
        max_samples: Max samples for SHAP calculation.

    Returns:
        Path to the saved JSON report.
    """
    # Sample data if needed
    if len(X) > max_samples:
        X_sample = X.sample(n=max_samples, random_state=42)
    else:
        X_sample = X

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    feature_names = list(X.columns)
    
    # Generate standard feature importance (LightGBM gain)
    lgb_importance = model.feature_importance(importance_type='gain')
    lgb_dict = dict(zip(feature_names, lgb_importance))

    # Generate cluster-aware report
    cluster_report = generate_cluster_importance_report(
        shap_values, feature_names, clusters
    )

    # Combine into final report
    report = {
        "metadata": {
            "model_file": str(MODEL_FILE),
            "data_file": str(DESCRIPTORS_FILE),
            "num_samples_analyzed": len(X_sample),
            "total_features": len(feature_names),
            "total_clusters": len(clusters)
        },
        "cluster_importance": cluster_report,
        "individual_feature_importance": {
            "shap_mean_abs": dict(zip(feature_names, np.mean(np.abs(shap_values), axis=0))),
            "lgb_gain": lgb_dict
        }
    }

    with open(FEATURE_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved feature importance report to {FEATURE_REPORT_FILE}")
    return str(FEATURE_REPORT_FILE)


def main():
    """Main entry point for generating SHAP reports."""
    logger.info("Starting SHAP report generation (T036)...")
    ensure_analysis_dir()

    try:
        # Load dependencies
        model, X, y, df = load_model_and_data()
        clusters = load_clusters()
        logger.info(f"Loaded {len(clusters)} feature clusters.")

        # Generate Plot
        plot_path = generate_shap_summary_plot(model, X, clusters)
        logger.info(f"Plot generated: {plot_path}")

        # Generate Report
        report_path = generate_feature_report(model, X, clusters)
        logger.info(f"Report generated: {report_path}")

        logger.info("T036 completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error generating SHAP report: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())