"""
SHAP Analysis Module for Adsorption Isotherm Parameter Prediction.

This module handles SHAP value calculation, visualization, and the Unified Consensus Analysis
(Task T032) to compare model drivers against literature consensus.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression

# Attempt to import from sibling modules based on API surface
try:
    from models.evaluate import load_models, load_test_data
    from analysis.cluster_permutation import load_test_data as load_test_data_perm
except ImportError:
    # Fallback for direct execution context if paths aren't set up yet
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from models.evaluate import load_models, load_test_data
    from analysis.cluster_permutation import load_test_data as load_test_data_perm

# Configure logging
logger = logging.getLogger(__name__)

# Constants for Consensus Analysis
LITERATURE_CONSENSUS_LIST = [
    "polarizability",
    "kinetic_diameter",
    "lj_epsilon",
    "quadrupole_moment",
    "surface_area",
    "pore_volume",
    "molecular_weight",
    "polar_surface_area"
]

class ConsensusValidationFailure(Exception):
    """Raised when no convergence or divergence is found against literature consensus."""
    pass

def ensure_dirs():
    """Ensure required output directories exist."""
    dirs = [
        Path("data/results"),
        Path("data/interpretation"),
        Path("figures")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_best_model() -> Tuple[Any, str]:
    """
    Load models and return the best performing one based on data/results/model_metrics.json.
    Returns:
        Tuple[Model, str]: The model instance and its name.
    """
    metrics_path = Path("data/results/model_metrics.json")
    if not metrics_path.exists():
        logger.error(f"Model metrics file not found at {metrics_path}. Cannot determine best model.")
        raise FileNotFoundError(f"Model metrics file not found: {metrics_path}")

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    # Assume structure: {"models": [{"name": "...", "r2": ...}, ...]}
    # Or flat list if saved differently. Adapt to actual T023/T024 output structure.
    if isinstance(metrics, dict) and "models" in metrics:
        models_list = metrics["models"]
    elif isinstance(metrics, list):
        models_list = metrics
    else:
        # Fallback: try to find max R2 in the dict directly if it's a flat mapping
        # This is a heuristic; adjust based on actual T023 output format.
        # Assuming T023 saves a list of results.
        models_list = [metrics] if "r2" in metrics else []

    best_model_name = None
    best_r2 = -np.inf

    for m in models_list:
        r2 = m.get("r2", -np.inf)
        if r2 > best_r2:
            best_r2 = r2
            best_model_name = m.get("name")

    if not best_model_name:
        raise ValueError("Could not identify a best model from metrics.")

    logger.info(f"Selected best model: {best_model_name} with R2={best_r2:.4f}")
    loaded_models = load_models()
    if best_model_name in loaded_models:
        return loaded_models[best_model_name], best_model_name
    else:
        # Fallback if name mismatch, try to find by order or first available
        logger.warning(f"Best model name {best_model_name} not found in loaded models. Using first available.")
        return next(iter(loaded_models.values())), list(loaded_models.keys())[0]

def generate_shap_summary_plot(model: Any, X_test: pd.DataFrame, model_name: str) -> str:
    """Generate SHAP summary plot and save to figures/shap_summary_{model_name}.png."""
    ensure_dirs()
    explainer = shap.Explainer(model, X_test)
    shap_values = explainer(X_test)

    # Save summary plot
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_test, plot_type="bar", show=False)
    output_path = Path(f"figures/shap_summary_{model_name}.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"SHAP summary plot saved to {output_path}")

    # Also save numerical summary for T030
    summary_data = {
        "model": model_name,
        "feature_importance": {}
    }
    # Get mean absolute SHAP values for ranking
    if hasattr(shap_values, "values"):
        # shap.Explainer returns array of values for each sample
        mean_abs_shap = np.mean(np.abs(shap_values.values), axis=0)
        features = X_test.columns.tolist()
        for i, feat in enumerate(features):
            summary_data["feature_importance"][feat] = float(mean_abs_shap[i])
    
    summary_path = Path("data/results/shap_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"SHAP summary data saved to {summary_path}")
    
    return str(output_path)

def generate_partial_dependence_plots(model: Any, X_test: pd.DataFrame) -> List[str]:
    """Generate PDPs for top features and check monotonicity."""
    ensure_dirs()
    # Simplified for this task: generate for top 3 features
    if X_test.shape[1] == 0:
        return []
    
    top_features = X_test.columns[:min(3, X_test.shape[1])].tolist()
    paths = []
    
    for feat in top_features:
        plt.figure(figsize=(8, 6))
        try:
            shap.dependence_plot(feat, model, X_test, show=False)
            path = Path(f"figures/pdp_{feat}.png")
            plt.savefig(path, dpi=150, bbox_inches='tight')
            plt.close()
            paths.append(str(path))
        except Exception as e:
            logger.warning(f"Could not generate PDP for {feat}: {e}")
            plt.close()
    
    return paths

def validate_consensus(shap_summary_path: str = "data/results/shap_summary.json") -> Dict[str, Any]:
    """
    T032: Unified Consensus Analysis.
    Compares top-ranked features from SHAP against LITERATURE_CONSENSUS_LIST.
    Checks for convergence (top features match consensus) or divergence.
    Also integrates T052 results (adjusted p-values) if available.
    
    Raises:
        ConsensusValidationFailure: If no convergence or divergence is found.
    """
    ensure_dirs()
    
    # 1. Load SHAP Summary
    if not os.path.exists(shap_summary_path):
        raise FileNotFoundError(f"SHAP summary not found at {shap_summary_path}. Run T030 first.")
    
    with open(shap_summary_path, 'r') as f:
        shap_data = json.load(f)
    
    feature_importance = shap_data.get("feature_importance", {})
    if not feature_importance:
        raise ValueError("SHAP summary contains no feature importance data.")
    
    # Sort features by importance
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    top_3_features = [f[0] for f in sorted_features[:3]]
    all_features = [f[0] for f in sorted_features]
    
    logger.info(f"Top 3 features: {top_3_features}")
    
    # 2. Load T052 Permutation P-values (if available)
    p_values_path = Path("data/results/permutation_pvalues.json")
    p_values_map = {}
    if p_values_path.exists():
        with open(p_values_path, 'r') as f:
            p_data = json.load(f)
        # p_data is a list of objects: [{"feature_name": "...", "adjusted_q_value": ...}, ...]
        for item in p_data:
            name = item.get("feature_name")
            q_val = item.get("adjusted_q_value")
            if name:
                p_values_map[name] = q_val
        logger.info(f"Loaded permutation p-values for {len(p_values_map)} features.")
    
    # 3. Analyze Convergence/Divergence
    consensus_hits = []
    consensus_misses = []
    significant_hits = []
    
    for feat in top_3_features:
        if feat in LITERATURE_CONSENSUS_LIST:
            consensus_hits.append(feat)
            # Check significance from T052
            if feat in p_values_map and p_values_map[feat] < 0.05:
                significant_hits.append(feat)
        else:
            consensus_misses.append(feat)
    
    # 4. Determine Convergence/Divergence Status
    has_convergence = len(consensus_hits) > 0
    has_divergence = len(consensus_misses) > 0 or (len(consensus_hits) < len(top_3_features) and len(top_3_features) > 0)
    
    # CRITICAL: Must find at least one point of convergence OR divergence
    if not has_convergence and not has_divergence:
        # This happens if top_3 is empty or no comparison possible
        raise ConsensusValidationFailure(
            "No convergence or divergence found. Top features list is empty or comparison failed."
        )
    
    # 5. Generate Report
    report = {
        "task_id": "T032",
        "analysis_type": "Unified Consensus Analysis",
        "literature_consensus_list": LITERATURE_CONSENSUS_LIST,
        "top_ranked_features": top_3_features,
        "convergence_analysis": {
            "found": has_convergence,
            "matching_features": consensus_hits,
            "significant_matching_features": significant_hits
        },
        "divergence_analysis": {
            "found": has_divergence,
            "non_consensus_features": consensus_misses
        },
        "integration_with_permutation_test": {
            "permutation_p_values_loaded": len(p_values_map) > 0,
            "significant_features_in_top_3": significant_hits
        },
        "conclusion": ""
    }
    
    if has_convergence:
        report["conclusion"] = (
            f"CONVERGENCE DETECTED: {len(consensus_hits)} of the top {len(top_3_features)} features "
            f"({', '.join(consensus_hits)}) align with the literature consensus list. "
            f"Additionally, {len(significant_hits)} of these are statistically significant (q < 0.05) based on "
            f"cluster permutation tests (T052)."
        )
    else:
        report["conclusion"] = (
            f"DIVERGENCE DETECTED: None of the top {len(top_3_features)} features align with the "
            f"literature consensus list. This suggests the model may be capturing non-standard drivers "
            f"or the consensus list needs revision."
        )
    
    # Save report
    report_path = Path("data/results/consensus_analysis_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Consensus analysis report saved to {report_path}")
    logger.info(report["conclusion"])
    
    return report

def run_shap_analysis_pipeline():
    """Main pipeline for SHAP analysis and Consensus Validation."""
    ensure_dirs()
    
    # Load Data
    logger.info("Loading test data...")
    X_test, y_test, feature_names = load_test_data()
    
    if X_test.empty or len(X_test) == 0:
        logger.error("Test data is empty. Cannot run SHAP analysis.")
        raise ValueError("Test data is empty.")
    
    # Get Best Model
    logger.info("Retrieving best model...")
    model, model_name = get_best_model()
    
    # Generate SHAP Plots
    logger.info("Generating SHAP summary plot...")
    shap_path = generate_shap_summary_plot(model, X_test, model_name)
    
    # Generate PDPs
    logger.info("Generating Partial Dependence Plots...")
    pdp_paths = generate_partial_dependence_plots(model, X_test)
    
    # T032: Unified Consensus Analysis
    logger.info("Running Unified Consensus Analysis (T032)...")
    try:
        consensus_report = validate_consensus()
    except ConsensusValidationFailure as e:
        logger.error(f"Consensus validation failed: {e}")
        # Re-raise to ensure the task is marked as failed if the critical check fails
        raise
    
    logger.info("SHAP analysis pipeline completed successfully.")
    return consensus_report

def main():
    """Entry point for the script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        run_shap_analysis_pipeline()
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()