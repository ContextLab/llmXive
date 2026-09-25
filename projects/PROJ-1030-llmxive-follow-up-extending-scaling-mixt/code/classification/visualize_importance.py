import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pickle
import numpy as np

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/CI environments
import matplotlib.pyplot as plt
import shap

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from classification.feature_importance import (
    load_filtered_data_for_importance,
    load_baseline_distribution,
    load_classifier,
    compute_shap_values,
    compute_permutation_importance,
    analyze_importance_against_baseline
)
from utils.logging_config import get_logger

logger = get_logger(__name__)

def generate_importance_plot(shap_values, feature_names, output_path, baseline_stats=None):
    """
    Generate a bar plot of mean absolute SHAP values (feature importance).
    If baseline_stats are provided, highlight features that exceed baseline noise.
    """
    if shap_values is None or len(shap_values) == 0:
        logger.warning("No SHAP values provided for plotting.")
        return

    # Aggregate SHAP values (mean absolute)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    indices = np.argsort(mean_abs_shap)[::-1]

    # Limit to top 20 features for readability
    top_n = min(20, len(indices))
    top_indices = indices[:top_n]
    top_features = [feature_names[i] for i in top_indices]
    top_values = mean_abs_shap[top_indices]

    plt.figure(figsize=(10, 8))
    y_pos = np.arange(len(top_features))

    plt.barh(y_pos, top_values, align='center', color='steelblue')
    plt.yticks(y_pos, top_features)
    plt.xlabel('Mean |SHAP Value|')
    plt.title('Feature Importance (Top 20)')

    if baseline_stats:
        # Highlight features significantly above baseline noise (e.g., > 2*std)
        if 'std' in baseline_stats:
            threshold = 2 * baseline_stats['std']
            # Create a mask for features above threshold
            # Note: This is a simplified check assuming feature indices align
            # In a robust implementation, we'd map feature names to baseline stats explicitly
            for i, val in enumerate(top_values):
                if val > threshold:
                    plt.gca().patches[i].set_color('crimson')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved feature importance plot to {output_path}")

def generate_beeswarm_plot(shap_values, feature_names, output_path):
    """
    Generate a SHAP beeswarm plot for detailed distribution analysis.
    """
    if shap_values is None or len(shap_values) == 0:
        logger.warning("No SHAP values provided for beeswarm plot.")
        return

    # Create a dummy feature matrix if not available for the plot
    # SHAP beeswarm expects a feature matrix X to map values to colors
    # We will use the first 1000 samples of the filtered data for visualization
    try:
        X, _, _, _ = load_filtered_data_for_importance()
        if X.shape[0] > 1000:
            sample_indices = np.random.choice(X.shape[0], 1000, replace=False)
            X_plot = X[sample_indices]
        else:
            X_plot = X
    except Exception as e:
        logger.warning(f"Could not load data for beeswarm plot background: {e}")
        X_plot = None

    plt.figure(figsize=(10, 8))
    if X_plot is not None:
        shap.summary_plot(shap_values, X_plot, feature_names=feature_names, show=False)
    else:
        shap.summary_plot(shap_values, feature_names=feature_names, show=False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved SHAP beeswarm plot to {output_path}")

def run_visualization_pipeline():
    """
    Main entry point for T035: Generate visualizations and ensure metrics.json is up to date.
    """
    # Paths
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = processed_dir / "metrics.json"
    importance_plot_path = processed_dir / "feature_importance_bar.png"
    beeswarm_plot_path = processed_dir / "feature_importance_beeswarm.png"

    # 1. Load Data and Model
    logger.info("Loading filtered data for importance analysis...")
    try:
        X, y, feature_names, _ = load_filtered_data_for_importance()
        classifier = load_classifier()
        baseline_stats = load_baseline_distribution()
    except Exception as e:
        logger.error(f"Failed to load data or model: {e}")
        raise

    # 2. Compute SHAP Values
    logger.info("Computing SHAP values...")
    shap_values = compute_shap_values(classifier, X)
    
    # 3. Compute Permutation Importance (optional, for comparison)
    logger.info("Computing permutation importance...")
    perm_importance = compute_permutation_importance(classifier, X, y)

    # 4. Analyze against baseline
    logger.info("Analyzing importance against baseline...")
    analysis_results = analyze_importance_against_baseline(
        mean_shap=np.abs(shap_values).mean(axis=0),
        feature_names=feature_names,
        baseline_stats=baseline_stats
    )

    # 5. Generate Visualizations
    logger.info("Generating visualizations...")
    generate_importance_plot(
        shap_values, 
        feature_names, 
        str(importance_plot_path), 
        baseline_stats=baseline_stats
    )
    
    generate_beeswarm_plot(
        shap_values,
        feature_names,
        str(beeswarm_plot_path)
    )

    # 6. Ensure metrics.json exists and is updated
    # The metrics are primarily generated by T032 (compute_metrics.py), 
    # but T035 ensures the file exists and is valid as per the task description.
    if metrics_path.exists():
        logger.info(f"Found existing metrics file at {metrics_path}. Verifying content.")
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
        
        # Ensure required keys exist, add analysis summary if missing
        if 'feature_importance_summary' not in metrics_data:
            metrics_data['feature_importance_summary'] = {
                "top_features": [feature_names[i] for i in np.argsort(np.abs(shap_values).mean(axis=0))[::-1][:10]],
                "analysis_method": "SHAP",
                "plot_paths": {
                    "bar_plot": str(importance_plot_path.relative_to(project_root)),
                    "beeswarm_plot": str(beeswarm_plot_path.relative_to(project_root))
                }
            }
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        logger.info("Updated metrics.json with feature importance summary.")
    else:
        logger.warning(f"Metrics file {metrics_path} not found. Creating a minimal one.")
        # This case should ideally be caught by T032, but we handle it here for robustness
        metrics_data = {
            "status": "incomplete",
            "note": "Metrics file missing from previous step. Created by T035 visualization script.",
            "feature_importance_summary": {
                "top_features": [feature_names[i] for i in np.argsort(np.abs(shap_values).mean(axis=0))[::-1][:10]],
                "plot_paths": {
                    "bar_plot": str(importance_plot_path.relative_to(project_root)),
                    "beeswarm_plot": str(beeswarm_plot_path.relative_to(project_root))
                }
            }
        }
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)

    logger.info("T035 Visualization task completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Generate feature importance visualizations for T035.")
    parser.parse_args()
    run_visualization_pipeline()

if __name__ == "__main__":
    main()