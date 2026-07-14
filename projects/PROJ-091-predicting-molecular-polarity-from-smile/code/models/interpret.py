"""
Module for Cluster-Aware SHAP analysis and feature importance interpretation.

This module implements SHAP (SHapley Additive exPlanations) analysis for the
molecular polarity prediction model. It includes cluster-aware analysis that
groups correlated features to provide more interpretable importance rankings.

The analysis reads from:
- data/processed/descriptors.parquet: Feature matrix and target
- data/processed/model.pkl: Trained LightGBM model

Outputs are saved to:
- data/processed/analysis/shap_values.npy: Raw SHAP values
- data/processed/analysis/shap_summary.png: Summary plot
- data/processed/analysis/feature_importance.json: Importance rankings
- data/processed/analysis/cluster_analysis.json: Cluster-based importance
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set

import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, set_log_level
from utils.validators import assert_no_3d_calls

# Initialize logger
logger = get_logger(__name__)
set_log_level(logging.INFO)

def load_model_and_data(
    model_path: Path,
    data_path: Path
) -> Tuple[lgb.Booster, pd.DataFrame, pd.Series]:
    """
    Load the trained model and descriptor data.

    Args:
        model_path: Path to the pickled LightGBM model
        data_path: Path to the parquet file with descriptors

    Returns:
        Tuple of (model, feature_matrix, target_series)

    Raises:
        FileNotFoundError: If model or data files don't exist
        ValueError: If data doesn't contain required columns
    """
    # Assert no 3D calls in this context (validation only)
    assert_no_3d_calls()

    # Load model
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loaded model from {model_path}")

    # Load data
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_parquet(data_path)

    # Ensure target column exists (should be 'dipole_moment' based on QM9)
    target_col = 'dipole_moment'
    if target_col not in df.columns:
        # Try to find any column that might be the target
        target_candidates = [c for c in df.columns if 'dipole' in c.lower() or 'target' in c.lower()]
        if target_candidates:
            target_col = target_candidates[0]
            logger.warning(f"Using '{target_col}' as target column instead of 'dipole_moment'")
        else:
            raise ValueError(f"Cannot find target column in {data_path}. Available columns: {df.columns.tolist()}")

    # Separate features and target
    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols]
    y = df[target_col]

    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
    logger.info(f"Target column: {target_col}")

    return model, X, y

def compute_shap_values(
    model: lgb.Booster,
    X: pd.DataFrame,
    max_samples: int = 1000
) -> Tuple[np.ndarray, shap.Explainer]:
    """
    Compute SHAP values for the model.

    Uses TreeExplainer for LightGBM models. Samples data if dataset is too large
    to avoid excessive memory usage.

    Args:
        model: Trained LightGBM model
        X: Feature DataFrame
        max_samples: Maximum number of samples to use for SHAP computation

    Returns:
        Tuple of (shap_values_array, explainer)
    """
    logger.info(f"Computing SHAP values for {min(len(X), max_samples)} samples")

    # Sample if necessary
    if len(X) > max_samples:
        indices = np.random.choice(len(X), max_samples, replace=False)
        X_sample = X.iloc[indices]
        logger.info(f"Sampled {max_samples} from {len(X)} samples")
    else:
        X_sample = X

    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)

    # Compute SHAP values
    shap_values = explainer.shap_values(X_sample)

    # Handle multi-output case (should be single output for regression)
    if isinstance(shap_values, list):
        # For multi-output, take the first (or average if needed)
        shap_values = np.array(shap_values[0]) if len(shap_values) > 0 else np.array(shap_values)
    else:
        shap_values = np.array(shap_values)

    logger.info(f"SHAP values shape: {shap_values.shape}")

    return shap_values, explainer

def get_cluster_aware_importance(
    shap_values: np.ndarray,
    feature_names: List[str],
    correlation_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Compute feature importance with cluster awareness.

    Groups correlated features into clusters and reports:
    - Global SHAP importance (mean absolute SHAP value)
    - Cluster-level importance (sum of absolute SHAP values in cluster)
    - Representative feature per cluster

    Args:
        shap_values: 2D array of SHAP values (n_samples, n_features)
        feature_names: List of feature names
        correlation_threshold: Threshold for clustering correlated features

    Returns:
        Dictionary with importance rankings and cluster information
    """
    n_features = len(feature_names)

    # Compute mean absolute SHAP importance
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    importance_ranking = sorted(
        [(feature_names[i], float(mean_abs_shap[i])) for i in range(n_features)],
        key=lambda x: x[1],
        reverse=True
    )

    # Compute correlation matrix for clustering
    # Use absolute correlation for clustering
    feature_matrix = pd.DataFrame(shap_values, columns=feature_names)
    corr_matrix = feature_matrix.corr().abs()

    # Identify clusters of correlated features
    visited = set()
    clusters = []

    for i, feat_i in enumerate(feature_names):
        if feat_i in visited:
            continue

        cluster = {feat_i}
        visited.add(feat_i)

        for j, feat_j in enumerate(feature_names):
            if i == j or feat_j in visited:
                continue

            if corr_matrix.loc[feat_i, feat_j] >= correlation_threshold:
                cluster.add(feat_j)
                visited.add(feat_j)

        clusters.append(sorted(cluster))

    # Compute cluster-level importance
    cluster_importance = []
    for cluster in clusters:
        cluster_indices = [feature_names.index(f) for f in cluster]
        cluster_shap_sum = np.sum(mean_abs_shap[cluster_indices])
        # Representative feature: highest individual importance in cluster
        rep_feat = max(cluster, key=lambda f: mean_abs_shap[feature_names.index(f)])
        cluster_importance.append({
            "cluster_id": len(cluster_importance),
            "features": cluster,
            "cluster_importance": float(cluster_shap_sum),
            "representative_feature": rep_feat,
            "representative_importance": float(mean_abs_shap[feature_names.index(rep_feat)])
        })

    # Sort clusters by importance
    cluster_importance.sort(key=lambda x: x["cluster_importance"], reverse=True)

    return {
        "global_importance": importance_ranking,
        "clusters": cluster_importance,
        "n_clusters": len(clusters),
        "n_features": n_features,
        "correlation_threshold": correlation_threshold
    }

def generate_shap_summary_plot(
    shap_values: np.ndarray,
    X: pd.DataFrame,
    output_path: Path,
    max_features: int = 20
) -> None:
    """
    Generate and save SHAP summary plot.

    Args:
        shap_values: SHAP values array
        X: Feature DataFrame (used for feature names)
        output_path: Path to save the plot
        max_features: Maximum number of features to show
    """
    logger.info(f"Generating SHAP summary plot -> {output_path}")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create plot
    shap.summary_plot(
        shap_values,
        X,
        plot_type="bar",
        max_display=max_features,
        show=False
    )

    # Save figure
    import matplotlib.pyplot as plt
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"SHAP summary plot saved to {output_path}")

def save_shap_values(
    shap_values: np.ndarray,
    feature_names: List[str],
    output_path: Path
) -> None:
    """
    Save SHAP values and metadata to disk.

    Args:
        shap_values: SHAP values array
        feature_names: List of feature names
        output_path: Path to save the numpy file
    """
    logger.info(f"Saving SHAP values to {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as numpy with metadata
    np.save(
        output_path,
        shap_values,
        allow_pickle=False
    )

    # Save metadata separately
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump({
            "feature_names": feature_names,
            "shap_shape": list(shap_values.shape)
        }, f, indent=2)

    logger.info(f"SHAP values saved ({output_path})")

def run_cluster_aware_shap_analysis(
    model_path: Path,
    data_path: Path,
    output_dir: Path,
    max_samples: int = 1000,
    correlation_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Run full cluster-aware SHAP analysis pipeline.

    This is the main entry point that orchestrates:
    1. Loading model and data
    2. Computing SHAP values
    3. Generating cluster-aware importance rankings
    4. Saving all artifacts

    Args:
        model_path: Path to trained model pickle
        data_path: Path to descriptors parquet
        output_dir: Directory to save analysis artifacts
        max_samples: Max samples for SHAP computation
        correlation_threshold: Threshold for feature clustering

    Returns:
        Dictionary containing analysis results and paths
    """
    logger.info("=" * 60)
    logger.info("Starting Cluster-Aware SHAP Analysis")
    logger.info("=" * 60)

    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data and model
    model, X, y = load_model_and_data(model_path, data_path)

    # Compute SHAP values
    shap_values, explainer = compute_shap_values(model, X, max_samples)

    # Get feature names
    feature_names = X.columns.tolist()

    # Generate cluster-aware importance
    importance_results = get_cluster_aware_importance(
        shap_values,
        feature_names,
        correlation_threshold
    )

    # Save artifacts
    shap_values_path = output_dir / "shap_values.npy"
    save_shap_values(shap_values, feature_names, shap_values_path)

    summary_plot_path = output_dir / "shap_summary.png"
    generate_shap_summary_plot(shap_values, X, summary_plot_path)

    importance_path = output_dir / "feature_importance.json"
    with open(importance_path, 'w') as f:
        json.dump(importance_results, f, indent=2)

    # Save cluster analysis
    cluster_path = output_dir / "cluster_analysis.json"
    with open(cluster_path, 'w') as f:
        json.dump({
            "n_clusters": importance_results["n_clusters"],
            "clusters": importance_results["clusters"],
            "top_10_features": importance_results["global_importance"][:10]
        }, f, indent=2)

    # Log summary
    logger.info("=" * 60)
    logger.info("SHAP Analysis Complete")
    logger.info(f"  - Samples analyzed: {shap_values.shape[0]}")
    logger.info(f"  - Features: {len(feature_names)}")
    logger.info(f"  - Clusters identified: {importance_results['n_clusters']}")
    logger.info(f"  - Top feature: {importance_results['global_importance'][0][0]}")
    logger.info("=" * 60)

    return {
        "shap_values_path": str(shap_values_path),
        "summary_plot_path": str(summary_plot_path),
        "importance_path": str(importance_path),
        "cluster_path": str(cluster_path),
        "results": importance_results
    }

def main():
    """
    Main entry point for SHAP analysis.

    Reads configuration from environment or defaults:
    - MODEL_PATH: Path to trained model (default: data/processed/model.pkl)
    - DATA_PATH: Path to descriptors (default: data/processed/descriptors.parquet)
    - OUTPUT_DIR: Output directory (default: data/processed/analysis)
    """
    model_path = Path(os.getenv("MODEL_PATH", "data/processed/model.pkl"))
    data_path = Path(os.getenv("DATA_PATH", "data/processed/descriptors.parquet"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "data/processed/analysis"))

    # Resolve to project root if relative
    if not model_path.is_absolute():
        model_path = project_root / model_path
    if not data_path.is_absolute():
        data_path = project_root / data_path
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir

    logger.info(f"Model path: {model_path}")
    logger.info(f"Data path: {data_path}")
    logger.info(f"Output directory: {output_dir}")

    try:
        results = run_cluster_aware_shap_analysis(
            model_path=model_path,
            data_path=data_path,
            output_dir=output_dir,
            max_samples=1000,
            correlation_threshold=0.8
        )

        logger.info("Analysis completed successfully!")
        logger.info(f"Results saved to: {output_dir}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()