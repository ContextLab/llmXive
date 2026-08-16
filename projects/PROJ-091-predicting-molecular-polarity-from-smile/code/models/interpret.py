import os
import sys
import json
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
import shap
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_model_and_data(model_path: Path, data_path: Path) -> tuple:
    """Load model and data."""
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    df = pd.read_parquet(data_path)
    feature_cols = [c for c in df.columns if c not in ['smiles', 'target']]
    X = df[feature_cols]
    return model, X

def compute_shap_values(model, X: pd.DataFrame) -> shap_values:
    """Compute SHAP values."""
    explainer = shap.TreeExplainer(model)
    return explainer(X)

def load_clusters_from_report(cluster_path: Path) -> List[List[str]]:
    """Load clusters from report."""
    with open(cluster_path, "r") as f:
        data = json.load(f)
    return data.get("clusters", [])

def get_cluster_aware_importance(shap_values, clusters: List[List[str]]) -> Dict[str, float]:
    """Compute cluster-aware importance."""
    importance = {}
    for i, cluster in enumerate(clusters):
        indices = [j for j, col in enumerate(shap_values.feature_names) if col in cluster]
        if indices:
            importance[f"cluster_{i}"] = float(np.mean(np.abs(shap_values.values[:, indices])))
    return importance

def generate_shap_summary_plot(shap_values, X: pd.DataFrame, output_path: Path) -> None:
    """Generate SHAP summary plot."""
    shap.summary_plot(shap_values, X, show=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.savefig(output_path)
    plt.close()

def save_shap_values(shap_values: shap_values, output_path: Path) -> None:
    """Save SHAP values."""
    with open(output_path, "wb") as f:
        pickle.dump(shap_values, f)

def generate_feature_report(importance: Dict[str, float], output_path: Path) -> None:
    """Generate feature importance report."""
    with open(output_path, "w") as f:
        json.dump(importance, f, indent=2)

def run_two_stage_bootstrap_shap(shap_values, n_samples: int = 10) -> List[Dict[str, Any]]:
    """Run two-stage bootstrap on SHAP values."""
    results = []
    for _ in range(n_samples):
        indices = np.random.choice(len(shap_values.values), size=len(shap_values.values), replace=True)
        sampled = shap_values.values[indices]
        top_features = np.argsort(np.abs(sampled).mean(axis=0))[-10:]
        results.append({"top_features": top_features.tolist()})
    return results

def run_cluster_aware_shap_analysis(model_path: Path, data_path: Path, cluster_path: Path, output_dir: Path) -> None:
    """Run full cluster-aware SHAP analysis."""
    model, X = load_model_and_data(model_path, data_path)
    shap_values = compute_shap_values(model, X)
    clusters = load_clusters_from_report(cluster_path)
    
    importance = get_cluster_aware_importance(shap_values, clusters)
    generate_feature_report(importance, output_dir / "cluster_importance.json")
    generate_shap_summary_plot(shap_values, X, output_dir / "shap_summary.png")
    save_shap_values(shap_values, output_dir / "shap_values.pkl")

def run_full_dataset_bootstrap(model_path: Path, data_path: Path, cluster_path: Path, output_path: Path) -> None:
    """Run bootstrap analysis on full dataset."""
    model, X = load_model_and_data(model_path, data_path)
    shap_values = compute_shap_values(model, X)
    bootstrap_results = run_two_stage_bootstrap_shap(shap_values)
    with open(output_path, "w") as f:
        json.dump(bootstrap_results, f, indent=2)

def main() -> None:
    """Main entry point."""
    model_path = Path("data/processed/model.pkl")
    data_path = Path("data/processed/descriptors.parquet")
    cluster_path = Path("data/processed/analysis/feature_clusters.json")
    output_dir = Path("data/processed/analysis")
    
    run_cluster_aware_shap_analysis(model_path, data_path, cluster_path, output_dir)
    run_full_dataset_bootstrap(model_path, data_path, cluster_path, output_dir / "bootstrap_results.json")

if __name__ == "__main__":
    main()
