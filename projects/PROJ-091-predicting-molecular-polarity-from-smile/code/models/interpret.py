"""
Cluster-Aware SHAP Analysis Module.

Implements SHAP analysis on the trained LightGBM model using 2D descriptors.
Includes Cluster-Aware importance aggregation, two-stage bootstrap stability,
and full dataset bootstrap for feature-set stability verification.

Dependencies:
    - shap
    - lightgbm
    - pandas
    - numpy
    - scikit-learn
    - rkit (project specific)
"""

import os
import sys
import json
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set

import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
from sklearn.metrics import mean_squared_error, r2_score

# Project internal imports
from utils.logging_config import get_logger, set_log_level
from utils.config import load_hyperparameters
from data.loader import iterate_smiles
from data.feature_clustering import cluster_correlated_features

# Ensure project root is in path if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Logger setup
logger = get_logger(__name__)
set_log_level(logging.INFO)

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"
DESCRIPTORS_PATH = PROCESSED_DIR / "descriptors.parquet"
MODEL_PATH = PROCESSED_DIR / "model.pkl"
SHAP_VALUES_PATH = ANALYSIS_DIR / "shap_values.npy"
SHAP_SUMMARY_PLOT_PATH = ANALYSIS_DIR / "shap_summary.png"
FEATURE_REPORT_PATH = ANALYSIS_DIR / "feature_importance_report.json"
CLUSTER_REPORT_PATH = ANALYSIS_DIR / "cluster_report.json"
STABILITY_REPORT_PATH = ANALYSIS_DIR / "stability_report.json"

# Ensure output directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)


def load_model_and_data() -> Tuple[lgb.LGBMRegressor, pd.DataFrame, pd.Series]:
    """
    Loads the trained model and the processed descriptor data.

    Returns:
        Tuple of (model, features_df, target_series)

    Raises:
        FileNotFoundError: If model or data files are missing.
        ValueError: If data structures are invalid.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}. Run T026 first.")
    if not DESCRIPTORS_PATH.exists():
        raise FileNotFoundError(f"Descriptors file not found: {DESCRIPTORS_PATH}. Run T018 first.")

    logger.info(f"Loading model from {MODEL_PATH}")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loading descriptors from {DESCRIPTORS_PATH}")
    df = pd.read_parquet(DESCRIPTORS_PATH)

    # Assume target column is 'target' or 'dipole' based on typical pipeline
    # Check common names
    target_col = None
    for col in ['target', 'dipole', 'dipole_moment']:
        if col in df.columns:
            target_col = col
            break

    if target_col is None:
        raise ValueError(f"Could not identify target column in {DESCRIPTORS_PATH}. Columns: {df.columns.tolist()}")

    features = df.drop(columns=[target_col])
    target = df[target_col]

    logger.info(f"Loaded {features.shape[0]} samples with {features.shape[1]} features.")
    return model, features, target


def compute_shap_values(model: lgb.LGBMRegressor, features: pd.DataFrame, 
                        sample_size: int = 5000) -> np.ndarray:
    """
    Computes SHAP values for the model.
    
    Uses a background dataset for explanation if the dataset is large, 
    otherwise computes on the full set.

    Args:
        model: Trained LightGBM model.
        features: Feature DataFrame.
        sample_size: Max number of samples to use for SHAP background.

    Returns:
        numpy array of SHAP values (samples x features).
    """
    logger.info("Computing SHAP values...")
    
    # LightGBM SHAP explainer
    explainer = shap.TreeExplainer(model)
    
    # If dataset is large, sample for background to save memory
    if len(features) > sample_size:
        logger.info(f"Dataset too large ({len(features)}). Using {sample_size} samples for background.")
        background = shap.sample(features, sample_size)
        shap_values = explainer.shap_values(background)
    else:
        shap_values = explainer.shap_values(features)

    # Handle case where shap_values might be a list (for multi-output, though regression is single)
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    logger.info(f"SHAP values computed. Shape: {shap_values.shape}")
    return shap_values


def get_cluster_aware_importance(shap_values: np.ndarray, feature_names: List[str], 
                                 correlation_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Aggregates SHAP importance based on feature clusters derived from correlation.
    
    This function groups correlated features (|r| > threshold) and reports 
    the aggregate importance of the cluster, satisfying the "Cluster-Aware" requirement.

    Args:
        shap_values: Array of SHAP values.
        feature_names: List of feature names.
        correlation_threshold: Threshold for clustering.

    Returns:
        Dict containing cluster assignments and aggregated importance.
    """
    logger.info("Computing cluster-aware importance...")
    
    # Convert SHAP values to DataFrame for correlation analysis if needed, 
    # but we use the absolute mean SHAP value as importance metric per feature.
    importance = np.abs(shap_values).mean(axis=0)
    
    # We need the actual feature matrix to compute correlations for clustering
    # Re-load or assume we can access the original data. 
    # Since this function is called after load_model_and_data, we might need to pass features.
    # However, for this specific function signature, we rely on the fact that 
    # clustering logic is in feature_clustering.py. 
    # We will re-read the parquet to get the feature matrix for correlation.
    
    if not DESCRIPTORS_PATH.exists():
        raise FileNotFoundError("Cannot compute clusters: descriptors file missing.")
    
    df = pd.read_parquet(DESCRIPTORS_PATH)
    # Drop target if present
    if 'target' in df.columns:
        df = df.drop(columns=['target'])
    elif 'dipole' in df.columns:
        df = df.drop(columns=['dipole'])
    
    # Ensure column order matches shap_values
    df = df[feature_names]

    # Use existing clustering utility
    # cluster_correlated_features returns a dict mapping feature -> cluster_id
    clusters = cluster_correlated_features(df, threshold=correlation_threshold)
    
    # Aggregate importance by cluster
    cluster_importance: Dict[str, float] = {}
    for feature, cluster_id in clusters.items():
        if cluster_id not in cluster_importance:
            cluster_importance[cluster_id] = 0.0
        # Map feature name to index
        idx = feature_names.index(feature)
        cluster_importance[cluster_id] += importance[idx]

    # Sort clusters by importance
    sorted_clusters = sorted(cluster_importance.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "clusters": clusters,
        "cluster_importance": dict(sorted_clusters),
        "feature_importance": {name: float(val) for name, val in zip(feature_names, importance)}
    }


def generate_shap_summary_plot(shap_values: np.ndarray, features: pd.DataFrame, 
                               output_path: Path):
    """
    Generates and saves the SHAP summary plot.
    """
    logger.info(f"Generating SHAP summary plot: {output_path}")
    shap.summary_plot(shap_values, features, plot_type="bar", show=False, 
                      max_display=30, output_fname=str(output_path))
    # shap.summary_plot with plot_type='bar' saves directly if output_fname is provided in some versions,
    # but for compatibility we use matplotlib if needed. The function above tries to save.
    # If shap version is older, it might not support output_fname directly for bar.
    # Fallback:
    if not output_path.exists():
        import matplotlib.pyplot as plt
        shap.summary_plot(shap_values, features, plot_type="bar", show=False, max_display=30)
        plt.savefig(output_path, dpi=150)
        plt.close()
    logger.info(f"Summary plot saved to {output_path}")


def save_shap_values(shap_values: np.ndarray, output_path: Path):
    """
    Saves SHAP values to disk.
    """
    logger.info(f"Saving SHAP values to {output_path}")
    np.save(output_path, shap_values)
    logger.info("SHAP values saved.")


def generate_feature_report(importance_data: Dict[str, Any], output_path: Path):
    """
    Generates a JSON report of feature importance and clusters.
    """
    logger.info(f"Generating feature report: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(importance_data, f, indent=2, default=str)
    logger.info("Feature report saved.")


def run_cluster_aware_shap_analysis() -> Dict[str, Any]:
    """
    Orchestrates the full Cluster-Aware SHAP analysis pipeline.
    1. Load model and data.
    2. Compute SHAP values.
    3. Compute cluster-aware importance.
    4. Generate plots and reports.
    5. Save artifacts.
    """
    logger.info("Starting Cluster-Aware SHAP Analysis (T032)...")
    
    # 1. Load
    model, features, target = load_model_and_data()
    
    # 2. Compute SHAP
    shap_values = compute_shap_values(model, features)
    
    # 3. Save SHAP values
    save_shap_values(shap_values, SHAP_VALUES_PATH)
    
    # 4. Generate Plot
    generate_shap_summary_plot(shap_values, features, SHAP_SUMMARY_PLOT_PATH)
    
    # 5. Cluster Aware Importance
    feature_names = features.columns.tolist()
    cluster_data = get_cluster_aware_importance(shap_values, feature_names)
    
    # 6. Save Reports
    generate_feature_report(cluster_data, FEATURE_REPORT_PATH)
    
    # Save cluster details separately
    with open(CLUSTER_REPORT_PATH, 'w') as f:
        json.dump(cluster_data['clusters'], f, indent=2)
    
    logger.info("Cluster-Aware SHAP Analysis completed successfully.")
    return {
        "shap_values_path": str(SHAP_VALUES_PATH),
        "summary_plot_path": str(SHAP_SUMMARY_PLOT_PATH),
        "feature_report_path": str(FEATURE_REPORT_PATH),
        "cluster_report_path": str(CLUSTER_REPORT_PATH)
    }


def run_two_stage_bootstrap_shap(n_iterations: int = 10) -> List[Dict[str, Any]]:
    """
    Performs two-stage bootstrap: resample SHAP values without re-training.
    This is a fast approximation to check stability of the SHAP values themselves.
    
    Args:
        n_iterations: Number of bootstrap iterations.
        
    Returns:
        List of dictionaries containing top features for each iteration.
    """
    logger.info(f"Starting Two-Stage Bootstrap (SHAP-only) with {n_iterations} iterations...")
    model, features, target = load_model_and_data()
    shap_values = compute_shap_values(model, features)
    
    results = []
    for i in range(n_iterations):
        # Resample SHAP values (rows) with replacement
        indices = np.random.choice(shap_values.shape[0], size=shap_values.shape[0], replace=True)
        resampled_shap = shap_values[indices]
        
        # Compute mean absolute importance
        importance = np.abs(resampled_shap).mean(axis=0)
        top_indices = np.argsort(importance)[::-1][:10]
        
        results.append({
            "iteration": i,
            "top_features": [features.columns[j] for j in top_indices],
            "top_values": importance[top_indices].tolist()
        })
        
        if (i + 1) % 5 == 0:
            logger.info(f"  Bootstrap iteration {i+1}/{n_iterations} completed.")
    
    return results


def run_full_dataset_bootstrap(n_iterations: int = 5, sample_fraction: float = 0.8) -> List[Dict[str, Any]]:
    """
    Performs full dataset bootstrap: resample data, re-train model, compute SHAP.
    This verifies feature-set stability as per spec SC-003.
    
    Args:
        n_iterations: Number of bootstrap iterations.
        sample_fraction: Fraction of data to use in each iteration.
        
    Returns:
        List of dictionaries containing top features and model metrics for each iteration.
    """
    logger.info(f"Starting Full Dataset Bootstrap with {n_iterations} iterations...")
    
    model_base, features, target = load_model_and_data()
    feature_names = features.columns.tolist()
    
    results = []
    
    # Hyperparameters from config
    hyperparams = load_hyperparameters()
    lgb_params = hyperparams.get('lightgbm', {})
    
    # Default parameters if not in config
    default_params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'verbose': -1,
        'n_estimators': 100,
        'random_state': 42
    }
    lgb_params.update(default_params)
    
    for i in range(n_iterations):
        logger.info(f"  Bootstrap iteration {i+1}/{n_iterations}...")
        
        # 1. Resample data
        indices = np.random.choice(features.shape[0], size=int(features.shape[0] * sample_fraction), replace=True)
        X_boot = features.iloc[indices]
        y_boot = target.iloc[indices]
        
        # 2. Train model
        # Use LightGBM directly
        train_data = lgb.Dataset(X_boot, label=y_boot)
        model_boot = lgb.train(lgb_params, train_data, num_boost_round=lgb_params.get('n_estimators', 100))
        
        # 3. Compute SHAP
        # Use a subset for SHAP to keep it fast
        shap_subset = X_boot.sample(n=min(1000, len(X_boot)), random_state=42)
        explainer = shap.TreeExplainer(model_boot)
        shap_vals = explainer.shap_values(shap_subset)
        
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[0]
            
        # 4. Extract top features
        importance = np.abs(shap_vals).mean(axis=0)
        top_indices = np.argsort(importance)[::-1][:10]
        
        results.append({
            "iteration": i,
            "top_features": [feature_names[j] for j in top_indices],
            "model_r2": float(r2_score(y_boot, model_boot.predict(X_boot))),
            "model_rmse": float(np.sqrt(mean_squared_error(y_boot, model_boot.predict(X_boot))))
        })
        
        gc.collect()
        
    return results


def main():
    """
    Entry point for the interpretation script.
    Runs the full Cluster-Aware SHAP analysis.
    """
    try:
        # Check prerequisites
        if not DESCRIPTORS_PATH.exists():
            logger.error(f"Prerequisite failed: {DESCRIPTORS_PATH} not found. Run T018/T019 first.")
            sys.exit(1)
        if not MODEL_PATH.exists():
            logger.error(f"Prerequisite failed: {MODEL_PATH} not found. Run T026 first.")
            sys.exit(1)

        # Run main analysis
        artifacts = run_cluster_aware_shap_analysis()
        
        # Run bootstrap analyses if requested (optional for this specific task T032, 
        # but T033a/b are separate tasks. T032 focuses on the core analysis.)
        # We will log that they can be run but don't block on them for T032 completion.
        logger.info("Core Cluster-Aware SHAP Analysis (T032) completed.")
        logger.info(f"Artifacts saved to: {artifacts}")
        
        # Save a summary JSON of the run
        run_summary = {
            "task": "T032",
            "status": "completed",
            "artifacts": artifacts
        }
        with open(ANALYSIS_DIR / "t032_run_summary.json", 'w') as f:
            json.dump(run_summary, f, indent=2)

    except Exception as e:
        logger.error(f"Error during T032 execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()