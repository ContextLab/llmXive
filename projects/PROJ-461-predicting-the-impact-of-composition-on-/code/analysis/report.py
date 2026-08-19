import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import shap

from config import Config, load_config
from utils.logger import get_logger

# --------------------------------------------------------------------------
# Helper functions (kept consistent with existing API surface)
# --------------------------------------------------------------------------

def load_model(model_path: Path) -> Any:
    """Load the trained LightGBM model."""
    with open(model_path, "rb") as f:
        return pickle.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load the processed dataset with features and target."""
    return pd.read_csv(data_path)

def calculate_model_metrics(
    model: Any, X: pd.DataFrame, y: np.ndarray
) -> Dict[str, float]:
    """Calculate MAE and R² on the given data."""
    preds = model.predict(X)
    mae = float(np.mean(np.abs(preds - y)))
    ss_res = np.sum((y - preds) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    return {"mae": mae, "r2": float(r2)}

def generate_shap_summary(
    model: Any, X: pd.DataFrame, feature_names: List[str], output_path: Path
) -> None:
    """Generate SHAP summary plot and save it."""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

def run_sensitivity_analysis(
    model: Any, X: pd.DataFrame, y: np.ndarray, noise_levels: List[float] = [0.01, 0.05, 0.1]
) -> Dict[str, Any]:
    """Run sensitivity analysis by adding noise to target and measuring MAE variance."""
    results = {}
    for noise_level in noise_levels:
        rng = np.random.default_rng(42)
        noisy_y = y + rng.normal(0, noise_level, size=y.shape)
        preds = model.predict(X)
        mae = float(np.mean(np.abs(preds - noisy_y)))
        results[f"noise_{noise_level}"] = {"mae": mae}
    return results

def generate_pdp_radius_mismatch(
    model: Any,
    X: pd.DataFrame,
    feature_name: str = "atomic_radius_mismatch",
    output_path: Path = Path("reports/pdp_radius_mismatch.png"),
) -> Dict[str, Any]:
    """
    Generate Partial Dependence Plots for radius mismatch if MAE > 0.1.
    Returns variance analysis findings.
    """
    if feature_name not in X.columns:
        raise ValueError(f"Feature '{feature_name}' not found in data.")

    # Calculate MAE to determine if we proceed (this function is called conditionally,
    # but we re-calculate or assume context passed. Here we assume caller ensures MAE > 0.1)
    # For safety, we just generate the plot as requested by the task logic.
    
    explainer = shap.TreeExplainer(model)
    # Compute PDP for the specific feature
    pdp_data = shap.PDPData(
        model=model, X=X, feature_names=X.columns.tolist(), feature=feature_name, nsamples='auto'
    )
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))
    shap.plots.pdp(pdp_data, show=False)
    plt.title(f"Partial Dependence Plot: {feature_name}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    # Variance analysis: Calculate the variance of the PDP values
    # shap.PDPData returns a structure we can inspect, but for simplicity,
    # we compute the variance of the partial dependence values directly from the explainer if needed.
    # However, shap's PDP plot data is internal. Let's compute PDP manually for variance.
    
    # Manual PDP calculation for variance analysis
    feature_values = X[feature_name].values
    unique_vals = np.unique(feature_values)
    pdp_vals = []
    
    # If too many unique values, sample
    if len(unique_vals) > 100:
        unique_vals = np.percentile(feature_values, np.linspace(0, 100, 100))
    
    for val in unique_vals:
        X_temp = X.copy()
        X_temp[feature_name] = val
        preds = model.predict(X_temp)
        pdp_vals.append(np.mean(preds))
    
    pdp_vals = np.array(pdp_vals)
    variance = float(np.var(pdp_vals))
    std_dev = float(np.std(pdp_vals))
    
    findings = {
        "feature": feature_name,
        "pdp_variance": variance,
        "pdp_std_dev": std_dev,
        "plot_saved": str(output_path),
        "interpretation": (
            f"The PDP for {feature_name} has a variance of {variance:.4f} and std dev of {std_dev:.4f}. "
            "This indicates the sensitivity of the model's prediction to changes in radius mismatch."
        )
    }
    
    return findings

def compile_analysis_report(
    metrics: Dict[str, float],
    sensitivity_results: Dict[str, Any],
    output_path: Path = Path("reports/analysis_report.html"),
) -> None:
    """Compile an HTML report with metrics and sensitivity analysis."""
    html_content = f"""
    <html>
    <head><title>Metallic Glass Density Analysis Report</title></head>
    <body>
        <h1>Analysis Report</h1>
        <h2>Model Metrics</h2>
        <ul>
            <li>MAE: {metrics.get('mae', 'N/A')}</li>
            <li>R²: {metrics.get('r2', 'N/A')}</li>
        </ul>
        <h2>Sensitivity Analysis</h2>
        <pre>{json.dumps(sensitivity_results, indent=2)}</pre>
    </body>
    </html>
    """
    with open(output_path, "w") as f:
        f.write(html_content)

def main() -> None:
    """Main entry point for the report generation pipeline."""
    config = load_config()
    logger = get_logger("report")
    
    model_path = config.model_dir / "model.pkl"
    data_path = config.data_dir / "clean_data.csv"
    metrics_path = config.report_dir / "metrics.json"
    
    # Load data and model
    model = load_model(model_path)
    df = load_processed_data(data_path)
    
    # Identify feature columns (exclude target and composition string)
    feature_cols = [c for c in df.columns if c not in ["composition", "density", "density_residual"]]
    X = df[feature_cols]
    y = df["density_residual"].values
    
    # Calculate metrics
    metrics = calculate_model_metrics(model, X, y)
    
    # Save metrics if not already done by training (T026)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
    
    # Generate SHAP summary
    shap_path = config.report_dir / "shap_summary.png"
    generate_shap_summary(model, X, feature_cols, shap_path)
    logger.info(f"SHAP summary saved to {shap_path}")
    
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(model, X, y)
    sens_path = config.report_dir / "sensitivity_analysis.json"
    with open(sens_path, "w") as f:
        json.dump(sensitivity_results, f, indent=2)
    logger.info(f"Sensitivity analysis saved to {sens_path}")
    
    # T033: Conditional PDP generation for radius mismatch if MAE > 0.1
    if metrics["mae"] > 0.1:
        logger.warning("MAE > 0.1. Generating Partial Dependence Plot for radius mismatch.")
        pdp_path = config.report_dir / "pdp_radius_mismatch.png"
        pdp_findings = generate_pdp_radius_mismatch(
            model, X, feature_name="atomic_radius_mismatch", output_path=pdp_path
        )
        
        # Save findings to a JSON file as distinct finding
        findings_path = config.report_dir / "pdp_findings.json"
        with open(findings_path, "w") as f:
            json.dump(pdp_findings, f, indent=2)
        
        logger.info(f"PDP radius mismatch plot saved to {pdp_path}")
        logger.info(f"PDP findings saved to {findings_path}")
    else:
        logger.info("MAE <= 0.1. Skipping PDP generation for radius mismatch.")
    
    # Compile final HTML report
    report_path = config.report_dir / "analysis_report.html"
    compile_analysis_report(metrics, sensitivity_results, report_path)
    logger.info(f"Analysis report compiled at {report_path}")

if __name__ == "__main__":
    main()