import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from jinja2 import Environment, FileSystemLoader
import datetime

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_model(model_path: Path) -> Any:
    """Load the trained model from disk."""
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load the processed data (clean or synthetic) from disk."""
    return pd.read_csv(data_path)

def calculate_model_metrics(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """Calculate model performance metrics."""
    y_pred = model.predict(X_test)
    mse = np.mean((y_test - y_pred) ** 2)
    mae = np.mean(np.abs(y_test - y_pred))
    r2 = 1 - (np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2))
    return {"mse": float(mse), "mae": float(mae), "r2": float(r2)}

def generate_predicted_vs_actual_plot(y_true: pd.Series, y_pred: np.ndarray, output_path: Path) -> None:
    """Generate scatter plot of predicted vs actual density."""
    plt.figure(figsize=(10, 8))
    plt.scatter(y_true, y_pred, alpha=0.6, edgecolors='k')
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
    plt.xlabel('Actual Density')
    plt.ylabel('Predicted Density')
    plt.title(f'Predicted vs Actual Density (R² = {calculate_model_metrics(None, None, y_true)["r2"]:.4f})')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved predicted vs actual plot to {output_path}")

def generate_shap_summary(model: Any, X: pd.DataFrame, feature_names: List[str], output_path: Path) -> None:
    """Generate SHAP summary plot."""
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
        plt.figure(figsize=(12, 8))
        shap.summary_plot(shap_values, X, feature_names=feature_names, show=False)
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved SHAP summary plot to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate SHAP summary: {e}")
        # Fallback: create a placeholder plot if SHAP fails
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "SHAP analysis unavailable", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("SHAP Summary (Unavailable)")
        plt.axis('off')
        plt.savefig(output_path)
        plt.close()

def run_sensitivity_analysis(model: Any, X: pd.DataFrame, y: pd.Series, noise_levels: List[float] = [0.01, 0.05, 0.1]) -> Dict[str, Any]:
    """Run sensitivity analysis by adding noise to target."""
    results = []
    for noise_level in noise_levels:
        y_noisy = y + np.random.normal(0, noise_level, size=y.shape)
        y_pred = model.predict(X)
        mae = np.mean(np.abs(y_noisy - y_pred))
        results.append({"noise_level": noise_level, "mae": float(mae)})
    return {"sensitivity_analysis": results}

def generate_pdp_radius_mismatch(model: Any, X: pd.DataFrame, feature_name: str, output_path: Path) -> None:
    """Generate Partial Dependence Plot for radius mismatch."""
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        pdp = explainer.partial_dependence(X, feature=feature_name)
        plt.figure(figsize=(10, 6))
        plt.plot(X[feature_name].sort_values(), pdp, marker='o')
        plt.xlabel(feature_name.replace('_', ' ').title())
        plt.ylabel('Partial Dependence')
        plt.title(f'Partial Dependence Plot: {feature_name.replace("_", " ").title()}')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved PDP for {feature_name} to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate PDP for {feature_name}: {e}")
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, f"PDP for {feature_name} unavailable", ha='center', va='center', transform=plt.gca().transAxes)
        plt.title(f"Partial Dependence Plot: {feature_name} (Unavailable)")
        plt.axis('off')
        plt.savefig(output_path)
        plt.close()

def compile_analysis_report(metrics: Dict[str, Any], report_path: Path, config: Config) -> None:
    """Compile the final HTML analysis report."""
    # Prepare data for template
    report_data = {
        "title": "Metallic Glass Density Prediction Analysis Report",
        "generated_at": datetime.datetime.now().isoformat(),
        "metrics": metrics,
        "config": {
            "seed": config.seed,
            "data_dir": str(config.data_dir),
            "model_dir": str(config.model_dir),
            "report_dir": str(config.report_dir)
        }
    }

    # Simple HTML template
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            h2 { color: #555; margin-top: 30px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .metric-card { background: #f9f9f9; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .metric-value { font-size: 1.5em; font-weight: bold; color: #007bff; }
            .timestamp { color: #888; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <p class="timestamp">Generated: {{ generated_at }}</p>

        <h2>Model Performance Metrics</h2>
        <div class="metric-card">
            <p>Model MAE: <span class="metric-value">{{ metrics.model_mae }}</span></p>
            <p>Linear Mixing Rule Baseline MAE: <span class="metric-value">{{ metrics.linear_baseline_mae }}</span></p>
            <p>Mass-Only Baseline MAE: <span class="metric-value">{{ metrics.mass_only_baseline_mae }}</span></p>
            <p>R² Score: <span class="metric-value">{{ metrics.r2_score }}</span></p>
        </div>

        <h2>Configuration</h2>
        <table>
            <tr><th>Parameter</th><th>Value</th></tr>
            <tr><td>Random Seed</td><td>{{ config.seed }}</td></tr>
            <tr><td>Data Directory</td><td>{{ config.data_dir }}</td></tr>
            <tr><td>Model Directory</td><td>{{ config.model_dir }}</td></tr>
            <tr><td>Report Directory</td><td>{{ config.report_dir }}</td></tr>
        </table>

        <h2>Analysis Summary</h2>
        <p>This report summarizes the predictive performance of the Gradient Boosting model trained on metallic glass composition data. Key metrics include Mean Absolute Error (MAE) compared against two baselines: the Linear Mixing Rule and a Mass-Only model. The R² score indicates the proportion of variance explained by the model.</p>
        <p>Visualizations (Predicted vs Actual, SHAP Summary, Sensitivity Analysis, and Partial Dependence Plots) are saved in the reports directory for further inspection.</p>
    </body>
    </html>
    """

    # Write HTML file
    with open(report_path, 'w') as f:
        f.write(html_template.format(**report_data))

    logger.info(f"Compiled analysis report to {report_path}")

def main() -> None:
    """Main entry point for report compilation."""
    config = load_config()
    logger.info("Starting report compilation...")

    # Load metrics from metrics.json
    metrics_path = config.report_dir / "metrics.json"
    if not metrics_path.exists():
        logger.error(f"Metrics file not found at {metrics_path}")
        return

    with open(metrics_path, 'r') as f:
        metrics = json.load(f)

    # Compile the HTML report
    report_path = config.report_dir / "analysis_report.html"
    compile_analysis_report(metrics, report_path, config)

    logger.info("Report compilation completed successfully.")

if __name__ == "__main__":
    main()