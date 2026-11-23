import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import logging

from utils.stats import calculate_vif, filter_high_vif_features
from utils.logging import get_logger, log_pipeline_step
from config import get_artifacts_path

logger = get_logger(__name__)

def train_null_model(X: pd.DataFrame, y: pd.Series) -> Any:
    """
    Train a baseline null model (e.g., predicting mean or majority class).
    This is a placeholder for the actual modeling logic if not already imported.
    In the context of this task, we focus on validation logic.
    """
    logger.warning("train_null_model called but logic not fully specified in this context. Assuming placeholder.")
    return None

def compare_models(real_metrics: Dict, null_metrics: Dict) -> Dict:
    """
    Compare real model performance against null model performance.
    """
    comparison = {
        "real_metric": real_metrics.get("score", 0),
        "null_metric": null_metrics.get("score", 0),
        "improvement": real_metrics.get("score", 0) - null_metrics.get("score", 0)
    }
    return comparison

def validate_null_baseline(model_metrics: Dict, null_metrics: Dict) -> bool:
    """
    Validate that the real model significantly outperforms the null baseline.
    """
    comparison = compare_models(model_metrics, null_metrics)
    is_valid = comparison["improvement"] > 0.05  # Arbitrary threshold for example
    if not is_valid:
        logger.warning("Model does not significantly outperform null baseline.")
    return is_valid

def check_vif_multicollinearity(
    feature_matrix: pd.DataFrame,
    threshold: float = 5.0,
    output_path: Optional[Path] = None
) -> Tuple[List[str], Dict[str, float]]:
    """
    Calculate Variance Inflation Factor (VIF) for features in the matrix
    to flag multicollinearity as per FR-005.

    Args:
        feature_matrix: DataFrame containing feature columns (numeric).
        threshold: VIF threshold above which a feature is flagged (default 5.0).
        output_path: Optional path to save the VIF report.

    Returns:
        Tuple of (list of flagged feature names, dict of VIF scores).
    """
    if feature_matrix.empty:
        logger.warning("Feature matrix is empty. Skipping VIF check.")
        return [], {}

    # Ensure only numeric columns are used
    numeric_cols = feature_matrix.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        logger.warning("No numeric features found for VIF calculation.")
        return [], {}

    vif_scores = calculate_vif(feature_matrix[numeric_cols])
    
    flagged_features = []
    for feat, score in vif_scores.items():
        if score > threshold:
            flagged_features.append(feat)
            logger.warning(f"High multicollinearity detected for feature '{feat}': VIF = {score:.2f}")

    # Save report if path provided
    if output_path:
        report_data = {
            "threshold": threshold,
            "timestamp": pd.Timestamp.now().isoformat(),
            "flagged_features": flagged_features,
            "vif_scores": vif_scores
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"VIF report saved to {output_path}")

    return flagged_features, vif_scores

def run_validation_pipeline(
    X_train: pd.DataFrame,
    model_metrics: Optional[Dict] = None,
    null_metrics: Optional[Dict] = None,
    vif_threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Run the full validation pipeline:
    1. Check VIF multicollinearity on training features.
    2. Validate null baseline if metrics are provided.

    Args:
        X_train: Training feature matrix.
        model_metrics: Dictionary of real model metrics.
        null_metrics: Dictionary of null model metrics.
        vif_threshold: Threshold for VIF flagging.

    Returns:
        Dictionary containing validation results.
    """
    results = {
        "vif_check": {},
        "null_baseline_valid": False,
        "comparison": {}
    }

    # VIF Check
    vif_report_path = get_artifacts_path() / "reports" / "vif_report.json"
    flagged, scores = check_vif_multicollinearity(X_train, threshold=vif_threshold, output_path=vif_report_path)
    results["vif_check"] = {
        "flagged_features": flagged,
        "count": len(flagged),
        "threshold": vif_threshold,
        "report_path": str(vif_report_path)
    }

    # Null Baseline Validation
    if model_metrics and null_metrics:
        is_valid = validate_null_baseline(model_metrics, null_metrics)
        comparison = compare_models(model_metrics, null_metrics)
        results["null_baseline_valid"] = is_valid
        results["comparison"] = comparison
    else:
        logger.info("Skipping null baseline validation as metrics were not provided.")

    return results

def save_validation_report(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the validation results to a JSON file.
    """
    if output_path is None:
        output_path = get_artifacts_path() / "reports" / "validation_report.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Validation report saved to {output_path}")
    return output_path

def main():
    """
    Entry point for running validation checks directly.
    """
    logger.info("Starting validation pipeline main.")
    # Example usage if run as script (would need real data paths)
    # This is primarily for integration into the main pipeline
    pass

if __name__ == "__main__":
    main()