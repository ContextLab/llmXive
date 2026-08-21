import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def load_model(config: Config) -> Any:
    """Load the trained model from disk."""
    model_path = config.model_dir / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    with open(model_path, "rb") as f:
        return pickle.load(f)


def load_processed_data(config: Config) -> pd.DataFrame:
    """Load the processed data with descriptors and residuals."""
    # Determine source from validation log
    validation_log_path = config.data_dir / "validation_log.json"
    if validation_log_path.exists():
        with open(validation_log_path, "r") as f:
            validation_info = json.load(f)
        source = validation_info.get("source", "clean_data.csv")
    else:
        source = "clean_data.csv"

    data_path = config.data_dir / source
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    return pd.read_csv(data_path)


def calculate_baseline_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Linear Mixing Rule Baseline MAE.
    Assumes columns 'rho_baseline' (predicted by linear rule) and 'density' (actual) exist.
    """
    if "rho_baseline" not in df.columns or "density" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'rho_baseline' and 'density' columns for baseline calculation."
        )

    residuals = df["density"] - df["rho_baseline"]
    mae = np.mean(np.abs(residuals))
    return {"linear_mixing_rule_mae": float(mae)}


def calculate_model_metrics(
    model: Any, df: pd.DataFrame, feature_cols: List[str]
) -> Dict[str, float]:
    """
    Calculate Model MAE and R² on the residual target.
    Assumes model is trained on 'rho_residual' and feature_cols are present.
    """
    if "rho_residual" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'rho_residual' column for model metric calculation."
        )

    X = df[feature_cols]
    y = df["rho_residual"]

    y_pred = model.predict(X)
    mae = np.mean(np.abs(y - y_pred))
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

    return {"model_mae": float(mae), "model_r2": float(r2)}


def calculate_mass_only_baseline_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Mass-Only Baseline MAE.
    Fits a simple Linear Regression on 'mean_atomic_mass' to predict 'rho_residual'.
    """
    if "mean_atomic_mass" not in df.columns or "rho_residual" not in df.columns:
        raise ValueError(
            "DataFrame must contain 'mean_atomic_mass' and 'rho_residual' columns."
        )

    from sklearn.linear_model import LinearRegression

    X = df[["mean_atomic_mass"]]
    y = df["rho_residual"]

    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)

    mae = np.mean(np.abs(y - y_pred))
    return {"mass_only_baseline_mae": float(mae)}


def save_metrics(
    config: Config,
    model_mae: float,
    model_r2: float,
    linear_mixing_mae: float,
    mass_only_mae: float,
) -> None:
    """Save all metrics to reports/metrics.json."""
    metrics = {
        "model_mae": model_mae,
        "model_r2": model_r2,
        "linear_mixing_rule_baseline_mae": linear_mixing_mae,
        "mass_only_baseline_mae": mass_only_mae,
    }

    report_path = config.report_dir / "metrics.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {report_path}")


def main() -> None:
    """Main entry point for T026: Save metrics to reports/metrics.json."""
    config = load_config()
    logger.info("Starting metrics calculation (T026)...")

    # Load data and model
    df = load_processed_data(config)
    model = load_model(config)

    # Define feature columns (excluding target and composition strings)
    feature_cols = [
        "mean_atomic_mass",
        "mean_atomic_radius",
        "electronegativity_variance",
        "atomic_radius_mismatch",
        "packing_efficiency",
    ]
    # Ensure columns exist, otherwise take available numeric ones excluding targets
    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        # Fallback to all numeric columns except known non-features
        exclude_cols = {"composition", "density", "rho_baseline", "rho_residual"}
        available_features = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude_cols]

    logger.info(f"Using features: {available_features}")

    # Calculate metrics
    linear_mixing_mae = calculate_baseline_metrics(df)["linear_mixing_rule_mae"]
    mass_only_mae = calculate_mass_only_baseline_metrics(df)["mass_only_baseline_mae"]
    model_metrics = calculate_model_metrics(model, df, available_features)
    model_mae = model_metrics["model_mae"]
    model_r2 = model_metrics["model_r2"]

    # Save metrics
    save_metrics(
        config,
        model_mae,
        model_r2,
        linear_mixing_mae,
        mass_only_mae,
    )

    logger.info("T026 completed successfully.")


if __name__ == "__main__":
    main()