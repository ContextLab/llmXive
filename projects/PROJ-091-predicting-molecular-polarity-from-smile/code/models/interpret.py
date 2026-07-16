import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import lightgbm as lgb
import shap
from rdkit import Chem
from rdkit.Chem import Descriptors

from utils.logging_config import get_logger, set_log_level
from utils.config import load_hyperparameters
from data.loader import iterate_smiles, load_batch
from data.feature_clustering import cluster_correlated_features, compute_vif

# Ensure logging is configured
logger = get_logger(__name__)
set_log_level(logging.INFO)

# Constants
DATA_PROCESSED = Path("data/processed")
DATA_ANALYSIS = Path("data/processed/analysis")
MODEL_PATH = DATA_PROCESSED / "model.pkl"
DESCRIPTORS_PATH = DATA_PROCESSED / "descriptors.parquet"
SHAP_VALUES_PATH = DATA_ANALYSIS / "shap_values.pkl"
SHAP_SUMMARY_PLOT_PATH = DATA_ANALYSIS / "shap_summary_plot.png"
FEATURE_REPORT_PATH = DATA_ANALYSIS / "feature_importance_report.json"
CLUSTER_REPORT_PATH = DATA_ANALYSIS / "feature_clusters.json"

def load_model_and_data() -> Tuple[lgb.Booster, pd.DataFrame, pd.Series, List[str]]:
    """Load the trained model and processed data."""
    logger.info(f"Loading model from {MODEL_PATH}")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loading descriptors from {DESCRIPTORS_PATH}")
    df = pd.read_parquet(DESCRIPTORS_PATH)

    # Separate features and target
    # Assuming the target column is named 'target' or 'dipole' based on common conventions
    # We need to identify the target column. Let's assume it's the last column or named 'target'.
    # Based on T007/T014 logic, target is usually separated.
    # Let's check columns. If 'target' exists, use it. Otherwise, assume last column.
    if 'target' in df.columns:
        y = df['target']
        X = df.drop(columns=['target'])
    elif 'dipole' in df.columns:
        y = df['dipole']
        X = df.drop(columns=['dipole'])
    else:
        # Fallback: last column is target
        target_col = df.columns[-1]
        y = df[target_col]
        X = df.drop(columns=[target_col])

    feature_names = list(X.columns)
    return model, X, y, feature_names

def compute_shap_values(model: lgb.Booster, X: pd.DataFrame) -> np.ndarray:
    """Compute SHAP values for the model."""
    logger.info("Computing SHAP values...")
    # Use TreeExplainer for LightGBM
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    return shap_values

def get_cluster_aware_importance(
    shap_values: np.ndarray,
    feature_names: List[str],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Group features into clusters based on correlation and calculate
    aggregate importance for each cluster.
    """
    logger.info("Calculating cluster-aware importance...")
    # Convert shap_values to absolute mean for importance
    # shap_values shape: (n_samples, n_features)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)

    # Create a DataFrame for correlation analysis
    # We need the feature matrix X to compute correlations, but we only have shap_values here.
    # However, the task requires distinguishing collinear clusters.
    # We should re-load X or pass it. Let's assume we need X.
    # Since this function is called after load, we might need to pass X or re-load.
    # To keep it self-contained, we will assume X is available or re-load it if needed.
    # But for efficiency, let's assume the caller passes X or we re-load from parquet.
    # Re-loading is safer for stateless function design.
    df = pd.read_parquet(DESCRIPTORS_PATH)
    if 'target' in df.columns:
        X = df.drop(columns=['target'])
    elif 'dipole' in df.columns:
        X = df.drop(columns=['dipole'])
    else:
        X = df.drop(columns=[df.columns[-1]])

    # Ensure column order matches feature_names
    X = X[feature_names]

    # Compute correlation matrix
    corr_matrix = X.corr().abs()

    # Use the existing clustering logic from feature_clustering
    clusters = cluster_correlated_features(corr_matrix, threshold=threshold)

    # Calculate aggregate importance per cluster
    cluster_importance = {}
    cluster_members = {}

    for i, cluster in enumerate(clusters):
        cluster_features = [feature_names[idx] for idx in cluster]
        cluster_members[f"Cluster_{i}"] = cluster_features

        # Sum of mean absolute SHAP values for features in this cluster
        total_importance = sum(mean_abs_shap[idx] for idx in cluster)
        cluster_importance[f"Cluster_{i}"] = {
            "total_importance": float(total_importance),
            "num_features": len(cluster),
            "features": cluster_features
        }

    # Sort clusters by total importance
    sorted_clusters = dict(
        sorted(cluster_importance.items(), key=lambda x: x[1]["total_importance"], reverse=True)
    )

    return {
        "clusters": sorted_clusters,
        "cluster_members": cluster_members,
        "individual_importance": {
            feature_names[i]: float(mean_abs_shap[i])
            for i in range(len(feature_names))
        }
    }

def generate_shap_summary_plot(
    shap_values: np.ndarray,
    feature_names: List[str],
    X: pd.DataFrame,
    output_path: Path
) -> None:
    """Generate and save the SHAP summary plot."""
    logger.info(f"Generating SHAP summary plot to {output_path}")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create SHAP summary plot
    # shap.summary_plot requires (shap_values, features)
    # For TreeExplainer, shap_values is usually a 2D array or list of arrays
    # If model is regression, shap_values is 2D (n_samples, n_features)
    # If classification, it might be a list. Assuming regression (dipole).

    plt = shap.summary_plot(
        shap_values,
        X,
        feature_names=feature_names,
        plot_type="bar",
        show=False,
        color_bar=True,
        max_display=20  # Limit to top 20 for clarity
    )

    # Save the figure
    fig = plt.gcf() if hasattr(plt, 'gcf') else plt
    # shap.summary_plot returns None or a plot object depending on version
    # The standard way is to capture the axes or just use the side effect
    # shap.summary_plot usually draws directly.
    # Let's use the standard shap output handling
    import matplotlib.pyplot as plt_module
    fig = plt_module.gcf()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt_module.close(fig)

    logger.info(f"SHAP summary plot saved to {output_path}")

def save_shap_values(shap_values: np.ndarray, output_path: Path) -> None:
    """Save SHAP values to disk."""
    logger.info(f"Saving SHAP values to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(shap_values, f)
    logger.info("SHAP values saved.")

def run_cluster_aware_shap_analysis(model: lgb.Booster, X: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
    """Run the full cluster-aware SHAP analysis."""
    shap_values = compute_shap_values(model, X)
    cluster_analysis = get_cluster_aware_importance(shap_values, feature_names)
    return cluster_analysis, shap_values

def run_two_stage_bootstrap_shap(
    model: lgb.Booster,
    X: pd.DataFrame,
    y: pd.Series,
    n_bootstrap: int = 10,
    sample_fraction: float = 0.8
) -> List[np.ndarray]:
    """
    Resample SHAP values without re-training (SHAP-only resampling).
    This is a faster approximation to check stability.
    """
    logger.info(f"Running two-stage bootstrap (n={n_bootstrap})...")
    shap_values_list = []
    n_samples = X.shape[0]
    indices = np.arange(n_samples)

    for i in range(n_bootstrap):
        # Sample indices
        sampled_indices = np.random.choice(indices, size=int(n_samples * sample_fraction), replace=False)
        X_sample = X.iloc[sampled_indices]

        # Compute SHAP on sample
        explainer = shap.TreeExplainer(model)
        shap_sample = explainer.shap_values(X_sample)
        shap_values_list.append(shap_sample)

    return shap_values_list

def run_full_dataset_bootstrap(
    model: lgb.Booster,
    X: pd.DataFrame,
    y: pd.Series,
    n_bootstrap: int = 5,
    sample_fraction: float = 0.8
) -> List[np.ndarray]:
    """
    Resample dataset, re-train model, and compute SHAP.
    This verifies feature-set stability across different data subsets.
    """
    logger.info(f"Running full dataset bootstrap (n={n_bootstrap})...")
    shap_values_list = []
    n_samples = X.shape[0]
    indices = np.arange(n_samples)

    for i in range(n_bootstrap):
        # Sample indices
        sampled_indices = np.random.choice(indices, size=int(n_samples * sample_fraction), replace=False)
        X_sample = X.iloc[sampled_indices]
        y_sample = y.iloc[sampled_indices]

        # Retrain model
        train_data = lgb.Dataset(X_sample, label=y_sample)
        params = load_hyperparameters()
        params['verbose'] = -1  # Suppress training logs

        # Simple training without complex tuning for speed
        new_model = lgb.train(params, train_data, num_boost_round=100)

        # Compute SHAP
        explainer = shap.TreeExplainer(new_model)
        shap_sample = explainer.shap_values(X_sample)
        shap_values_list.append(shap_sample)

    return shap_values_list

def generate_feature_report(
    cluster_analysis: Dict[str, Any],
    output_path: Path,
    cluster_members_path: Optional[Path] = None
) -> None:
    """Generate and save the feature importance report distinguishing collinear clusters."""
    logger.info(f"Generating feature report to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare report data
    report = {
        "summary": {
            "total_features": len(cluster_analysis.get("individual_importance", {})),
            "total_clusters": len(cluster_analysis.get("clusters", {})),
            "analysis_method": "Cluster-Aware SHAP with Correlation Clustering"
        },
        "cluster_importance": cluster_analysis.get("clusters", {}),
        "individual_importance": cluster_analysis.get("individual_importance", {}),
        "cluster_members": cluster_analysis.get("cluster_members", {})
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Feature report saved to {output_path}")

    if cluster_members_path:
        cluster_members_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cluster_members_path, 'w') as f:
            json.dump(cluster_analysis.get("cluster_members", {}), f, indent=2)
        logger.info(f"Cluster members saved to {cluster_members_path}")

def main():
    """Main entry point for T036: Generate SHAP summary plot and feature importance report."""
    logger.info("Starting T036: SHAP Summary and Feature Report Generation")

    # Ensure output directory exists
    DATA_ANALYSIS.mkdir(parents=True, exist_ok=True)

    # 1. Load Model and Data
    try:
        model, X, y, feature_names = load_model_and_data()
    except Exception as e:
        logger.error(f"Failed to load model or data: {e}")
        sys.exit(1)

    # 2. Run Cluster-Aware SHAP Analysis
    cluster_analysis, shap_values = run_cluster_aware_shap_analysis(model, X, feature_names)

    # 3. Save SHAP Values
    save_shap_values(shap_values, SHAP_VALUES_PATH)

    # 4. Generate SHAP Summary Plot
    # We need X for the plot
    generate_shap_summary_plot(shap_values, feature_names, X, SHAP_SUMMARY_PLOT_PATH)

    # 5. Generate Feature Importance Report
    generate_feature_report(cluster_analysis, FEATURE_REPORT_PATH, CLUSTER_REPORT_PATH)

    logger.info("T036 completed successfully.")
    logger.info(f"Artifacts saved:")
    logger.info(f"  - SHAP Values: {SHAP_VALUES_PATH}")
    logger.info(f"  - Summary Plot: {SHAP_SUMMARY_PLOT_PATH}")
    logger.info(f"  - Feature Report: {FEATURE_REPORT_PATH}")
    logger.info(f"  - Cluster Report: {CLUSTER_REPORT_PATH}")

if __name__ == "__main__":
    main()