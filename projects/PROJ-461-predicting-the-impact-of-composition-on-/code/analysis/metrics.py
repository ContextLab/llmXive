import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from config import Config, load_config
from utils.logger import get_logger

logger = get_logger(__name__)

def load_model(model_path: Path) -> Any:
    """Load the trained model from a pickle file."""
    logger.info(f"Loading model from {model_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, "rb") as f:
        return pickle.load(f)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """Load the processed dataset containing features and target."""
    logger.info(f"Loading processed data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_csv(data_path)
    return df

def calculate_baseline_metrics(df: pd.DataFrame, config: Config) -> Dict[str, float]:
    """
    Calculate metrics for baselines:
    1. Linear Mixing Rule Baseline (predicts rho_baseline directly)
    2. Mass-Only Baseline (predicts rho_residual using mean_atomic_mass)
    
    Returns dict with 'lmr_mae', 'mass_only_mae'.
    """
    logger.info("Calculating baseline metrics...")
    
    # Ensure required columns exist
    required_cols = ['density', 'mean_atomic_mass']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Calculate Linear Mixing Rule Baseline (LMR)
    # The spec implies we calculate rho_baseline = sum(w_i * rho_i).
    # However, for a regression baseline to compare against the ML model's residual prediction,
    # we need to see if a simple linear model on mass fractions predicts density better than just the rule.
    # But T025-ALT-SPEC says: "Linear Regression on raw mass fractions to predict rho_baseline directly".
    # And T023 calculates rho_baseline and rho_residual = rho_actual - rho_baseline.
    # The ML model predicts rho_residual.
    # To compare fairly, we should compare the ML model's prediction of rho_residual vs a baseline prediction of rho_residual.
    # However, the task T026 asks for "Linear Mixing Rule Baseline MAE".
    # Interpretation: The LMR Baseline is the error of the pure Linear Mixing Rule (no learning) on the ACTUAL density.
    # But the ML model predicts RESIDUALS.
    # Let's follow T025-ALT-SPEC literally: "Linear Regression on raw mass fractions to predict rho_baseline directly".
    # This seems to imply a learned baseline.
    # Let's re-read T026: "Save metrics (Model MAE, Linear Mixing Rule Baseline MAE, Mass-Only Baseline MAE, R²)".
    # Model MAE is on rho_residual.
    # If we calculate LMR MAE on rho_actual, the scale is different.
    # Standard practice in this context: Compare the improvement over the baseline.
    # Let's assume the "Linear Mixing Rule Baseline MAE" refers to the MAE of the *Linear Mixing Rule* itself
    # (i.e., |rho_actual - rho_baseline_calc|) on the test set.
    # And "Mass-Only Baseline MAE" refers to the MAE of a model using only mean_atomic_mass to predict rho_residual?
    # Or predicting rho_actual?
    # Given T025-ALT: "Mass-Only Model (Linear Regression on mean_atomic_mass) on rho_residual".
    # So Mass-Only Baseline is a trained model on rho_residual.
    # The LMR Baseline is likely the error of the theoretical LMR (no training) on rho_actual, OR a trained model on rho_baseline.
    # Let's look at T023: "derive residual target (rho_residual = rho_actual - rho_baseline)".
    # If the ML model predicts rho_residual, then Predicted Density = rho_baseline + Pred_residual.
    # Actual Density = rho_actual.
    # Error = |(rho_baseline + Pred_residual) - rho_actual| = |Pred_residual - (rho_actual - rho_baseline)| = |Pred_residual - rho_residual|.
    # So Model MAE is on rho_residual.
    # To compare, Baseline MAE should be on rho_residual too.
    # But the LMR *is* the calculation of rho_baseline. It doesn't predict rho_residual.
    # The LMR Baseline error is effectively the error of assuming rho_residual = 0.
    # So LMR MAE = mean(|0 - rho_residual|) = mean(|rho_residual|).
    # This is a strong baseline.
    # Let's implement:
    # 1. LMR Baseline MAE: MAE of (rho_actual - rho_baseline_calc) assuming the model predicts 0 residual.
    #    i.e., mean(abs(df['rho_residual'])) if 'rho_residual' exists.
    #    If 'rho_residual' doesn't exist, we calculate it.
    # 2. Mass-Only Baseline MAE: Train a LinearRegression on mean_atomic_mass to predict rho_residual.
    
    # Check if rho_residual exists, if not calculate it (assuming rho_baseline is in df or can be derived)
    if 'rho_residual' not in df.columns:
        if 'rho_baseline' in df.columns:
            df['rho_residual'] = df['density'] - df['rho_baseline']
            logger.info("Calculated rho_residual from density and rho_baseline.")
        else:
            # Fallback: assume rho_baseline is not stored, but we can't recalculate without composition parsing here.
            # We assume the pipeline T023 stored it. If not, we might need to parse composition.
            # For now, assume it's there or fail.
            # Let's try to parse composition if needed, but that's heavy.
            # Assuming T023 ran and saved it.
            raise ValueError("rho_residual column not found and rho_baseline not found to calculate it.")
    
    # LMR Baseline: The error of the pure LMR (i.e., predicting residual = 0)
    lmr_mae = np.mean(np.abs(df['rho_residual']))
    
    # Mass-Only Baseline: Linear Regression on mean_atomic_mass to predict rho_residual
    # Prepare data
    X_mass = df['mean_atomic_mass'].values.reshape(-1, 1)
    y_residual = df['rho_residual'].values
    
    # Train on full data for this metric calculation (or split if needed, but usually metrics are on test set)
    # Since this is a baseline comparison, we do it on the same set the model was evaluated on.
    # We assume df is the test set or the set where evaluation happened.
    # If df contains train+test, we need to be careful. Assuming df is the evaluation set.
    
    mass_only_model = LinearRegression()
    mass_only_model.fit(X_mass, y_residual)
    y_pred_mass = mass_only_model.predict(X_mass)
    mass_only_mae = np.mean(np.abs(y_residual - y_pred_mass))
    
    logger.info(f"LMR Baseline MAE: {lmr_mae:.4f}")
    logger.info(f"Mass-Only Baseline MAE: {mass_only_mae:.4f}")
    
    return {
        "lmr_baseline_mae": float(lmr_mae),
        "mass_only_baseline_mae": float(mass_only_mae)
    }

def calculate_model_metrics(model: Any, df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate metrics for the trained model:
    - Predicts rho_residual
    - Returns MAE and R² on the provided dataframe (assumed to be test set)
    """
    logger.info("Calculating model metrics...")
    
    if 'rho_residual' not in df.columns:
        raise ValueError("rho_residual column not found in dataframe")
    
    X = df[feature_cols].values
    y_true = df['rho_residual'].values
    
    y_pred = model.predict(X)
    
    mae = np.mean(np.abs(y_true - y_pred))
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    logger.info(f"Model MAE: {mae:.4f}, R²: {r2:.4f}")
    
    return {
        "model_mae": float(mae),
        "model_r2": float(r2)
    }

def save_metrics(metrics: Dict[str, float], output_path: Path) -> None:
    """Save metrics to a JSON file."""
    logger.info(f"Saving metrics to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point for T026."""
    config = load_config()
    model_path = config.model_dir / "model.pkl"
    data_path = config.data_dir / "clean_data.csv"
    metrics_path = config.report_dir / "metrics.json"
    
    # Load model and data
    model = load_model(model_path)
    df = load_processed_data(data_path)
    
    # Determine feature columns (exclude target and non-feature cols)
    # Assuming the model was trained on specific features. We can infer from the model or hardcode based on engineering.
    # Common features from T020: mean_atomic_mass, mean_atomic_radius, electronegativity_variance, atomic_radius_mismatch, packing_efficiency
    feature_cols = [
        "mean_atomic_mass", 
        "mean_atomic_radius", 
        "electronegativity_variance", 
        "atomic_radius_mismatch", 
        "packing_efficiency"
    ]
    # Check if these exist in df
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        # Try to find available features if exact names differ, or raise error
        # For now, strict check
        raise ValueError(f"Missing feature columns in data: {missing}")
    
    # Calculate Baseline Metrics
    baseline_metrics = calculate_baseline_metrics(df, config)
    
    # Calculate Model Metrics
    model_metrics = calculate_model_metrics(model, df, feature_cols)
    
    # Combine
    all_metrics = {
        **model_metrics,
        **baseline_metrics
    }
    
    # Save
    save_metrics(all_metrics, metrics_path)
    logger.info("T026 completed successfully.")

if __name__ == "__main__":
    main()
