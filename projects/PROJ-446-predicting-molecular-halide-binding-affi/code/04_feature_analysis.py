import os
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import partial_dependence, PartialDependenceDisplay
import matplotlib.pyplot as plt

from utils.config import get_path, get_data_path, get_code_path, is_simulated_mode
from utils.logger import get_logger
from utils.validators import load_schema, validate_dataset

logger = get_logger(__name__)

# Physical plausibility rules: (feature_name, expected_sign)
# expected_sign: 1 means positive correlation with affinity (log K), -1 means negative.
# Physics basis:
# - charge_density: Higher charge density -> stronger electrostatic attraction -> higher affinity (positive)
# - cavity_volume: Larger cavity -> better steric match for larger halides, but if cavity is too large for a specific halide, affinity drops.
#   However, in the context of "binding affinity" generally, a larger accessible cavity often correlates with ability to bind larger, more polarizable ions.
#   But strictly electrostatic: if the cavity is too big, the ion is too far from donors -> weaker binding.
#   For this task, we assume the "top feature" logic checks against a specific hypothesis.
#   We will define a map of known physical expectations.
PHYSICAL_EXPECTATIONS = {
    "charge_density": 1,  # Higher charge density -> stronger binding (positive sign)
    "cavity_volume": -1,  # Larger cavity (if too large relative to ion) -> weaker binding (negative sign)
    "h_bond_donor_count": 1,  # More donors -> stronger binding (positive)
    "molecular_weight": 0,  # Ambiguous, skip strict check
    "polarizability": 1,  # Higher polarizability -> stronger dispersion -> stronger binding (positive)
}

def load_preprocessed_data() -> pd.DataFrame:
    """Load the processed halide binding dataset."""
    data_path = get_data_path("processed/halide_binding_data.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} records from {data_path}")
    return df

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """Identify feature columns (exclude target and metadata)."""
    target_cols = ["log_k", "delta_g", "affinity_value"]
    meta_cols = ["host_id", "smiles", "inchi", "halide_identity", "solvent"]
    feature_cols = [c for c in df.columns if c not in target_cols and c not in meta_cols]
    # Ensure we only select numeric columns
    numeric_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    return numeric_cols

def run_feature_stability_analysis(
    df: pd.DataFrame,
    feature_cols: List[str],
    n_bootstrap: int = 100,
    random_state: int = 42
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Run bootstrap resampling to calculate feature stability (CV).
    Returns: (mean_importance, cv_importance)
    """
    logger.info(f"Running feature stability analysis with {n_bootstrap} bootstraps...")
    np.random.seed(random_state)

    importance_sums = {col: 0.0 for col in feature_cols}
    importance_squares = {col: 0.0 for col in feature_cols}

    X = df[feature_cols]
    # Assume 'log_k' is the target
    if "log_k" not in df.columns:
        raise ValueError("Target column 'log_k' not found in dataframe")
    y = df["log_k"]

    model = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=-1)

    for i in range(n_bootstrap):
        idx = np.random.choice(len(X), size=len(X), replace=True)
        X_boot = X.iloc[idx]
        y_boot = y.iloc[idx]

        model.fit(X_boot, y_boot)
        importances = model.feature_importances_

        for j, col in enumerate(feature_cols):
            imp = importances[j]
            importance_sums[col] += imp
            importance_squares[col] += imp ** 2

    mean_importance = {col: s / n_bootstrap for col, s in importance_sums.items()}
    variance = {col: (squares / n_bootstrap) - (mean ** 2) for col, s, mean in zip(
        importance_squares, importance_squares.values(), mean_importance.values()
    )}
    std_dev = {col: np.sqrt(var) for col, var in variance.items()}
    cv = {col: (std / mean) if mean > 1e-9 else 0.0 for col, std, mean in zip(std_dev, std_dev.values(), mean_importance.values())}

    logger.info("Feature stability analysis complete.")
    return mean_importance, cv

def check_physical_plausibility(mean_importance: Dict[str, float], cv: Dict[str, float]) -> Dict[str, Any]:
    """
    Identify the top feature by mean importance and verify its sign against physical expectations.
    Note: Random Forest feature importances are non-negative by definition.
    To check the 'sign' of the relationship, we must calculate the correlation or a linear coefficient
    for the top feature.
    """
    if not mean_importance:
        return {"status": "error", "reason": "No features found"}

    # Identify top feature by importance
    top_feature = max(mean_importance, key=mean_importance.get)
    top_importance = mean_importance[top_feature]
    top_cv = cv.get(top_feature, 0.0)

    logger.info(f"Top feature: {top_feature} (Importance: {top_importance:.4f}, CV: {top_cv:.4f})")

    # Calculate correlation to determine the sign of the relationship
    # We use Pearson correlation for simplicity
    df = load_preprocessed_data()
    if top_feature not in df.columns or "log_k" not in df.columns:
        return {"status": "error", "reason": "Missing columns for correlation check"}

    correlation = df[top_feature].corr(df["log_k"])
    observed_sign = 1 if correlation > 0 else (-1 if correlation < 0 else 0)

    # Get expected sign
    expected_sign = PHYSICAL_EXPECTATIONS.get(top_feature, 0)

    result = {
        "top_feature": top_feature,
        "importance": top_importance,
        "cv": top_cv,
        "correlation": correlation,
        "observed_sign": observed_sign,
        "expected_sign": expected_sign,
        "is_plausible": True,
        "reason": "OK"
    }

    if expected_sign == 0:
        result["reason"] = "No strict physical expectation defined for this feature"
    elif observed_sign == 0:
        result["is_plausible"] = False
        result["reason"] = "Observed correlation is zero (no relationship)"
    elif observed_sign != expected_sign:
        result["is_plausible"] = False
        result["reason"] = f"Sign mismatch: Observed ({observed_sign}) != Expected ({expected_sign}) for {top_feature}"
    else:
        result["reason"] = f"Sign matches expectation ({expected_sign})"

    return result

def save_feature_analysis_results(
    mean_importance: Dict[str, float],
    cv: Dict[str, float],
    plausibility_check: Dict[str, Any],
    output_path: str
):
    """Save analysis results to JSON."""
    results = {
        "feature_stability": {
            "mean_importance": mean_importance,
            "coefficient_of_variation": cv
        },
        "physical_plausibility_check": plausibility_check
    }

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved feature analysis results to {output_path}")

def generate_partial_dependence_plots(
    df: pd.DataFrame,
    model: RandomForestRegressor,
    feature_cols: List[str],
    output_dir: str
):
    """Generate PDPs for top 2 features."""
    os.makedirs(output_dir, exist_ok=True)

    # Identify top 2 features
    sorted_features = sorted(feature_cols, key=lambda k: model.feature_importances_[feature_cols.index(k)], reverse=True)[:2]

    if len(sorted_features) < 2:
        logger.warning("Not enough features to generate 2 PDPs")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    PartialDependenceDisplay.from_estimator(model, df[feature_cols], features=sorted_features, ax=axes)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "partial_dependence_plots.png")
    plt.savefig(plot_path)
    plt.close()
    logger.info(f"Saved PDPs to {plot_path}")

def main():
    """Main entry point for Feature Analysis."""
    logger.info("Starting Feature Analysis (US3)...")

    # Load data
    df = load_preprocessed_data()
    feature_cols = get_feature_columns(df)

    if not feature_cols:
        logger.error("No feature columns found. Exiting.")
        sys.exit(1)

    # Run stability analysis
    mean_importance, cv = run_feature_stability_analysis(df, feature_cols)

    # Run Physical Plausibility Check (T025)
    plausibility_result = check_physical_plausibility(mean_importance, cv)

    # Save results
    output_path = get_data_path("processed/feature_analysis.json")
    save_feature_analysis_results(mean_importance, cv, plausibility_result, output_path)

    # Generate PDPs
    # Train a quick model for PDPs if not already available (or load from T022)
    # For T025 standalone, we train a RF to generate PDPs
    X = df[feature_cols]
    y = df["log_k"]
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X, y)

    figures_dir = get_path("docs/paper/figures")
    generate_partial_dependence_plots(df, rf_model, feature_cols, figures_dir)

    logger.info("Feature Analysis completed successfully.")

if __name__ == "__main__":
    main()