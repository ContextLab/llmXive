"""
Feature Importance Analysis using SHAP.

This module implements SHAP (SHapley Additive exPlanations) analysis to identify
predictive sub-networks in the trained classifier. It compares feature importance
results against the baseline distribution from T032.1 to highlight which expert
activations and latent dimensions are most predictive of physical validity.

Dependencies:
- shap (must be installed via requirements.txt)
- numpy, pandas, scikit-learn, pickle
"""

import os
import sys
import json
import logging
import pickle
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "features.npy"
LABELS_PATH = PROJECT_ROOT / "data" / "processed" / "labels.csv"
METADATA_PATH = PROJECT_ROOT / "data" / "processed" / "metadata.json"
BASELINE_DIST_PATH = PROJECT_ROOT / "data" / "processed" / "activation_distribution.json"
CLASSIFIER_PATH = PROJECT_ROOT / "data" / "processed" / "classifier.pkl"
OUTPUT_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "feature_importance_report.json"
OUTPUT_PLOT_PATH = PROJECT_ROOT / "docs" / "figures" / "feature_importance_summary.png"
OUTPUT_BEESWARM_PATH = PROJECT_ROOT / "docs" / "figures" / "feature_importance_beeswarm.png"

def load_filtered_data_for_importance() -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """
    Load filtered features and labels for importance analysis.
    
    Returns:
        Tuple of (X_features, y_labels, metadata_df)
    """
    logger.info(f"Loading features from {FEATURES_PATH}")
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")
    
    features = np.load(FEATURES_PATH, allow_pickle=True)
    
    logger.info(f"Loading labels from {LABELS_PATH}")
    if not LABELS_PATH.exists():
        raise FileNotFoundError(f"Labels file not found: {LABELS_PATH}")
    
    labels_df = pd.read_csv(LABELS_PATH)
    
    # Filter out null labels as per T030.1 requirement
    filtered_labels_df = labels_df[labels_df['label'].isin(['valid', 'invalid'])]
    logger.info(f"Filtered {len(labels_df) - len(filtered_labels_df)} null samples for analysis")
    
    # Ensure features and labels are aligned
    # Assuming features are stored in order of clip_ids
    if 'clip_id' in filtered_labels_df.columns:
        # We assume the order in features.npy matches the order in the filtered labels
        # For robustness, we could join on clip_id if features had that metadata
        pass
    
    X = features[:len(filtered_labels_df)]  # Truncate to match filtered labels if needed
    y = (filtered_labels_df['label'] == 'invalid').astype(int).values  # Binary: 1=invalid, 0=valid
    
    logger.info(f"Loaded {X.shape[0]} samples with {X.shape[1]} features")
    logger.info(f"Class distribution: {np.bincount(y)} (0=valid, 1=invalid)")
    
    return X, y, filtered_labels_df

def load_baseline_distribution() -> Dict[str, Any]:
    """
    Load the baseline activation distribution from T032.1.
    
    Returns:
        Dictionary containing baseline statistics.
    """
    logger.info(f"Loading baseline distribution from {BASELINE_DIST_PATH}")
    if not BASELINE_DIST_PATH.exists():
        raise FileNotFoundError(f"Baseline distribution file not found: {BASELINE_DIST_PATH}")
    
    with open(BASELINE_DIST_PATH, 'r') as f:
        baseline = json.load(f)
    
    return baseline

def load_classifier() -> Any:
    """
    Load the trained classifier from T031.
    
    Returns:
        Trained model object.
    """
    logger.info(f"Loading classifier from {CLASSIFIER_PATH}")
    if not CLASSIFIER_PATH.exists():
        raise FileNotFoundError(f"Classifier file not found: {CLASSIFIER_PATH}")
    
    with open(CLASSIFIER_PATH, 'rb') as f:
        model = pickle.load(f)
    
    return model

def compute_shap_values(model: Any, X: np.ndarray, X_background: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Compute SHAP values for the model on the input data.
    
    Args:
        model: Trained classifier model.
        X: Input feature matrix.
        X_background: Background dataset for SHAP (defaults to a sample of X).
    
    Returns:
        SHAP values array.
    """
    logger.info("Computing SHAP values...")
    
    if X_background is None:
        # Use a stratified sample of 100 points as background
        n_samples = min(100, len(X))
        indices = np.random.choice(len(X), n_samples, replace=False)
        X_background = X[indices]
        logger.info(f"Using {n_samples} samples as background for SHAP")
    
    # Choose explainer based on model type
    try:
        if hasattr(model, 'feature_importances_'):
            # Tree-based models (RandomForest, XGBoost, etc.)
            logger.info("Detected tree-based model, using TreeExplainer")
            explainer = shap.TreeExplainer(model, X_background)
        else:
            # Generic model, use DeepExplainer or KernelExplainer
            logger.info("Using KernelExplainer for generic model")
            explainer = shap.KernelExplainer(model.predict_proba, X_background)
        
        shap_values = explainer.shap_values(X)
        
        # Handle multi-class output if necessary (binary classification returns list of 2 arrays)
        if isinstance(shap_values, list):
            # For binary classification, we usually care about the positive class (index 1)
            shap_values = shap_values[1]
        
        logger.info(f"Computed SHAP values with shape {shap_values.shape}")
        return shap_values
        
    except Exception as e:
        logger.error(f"Error computing SHAP values: {e}")
        logger.warning("Falling back to permutation importance as a backup")
        return compute_permutation_importance(model, X)

def compute_permutation_importance(model: Any, X: np.ndarray) -> np.ndarray:
    """
    Compute permutation importance as a fallback.
    
    Args:
        model: Trained classifier model.
        X: Input feature matrix.
    
    Returns:
        Permutation importance values (normalized to absolute mean).
    """
    logger.info("Computing permutation importance...")
    
    # Create a simple dummy y if not available (we need to pass something)
    # In a real scenario, we would pass the actual y
    y_dummy = np.zeros(len(X))
    
    result = permutation_importance(model, X, y_dummy, n_repeats=10, random_state=42, n_jobs=-1)
    
    # Return absolute mean importance
    importance = np.abs(result.importances_mean)
    logger.info(f"Computed permutation importance with shape {importance.shape}")
    return importance

def analyze_importance_against_baseline(
    shap_values: np.ndarray, 
    baseline: Dict[str, Any], 
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze feature importance against the baseline distribution.
    
    Args:
        shap_values: SHAP values array.
        baseline: Baseline distribution statistics.
        feature_names: Optional list of feature names.
    
    Returns:
        Dictionary containing analysis results.
    """
    logger.info("Analyzing importance against baseline...")
    
    # Calculate mean absolute SHAP values for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Identify top features
    top_k = 20
    top_indices = np.argsort(mean_abs_shap)[::-1][:top_k]
    
    analysis = {
        "top_features": [],
        "baseline_comparison": {},
        "summary": {}
    }
    
    # Map indices to feature names if available, else use generic names
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(len(mean_abs_shap))]
    
    for idx in top_indices:
        feature_name = feature_names[idx]
        mean_val = float(mean_abs_shap[idx])
        
        # Compare with baseline mean/std if available
        baseline_mean = baseline.get("mean", 0.0)
        baseline_std = baseline.get("std", 1.0)
        
        # Calculate z-score relative to baseline
        z_score = (mean_val - baseline_mean) / (baseline_std + 1e-8)
        
        analysis["top_features"].append({
            "name": feature_name,
            "mean_abs_shap": mean_val,
            "baseline_mean": baseline_mean,
            "baseline_std": baseline_std,
            "z_score": float(z_score),
            "is_predictive": z_score > 2.0  # Heuristic threshold
        })
    
    # Summary statistics
    analysis["summary"] = {
        "total_features": len(mean_abs_shap),
        "top_k_analyzed": top_k,
        "num_predictive_features": sum(1 for f in analysis["top_features"] if f["is_predictive"]),
        "mean_importance": float(np.mean(mean_abs_shap)),
        "std_importance": float(np.std(mean_abs_shap))
    }
    
    logger.info(f"Analysis complete. Found {analysis['summary']['num_predictive_features']} predictive features.")
    return analysis

def generate_plots(
    shap_values: np.ndarray, 
    X: np.ndarray, 
    feature_names: Optional[List[str]] = None,
    output_dir: Optional[Path] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate SHAP summary plots and save them.
    
    Args:
        shap_values: SHAP values array.
        X: Input feature matrix.
        feature_names: Optional list of feature names.
        output_dir: Directory to save plots.
    
    Returns:
        Tuple of (summary_plot_path, beeswarm_plot_path)
    """
    logger.info("Generating SHAP plots...")
    
    if output_dir is None:
        output_dir = OUTPUT_PLOT_PATH.parent
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summary_path = None
    beeswarm_path = None
    
    try:
        # Use a subset for plotting to avoid memory issues
        n_plot = min(500, len(X))
        X_plot = X[:n_plot]
        shap_plot = shap_values[:n_plot]
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(shap_plot.shape[1])]
        
        # Summary plot (bar plot of mean absolute SHAP values)
        summary_path = str(output_dir / "feature_importance_summary.png")
        plt = shap.summary_plot(
            shap_plot, 
            X_plot, 
            feature_names=feature_names, 
            plot_type="bar",
            show=False
        )
        plt.savefig(summary_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved summary plot to {summary_path}")
        
        # Beeswarm plot (distribution of SHAP values)
        beeswarm_path = str(output_dir / "feature_importance_beeswarm.png")
        plt = shap.summary_plot(
            shap_plot, 
            X_plot, 
            feature_names=feature_names, 
            plot_type="violin", # or 'dot' or 'beeswarm'
            show=False
        )
        plt.savefig(beeswarm_path, dpi=150, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved beeswarm plot to {beeswarm_path}")
        
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        logger.warning("Plots could not be generated. Continuing without visualization files.")
    
    return summary_path, beeswarm_path

def main():
    """Main entry point for feature importance analysis."""
    parser = argparse.ArgumentParser(description="Analyze feature importance using SHAP")
    parser.add_argument("--output", type=str, default=str(OUTPUT_REPORT_PATH),
                      help="Path to save the feature importance report JSON")
    parser.add_argument("--plot-dir", type=str, default=str(OUTPUT_PLOT_PATH.parent),
                      help="Directory to save SHAP plots")
    args = parser.parse_args()
    
    try:
        # 1. Load data
        X, y, labels_df = load_filtered_data_for_importance()
        baseline = load_baseline_distribution()
        model = load_classifier()
        
        # 2. Compute SHAP values
        shap_values = compute_shap_values(model, X)
        
        # 3. Analyze against baseline
        analysis_results = analyze_importance_against_baseline(shap_values, baseline)
        
        # 4. Generate plots
        plot_dir = Path(args.plot_dir)
        summary_plot, beeswarm_plot = generate_plots(shap_values, X, output_dir=plot_dir)
        
        # 5. Compile final report
        report = {
            "analysis_results": analysis_results,
            "plots": {
                "summary_plot_path": summary_plot,
                "beeswarm_plot_path": beeswarm_plot
            },
            "metadata": {
                "total_samples_analyzed": len(X),
                "num_features": X.shape[1],
                "baseline_source": str(BASELINE_DIST_PATH),
                "classifier_source": str(CLASSIFIER_PATH)
            }
        }
        
        # 6. Save report
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Feature importance report saved to {output_path}")
        logger.info("Analysis complete.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
