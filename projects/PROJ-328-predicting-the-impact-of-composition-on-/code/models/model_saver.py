import os
import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from seed import init_reproducibility
from config import get_models_dir, get_data_processed_dir, get_log_level, get_log_format
from utils.logging_config import get_logger
from utils.error_handlers import ModelTrainingError, ConfigurationError

logger = get_logger(__name__)

def save_model(model: Any, model_name: str, model_dir: Optional[Path] = None) -> Path:
    """
    Save a trained model object to disk using pickle.

    Args:
        model: The trained model instance (e.g., XGBoost or LinearRegression).
        model_name: The name to use for the file (e.g., 'xgboost_v1').
        model_dir: Optional directory override. Defaults to config models dir.

    Returns:
        Path to the saved model file.
    """
    if model_dir is None:
        model_dir = get_models_dir()

    model_path = model_dir / f"{model_name}.pkl"
    model_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Failed to save model to {model_path}: {e}")
        raise ModelTrainingError(f"Failed to save model: {e}")

def save_metrics(metrics: Dict[str, Any], model_name: str, metrics_dir: Optional[Path] = None) -> Path:
    """
    Save model metrics (CV results, bootstrap stats, etc.) to JSON.

    Args:
        metrics: Dictionary of metrics to save.
        model_name: Name of the model for the filename.
        metrics_dir: Optional directory override. Defaults to models dir.

    Returns:
        Path to the saved metrics file.
    """
    if metrics_dir is None:
        metrics_dir = get_models_dir()

    metrics_path = metrics_dir / f"{model_name}_metrics.json"
    metrics_dir.mkdir(parents=True, exist_ok=True)

    # Ensure all values are JSON serializable (convert numpy types)
    def convert_to_serializable(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        return obj

    clean_metrics = convert_to_serializable(metrics)

    try:
        with open(metrics_path, 'w') as f:
            json.dump(clean_metrics, f, indent=2)
        logger.info(f"Metrics saved to {metrics_path}")
        return metrics_path
    except Exception as e:
        logger.error(f"Failed to save metrics to {metrics_path}: {e}")
        raise ModelTrainingError(f"Failed to save metrics: {e}")

def save_vif_results(vif_data: Dict[str, float], model_name: str, data_dir: Optional[Path] = None) -> Path:
    """
    Save VIF (Variance Inflation Factor) diagnostics to a CSV file.

    Args:
        vif_data: Dictionary mapping feature names to VIF scores.
        model_name: Name of the model for the filename.
        data_dir: Optional directory override. Defaults to processed data dir.

    Returns:
        Path to the saved VIF results file.
    """
    if data_dir is None:
        data_dir = get_data_processed_dir()

    vif_path = data_dir / f"{model_name}_vif_diagnostics.csv"
    data_dir.mkdir(parents=True, exist_ok=True)

    df_vif = pd.DataFrame({
        'feature': list(vif_data.keys()),
        'vif_score': list(vif_data.values())
    })

    try:
        df_vif.to_csv(vif_path, index=False)
        logger.info(f"VIF diagnostics saved to {vif_path}")
        return vif_path
    except Exception as e:
        logger.error(f"Failed to save VIF results to {vif_path}: {e}")
        raise ModelTrainingError(f"Failed to save VIF results: {e}")

def save_shap_summary(shap_values: np.ndarray, feature_names: List[str], model_name: str, data_dir: Optional[Path] = None) -> Path:
    """
    Save SHAP summary statistics (mean absolute values) to a CSV.

    Args:
        shap_values: The SHAP values array (n_samples, n_features).
        feature_names: List of feature names corresponding to columns.
        model_name: Name of the model for the filename.
        data_dir: Optional directory override. Defaults to processed data dir.

    Returns:
        Path to the saved SHAP summary file.
    """
    if data_dir is None:
        data_dir = get_data_processed_dir()

    shap_path = data_dir / f"{model_name}_shap_summary.csv"
    data_dir.mkdir(parents=True, exist_ok=True)

    if shap_values is None or len(shap_values) == 0:
        logger.warning("No SHAP values provided, skipping summary save.")
        return shap_path

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    df_shap = pd.DataFrame({
        'feature': feature_names,
        'mean_abs_shap': mean_abs_shap
    })
    df_shap = df_shap.sort_values(by='mean_abs_shap', ascending=False)

    try:
        df_shap.to_csv(shap_path, index=False)
        logger.info(f"SHAP summary saved to {shap_path}")
        return shap_path
    except Exception as e:
        logger.error(f"Failed to save SHAP summary to {shap_path}: {e}")
        raise ModelTrainingError(f"Failed to save SHAP summary: {e}")

def save_comparison_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the model comparison report (t-test results, etc.) to JSON.

    Args:
        report: Dictionary containing the comparison report.
        output_path: Optional full path override. Defaults to models dir.

    Returns:
        Path to the saved report file.
    """
    if output_path is None:
        output_path = get_models_dir() / "model_comparison_report.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    def convert_to_serializable(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        return obj

    clean_report = convert_to_serializable(report)

    try:
        with open(output_path, 'w') as f:
            json.dump(clean_report, f, indent=2)
        logger.info(f"Comparison report saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save comparison report to {output_path}: {e}")
        raise ModelTrainingError(f"Failed to save comparison report: {e}")

def main():
    """
    Main entry point for saving model artifacts.
    This script is intended to be called by the training pipeline after training is complete.
    It expects environment variables or arguments to specify which models to save.
    For this task implementation, we assume the calling script passes the objects directly.
    """
    logger.info("Model Saver module loaded. Use functions directly from the pipeline.")
    init_reproducibility()

if __name__ == "__main__":
    main()