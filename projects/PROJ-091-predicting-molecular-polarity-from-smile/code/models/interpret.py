import os
import sys
import json
import logging
import pickle
import gc
from pathlib import Path
import pandas as pd
import numpy as np
import shap
import lightgbm as lgb
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_model_and_data(model_path: Path, data_path: Path):
    """Load model and data for interpretation."""
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    df = pd.read_parquet(data_path)
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    X = df[feature_cols].values
    return model, X, df

def compute_shap_values(model, X):
    """Compute SHAP values."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    return shap_values

def load_clusters_from_report(cluster_map_path: Path) -> dict:
    """Load cluster mapping from CSV."""
    if not cluster_map_path.exists():
        logger.warning(f"Cluster map not found: {cluster_map_path}")
        return {}
    df = pd.read_csv(cluster_map_path)
    clusters = {}
    for _, row in df.iterrows():
        clusters[row['feature_id']] = row['cluster_id']
    return clusters

def get_cluster_aware_importance(shap_values, clusters, feature_names):
    """Aggregate SHAP values by cluster."""
    cluster_importance = {}
    for i, fname in enumerate(feature_names):
        if fname in clusters:
            cid = clusters[fname]
            if cid not in cluster_importance:
                cluster_importance[cid] = []
            cluster_importance[cid].append(np.abs(shap_values[:, i]).mean())

    # Average within clusters
    result = {}
    for cid, vals in cluster_importance.items():
        result[cid] = np.mean(vals)
    return result

def generate_shap_summary_plot(shap_values, feature_names, output_path: Path):
    """Generate SHAP summary plot."""
    plt = shap.summary_plot(shap_values, feature_names=feature_names, show=False)
    plt.savefig(output_path)
    logger.info(f"SHAP summary plot saved to {output_path}")

def save_shap_values(shap_values, feature_names, output_path: Path):
    """Save SHAP values to file."""
    df = pd.DataFrame(shap_values, columns=feature_names)
    df.to_parquet(output_path)
    logger.info(f"SHAP values saved to {output_path}")

def generate_feature_report(importance_dict, output_path: Path):
    """Generate feature importance report."""
    df = pd.DataFrame(list(importance_dict.items()), columns=['cluster_id', 'importance'])
    df = df.sort_values('importance', ascending=False)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature report saved to {output_path}")

def run_two_stage_bootstrap_shap(shap_values, n_iterations=100):
    """
    Two-stage bootstrap: resample SHAP values directly.
    """
    n_samples = shap_values.shape[0]
    bootstrap_results = []

    for _ in range(n_iterations):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resampled = shap_values[indices]
        bootstrap_results.append(resampled)

    return bootstrap_results

def run_cluster_aware_shap_analysis(model_path, data_path, cluster_map_path, output_dir):
    """Main cluster-aware SHAP analysis."""
    model, X, df = load_model_and_data(model_path, data_path)
    feature_names = [c for c in df.columns if c not in ['smiles', 'target']]
    shap_values = compute_shap_values(model, X)

    clusters = load_clusters_from_report(cluster_map_path)
    importance = get_cluster_aware_importance(shap_values, clusters, feature_names)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_shap_summary_plot(shap_values, feature_names, output_dir / "shap_summary.png")
    save_shap_values(shap_values, feature_names, output_dir / "shap_values.parquet")
    generate_feature_report(importance, output_dir / "cluster_importance.csv")

    logger.info("Cluster-aware SHAP analysis complete.")

def run_full_dataset_bootstrap(shap_values, n_iterations=100):
    """Run full dataset bootstrap for stability analysis."""
    return run_two_stage_bootstrap_shap(shap_values, n_iterations)

def main():
    """Main entry point."""
    model_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "model.pkl"
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "descriptors.parquet"
    cluster_map_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "cluster_map.csv"
    output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "analysis"

    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        sys.exit(1)

    run_cluster_aware_shap_analysis(model_path, data_path, cluster_map_path, output_dir)

if __name__ == "__main__":
    main()
