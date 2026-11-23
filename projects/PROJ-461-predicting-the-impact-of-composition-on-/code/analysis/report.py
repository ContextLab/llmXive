import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def load_model(config: Config) -> Any:
    """Load the trained LightGBM model from disk."""
    model_path = config.model_dir / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    with open(model_path, "rb") as f:
        return pickle.load(f)


def load_processed_data(config: Config) -> pd.DataFrame:
    """Load the processed data (clean or synthetic) based on validation log."""
    validation_log_path = config.data_dir / "validation_log.json"
    if not validation_log_path.exists():
        raise FileNotFoundError(f"Validation log not found at {validation_log_path}")

    with open(validation_log_path, "r") as f:
        validation_info = json.load(f)

    data_path = config.data_dir / validation_info["data_path"]
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")

    return pd.read_csv(data_path)


def calculate_model_metrics(
    model: Any, X_test: pd.DataFrame, y_test: pd.Series
) -> Dict[str, float]:
    """Calculate MAE and R2 for the model on test data."""
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = model.score(X_test, y_test)
    return {"mae": float(mae), "r2": float(r2)}


def generate_predicted_vs_actual_plot(
    y_true: np.ndarray, y_pred: np.ndarray, output_path: Path
) -> None:
    """Generate a scatter plot of predicted vs actual values with R2 in title."""
    plt.figure(figsize=(8, 6))
    plt.scatter(y_true, y_pred, alpha=0.6)
    plt.plot(
        [y_true.min(), y_true.max()],
        [y_true.min(), y_true.max()],
        "r--",
        lw=2,
    )
    plt.xlabel("Actual Density")
    plt.ylabel("Predicted Density")
    plt.title(f"Predicted vs Actual (R² = {calculate_r2(y_true, y_pred):.4f})")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved predicted vs actual plot to {output_path}")


def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared value."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1 - (ss_res / ss_tot))


def generate_shap_summary(
    model: Any, X: pd.DataFrame, feature_names: List[str], output_path: Path
) -> None:
    """Generate SHAP summary plot comparing Mean Atomic Mass vs Radius Mismatch."""
    try:
        import shap

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            shap_values, X, feature_names=feature_names, show=False
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Saved SHAP summary plot to {output_path}")
    except ImportError:
        logger.warning("SHAP not installed, skipping summary plot generation")
        # Create a placeholder file to indicate the step was attempted
        with open(output_path, "w") as f:
            f.write("SHAP not installed - plot skipped")


def run_sensitivity_analysis(
    config: Config, model: Any, X_test: pd.DataFrame, y_test: pd.Series
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by adding Gaussian noise to the target variable
    and measuring the variance in MAE and RMSE.

    Outputs:
        reports/sensitivity_analysis.json containing MAE and RMSE variance for each noise level.
    """
    noise_levels = [0.0, 0.01, 0.02, 0.05, 0.1]
    results = []

    base_mae = mean_absolute_error(y_test, model.predict(X_test))
    base_rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))

    for noise_mag in noise_levels:
        # Add Gaussian noise to target
        noise = np.random.normal(0, noise_mag, size=y_test.shape)
        y_noisy = y_test + noise

        predictions = model.predict(X_test)
        # Note: The model is trained on original data, we evaluate on noisy targets
        # to see how sensitive the error metrics are to target noise.
        current_mae = mean_absolute_error(y_noisy, predictions)
        current_rmse = np.sqrt(mean_squared_error(y_noisy, predictions))

        results.append(
            {
                "noise_level": float(noise_mag),
                "mae": float(current_mae),
                "rmse": float(current_rmse),
                "mae_variance": float(current_mae - base_mae),
                "rmse_variance": float(current_rmse - base_rmse),
            }
        )
        logger.info(
            f"Noise {noise_mag:.2f}: MAE={current_mae:.4f}, RMSE={current_rmse:.4f}"
        )

    output = {
        "description": "Sensitivity analysis of model metrics to Gaussian noise in target",
        "base_metrics": {
            "mae": float(base_mae),
            "rmse": float(base_rmse),
        },
        "results": results,
    }

    return output


def generate_pdp_radius_mismatch(
    model: Any, X: pd.DataFrame, feature_name: str, output_path: Path
) -> None:
    """Generate Partial Dependence Plot for radius mismatch if triggered."""
    try:
        import shap

        explainer = shap.TreeExplainer(model)
        pdp = shap.partial_dependence(
            explainer, X, [feature_name], kind="average"
        )
        pdp_values = pdp["values"]
        pdp_dependence = pdp["average"]

        plt.figure(figsize=(8, 6))
        plt.plot(pdp_values, pdp_dependence, marker="o")
        plt.xlabel(feature_name)
        plt.ylabel("Partial Dependence")
        plt.title(f"Partial Dependence Plot for {feature_name}")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        logger.info(f"Saved PDP for {feature_name} to {output_path}")
    except ImportError:
        logger.warning("SHAP not installed, skipping PDP generation")
        with open(output_path, "w") as f:
            f.write("SHAP not installed - PDP skipped")


def compile_analysis_report(
    config: Config,
    predictions_path: Path,
    shap_path: Path,
    sensitivity_path: Path,
    output_path: Path,
) -> None:
    """Compile the final HTML analysis report."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metallic Glass Density Analysis Report</title>
    </head>
    <body>
        <h1>Metallic Glass Density Prediction Report</h1>
        <h2>Predicted vs Actual</h2>
        <img src="reports/predicted_vs_actual.png" alt="Predicted vs Actual Plot" style="max-width: 800px;">
        <h2>SHAP Feature Importance</h2>
        <img src="reports/shap_summary.png" alt="SHAP Summary" style="max-width: 800px;">
        <h2>Sensitivity Analysis</h2>
        <pre>
    """
    with open(sensitivity_path, "r") as f:
        html_content += json.dumps(json.load(f), indent=2)
    html_content += """
        </pre>
    </body>
    </html>
    """
    with open(output_path, "w") as f:
        f.write(html_content)
    logger.info(f"Saved analysis report to {output_path}")


def main() -> None:
    """Main entry point for the analysis report module."""
    config = load_config()
    logger.info("Starting analysis report generation")

    # Load model and data
    model = load_model(config)
    df = load_processed_data(config)

    # Prepare features and target (assuming 'density' is the target)
    # We need to identify feature columns. Assuming they are all numeric except 'composition' and 'density'
    feature_cols = [
        col for col in df.columns if col not in ["composition", "density"]
    ]
    X = df[feature_cols]
    y = df["density"]

    # 1. Generate Predicted vs Actual Plot
    y_pred = model.predict(X)
    output_plot = config.report_dir / "predicted_vs_actual.png"
    generate_predicted_vs_actual_plot(y.values, y_pred, output_plot)

    # 2. Generate SHAP Summary
    output_shap = config.report_dir / "shap_summary.png"
    generate_shap_summary(model, X, feature_cols, output_shap)

    # 3. Run Sensitivity Analysis
    sensitivity_results = run_sensitivity_analysis(config, model, X, y)
    output_sensitivity = config.report_dir / "sensitivity_analysis.json"
    with open(output_sensitivity, "w") as f:
        json.dump(sensitivity_results, f, indent=2)
    logger.info(f"Sensitivity analysis saved to {output_sensitivity}")

    # 4. Compile Report
    # Note: This assumes the previous plots exist. In a real pipeline, we might check existence.
    output_report = config.report_dir / "analysis_report.html"
    compile_analysis_report(
        config,
        output_plot,
        output_shap,
        output_sensitivity,
        output_report,
    )

    logger.info("Analysis report generation complete")


if __name__ == "__main__":
    main()