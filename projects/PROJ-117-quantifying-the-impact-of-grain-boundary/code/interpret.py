import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
import yaml

# Import from project utilities and modules
from utils import setup_logging, load_metadata
from config.threshold_config import get_threshold_justification, get_threshold_metadata

# Configure logging
logger = setup_logging("interpret")

def load_model_and_data(model_path: str, data_path: str) -> Tuple[Any, pd.DataFrame]:
    """Load the trained model and the dataset used for training/evaluation."""
    logger.info(f"Loading model from {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    # Assuming model is saved as JSON (XGBoost) or pickle
    # Adjust based on actual save format in train_final.py
    try:
        import xgboost as xgb
        model = xgb.Booster()
        model.load_model(model_path)
    except Exception as e:
        logger.warning(f"Failed to load as XGBoost booster, trying pickle: {e}")
        import pickle
        with open(model_path, 'rb') as f:
            model = pickle.load(f)

    logger.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # Try parquet first, fallback to csv
    if data_path.endswith('.parquet'):
        df = pd.read_parquet(data_path)
    elif data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
    else:
        # Try parquet by default
        try:
            df = pd.read_parquet(data_path)
        except:
            df = pd.read_csv(data_path)

    return model, df

def load_threshold_justification() -> str:
    """
    Load the R² threshold justification from config.yaml.
    This satisfies T022: Add logic to load the R² threshold justification
    and include it in the final report.
    """
    config_path = Path("config.yaml")
    if not config_path.exists():
        logger.warning("config.yaml not found. Using default justification.")
        return "No justification found in config.yaml."

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Navigate to the justification field as per T030 spec
        justification = config.get('thresholds', {}).get('r2', {}).get('citation', '')

        if not justification:
            logger.warning("thresholds.r2.citation is empty in config.yaml.")
            return "No justification found in config.yaml."

        logger.info(f"Loaded threshold justification: {justification}")
        return justification

    except Exception as e:
        logger.error(f"Error loading threshold justification from config.yaml: {e}")
        return f"Error loading justification: {str(e)}"

def generate_shap_analysis(model: Any, data: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
    """Generate SHAP summary plot and feature importance list."""
    logger.info("Generating SHAP analysis...")

    # Prepare data for SHAP (exclude target column if present)
    # Assuming the last column is the target 'diffusivity' or similar
    # We need to identify feature columns. Let's assume all except 'diffusivity' are features.
    feature_cols = [c for c in data.columns if c.lower() not in ['diffusivity', 'target', 'y']]

    if len(feature_cols) == 0:
        logger.error("No feature columns found in dataset.")
        return {"error": "No feature columns found"}

    X = data[feature_cols].fillna(0)  # Handle missing values for SHAP

    # Create SHAP explainer
    # For XGBoost, we can use the built-in tree explainer
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
    except Exception as e:
        logger.error(f"Error creating SHAP explainer: {e}")
        # Fallback: use KernelExplainer (slower but more general)
        logger.info("Falling back to KernelExplainer...")
        explainer = shap.KernelExplainer(model.predict, X.sample(min(100, len(X))))
        shap_values = explainer.shap_values(X.sample(min(100, len(X))))

    # Create summary plot
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values, X, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance")
    plt.tight_layout()
    shap_plot_path = Path("artifacts/figures/shap_summary.png")
    shap_plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(shap_plot_path)
    plt.close()
    logger.info(f"Saved SHAP summary plot to {shap_plot_path}")

    # Extract feature importance
    if isinstance(shap_values, list):
        # For multi-output, take the first
        shap_values = shap_values[0]

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'mean_abs_shap': mean_abs_shap
    }).sort_values('mean_abs_shap', ascending=False)

    return {
        "plot_path": str(shap_plot_path),
        "feature_importance": importance_df.to_dict(orient='records')
    }

def perform_sensitivity_analysis(model: Any, data: pd.DataFrame, thresholds: List[float]) -> pd.DataFrame:
    """
    Perform sensitivity analysis by sweeping R² thresholds.
    Calculates pass rate and FPR proxy for each threshold.
    """
    logger.info(f"Performing sensitivity analysis for thresholds: {thresholds}")

    # Prepare data
    feature_cols = [c for c in data.columns if c.lower() not in ['diffusivity', 'target', 'y']]
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in dataset.")

    X = data[feature_cols].fillna(0)
    y_true = data['diffusivity'] if 'diffusivity' in data.columns else data.iloc[:, -1]

    # Get predictions
    try:
        y_pred = model.predict(X)
    except Exception as e:
        # Fallback for non-XGBoost models
        y_pred = model.predict(X.values)

    results = []

    for threshold in thresholds:
        # Calculate R² for this threshold context (overall model R²)
        # Note: We calculate overall R² once, then check pass rate against threshold
        from sklearn.metrics import r2_score
        overall_r2 = r2_score(y_true, y_pred)

        # Pass Rate: Proportion of bootstrap samples (or folds) where R² > threshold
        # Since we have one model, we use the overall R² as a proxy for "pass"
        pass_rate = 1.0 if overall_r2 > threshold else 0.0

        # False Positive Rate Proxy:
        # Proportion of test records where predicted > threshold AND actual <= threshold
        # This measures how often we over-predict diffusivity above the threshold
        fp_count = np.sum((y_pred > threshold) & (y_true <= threshold))
        total_count = len(y_true)
        fpr_proxy = fp_count / total_count if total_count > 0 else 0.0

        results.append({
            'threshold': threshold,
            'pass_rate': pass_rate,
            'fpr_proxy': fpr_proxy,
            'sample_size': total_count,
            'overall_r2': overall_r2
        })

    return pd.DataFrame(results)

def main():
    """Main entry point for interpretability analysis."""
    logger.info("Starting interpretability analysis...")

    # Define paths
    model_path = "models/best_model.json"
    data_path = "data/processed/cleaned_dataset.parquet"
    output_dir = Path("artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load threshold justification (T022 requirement)
    justification = load_threshold_justification()

    # Load model and data
    try:
        model, data = load_model_and_data(model_path, data_path)
    except Exception as e:
        logger.error(f"Failed to load model or data: {e}")
        # Create error report
        error_report = {
            "status": "failed",
            "error": str(e),
            "threshold_justification": justification
        }
        with open(output_dir / "reports" / "interpretability_report.json", 'w') as f:
            json.dump(error_report, f, indent=2)
        sys.exit(1)

    # Generate SHAP analysis
    shap_results = generate_shap_analysis(model, data, list(data.columns))

    # Perform sensitivity analysis
    # Load thresholds from config.yaml
    config_path = Path("config.yaml")
    thresholds = [0.70, 0.75, 0.80]  # Default fallback
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                sweep_range = config.get('thresholds', {}).get('r2', {}).get('sweep_range', [])
                if sweep_range:
                    thresholds = [float(x) for x in sweep_range]
        except Exception as e:
            logger.warning(f"Could not load sweep_range from config.yaml: {e}")

    sensitivity_df = perform_sensitivity_analysis(model, data, thresholds)

    # Save sensitivity table
    sensitivity_path = output_dir / "reports" / "threshold-sensitivity-table.csv"
    sensitivity_df.to_csv(sensitivity_path, index=False)
    logger.info(f"Saved sensitivity table to {sensitivity_path}")

    # Generate final report including threshold justification
    report = {
        "status": "success",
        "threshold_justification": justification,
        "shap_analysis": shap_results,
        "sensitivity_analysis": {
            "thresholds_tested": thresholds,
            "results": sensitivity_df.to_dict(orient='records')
        },
        "config_loaded": config_path.exists(),
        "justification_source": "config.yaml" if config_path.exists() else "default"
    }

    report_path = output_dir / "reports" / "interpretability_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved interpretability report to {report_path}")
    logger.info("Interpretability analysis completed successfully.")

if __name__ == "__main__":
    main()