import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from statsmodels.stats.outliers_influence import variance_inflation_factor
from utils.logging_config import get_logger, setup_logging
from utils.config import get_config

# Ensure imports match the API surface provided in the prompt
# We are extending this file, so we must keep existing public names
# and add new ones required for T023.

def load_model_artifacts(base_path: str) -> Dict[str, Any]:
    """Loads saved model artifacts (RF and VLM) from disk."""
    artifact_path = Path(base_path) / "data" / "artifacts"
    models = {}
    if (artifact_path / "rf_model.pkl").exists():
        import pickle
        with open(artifact_path / "rf_model.pkl", "rb") as f:
            models['rf'] = pickle.load(f)
    if (artifact_path / "vlm_model.pkl").exists():
        import pickle
        with open(artifact_path / "vlm_model.pkl", "rb") as f:
            models['vlm'] = pickle.load(f)
    return models

def load_aligned_data(path: str) -> pd.DataFrame:
    """Loads the aligned dataset from NetCDF or CSV."""
    p = Path(path)
    if p.suffix == '.nc':
        import xarray as xr
        ds = xr.open_dataset(p)
        df = ds.to_dataframe().reset_index()
        # Handle potential multi-index flattening issues
        if 'level_0' in df.columns: df.drop(columns=['level_0'], inplace=True)
        return df
    elif p.suffix == '.csv':
        return pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported file format: {p.suffix}")

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes RMSE, R², MAE."""
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred))
    }

def generate_basin_masks(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Generates boolean masks for each ocean basin."""
    basins = df['basin'].unique()
    return {b: df['basin'] == b for b in basins}

def evaluate_models(models: Dict[str, Any], X: np.ndarray, y: np.ndarray) -> Dict[str, Dict[str, float]]:
    """Evaluates all models on given data."""
    results = {}
    for name, model in models.items():
        if name == 'rf':
            preds = model.predict(X)
        elif name == 'vlm':
            # Assuming VLM has predict method similar to sklearn
            preds = model.predict(X)
        else:
            continue
        results[name] = compute_metrics(y, preds)
    return results

def calculate_basin_stratified_metrics(models: Dict[str, Any], df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Calculates metrics stratified by basin."""
    basins = df['basin'].unique()
    results = {b: {} for b in basins}
    for b in basins:
        mask = df['basin'] == b
        X_b = df.loc[mask, feature_cols].values
        y_b = df.loc[mask, 'chlorophyll-a'].values
        if len(X_b) > 0:
            results[b] = evaluate_models(models, X_b, y_b)
    return results

def generate_model_comparison_csv(results: Dict[str, Dict[str, Dict[str, float]]], output_path: str):
    """Generates a CSV comparing model performance across basins."""
    rows = []
    for basin, models_data in results.items():
        for model_name, metrics in models_data.items():
            row = {'basin': basin, 'model': model_name}
            row.update(metrics)
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)

def calculate_basin_variance_metrics(results: Dict[str, Dict[str, Dict[str, float]]]) -> Dict[str, Any]:
    """Calculates variance in R² scores across basins."""
    variance_data = {}
    for model_name in results.get(list(results.keys())[0], {}).keys():
        r2_scores = []
        for basin_data in results.values():
            if model_name in basin_data:
                r2_scores.append(basin_data[model_name]['r2'])
        if len(r2_scores) > 1:
            variance_data[model_name] = {
                'variance': float(np.var(r2_scores)),
                'max_r2': float(max(r2_scores)),
                'min_r2': float(min(r2_scores)),
                'diff': float(max(r2_scores) - min(r2_scores))
            }
    return variance_data

def calculate_variance_inflation_factor(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for each feature.
    Returns a dictionary mapping feature name to VIF score.
    """
    # Add intercept for VIF calculation
    X = df[feature_cols].dropna()
    if X.empty:
        return {col: 0.0 for col in feature_cols}
    
    # Add constant
    X_const = sm.add_constant(X)
    vif_data = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data[col] = float(vif)
        except Exception:
            vif_data[col] = float('inf')
    return vif_data

def run_permutation_importance_analysis(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    logger: logging.Logger,
    vif_threshold: float = 5.0,
    tolerance: float = 0.01
) -> Dict[str, float]:
    """
    Implements permutation importance analysis.
    1. Checks for multicollinearity using VIF.
    2. Computes permutation importance.
    3. Normalizes scores to sum to 1.0.
    4. Verifies the sum is within tolerance.
    """
    from sklearn.inspection import permutation_importance

    # 1. Check Multicollinearity (VIF)
    # We need a DataFrame for VIF calculation
    # Create a temporary DataFrame with the data passed
    # Note: In a real scenario, we might need to handle NaNs carefully before this
    temp_df = pd.DataFrame(X, columns=feature_names)
    
    vif_scores = calculate_variance_inflation_factor(temp_df, feature_names)
    max_vif = max(vif_scores.values()) if vif_scores else 0.0
    
    if max_vif > vif_threshold:
        logger.warning(f"High multicollinearity detected! Max VIF: {max_vif:.2f} (Threshold: {vif_threshold}). Proceeding without PCA as per spec.")
        # Spec says: "proceed without PCA to preserve spec assumptions"
        # So we do nothing, just log.
    else:
        logger.info(f"Multicollinearity check passed. Max VIF: {max_vif:.2f}")

    # 2. Compute Permutation Importance
    # Use the base estimator if the model is a wrapper, but usually sklearn models work directly
    try:
        perm_result = permutation_importance(
            model, X, y, n_repeats=10, random_state=42, n_jobs=-1
        )
        importance_scores = perm_result.importances_mean
    except Exception as e:
        logger.error(f"Permutation importance calculation failed: {e}")
        raise

    # 3. Normalize scores to sum to 1.0
    # Take absolute values to ensure positive importance for normalization if needed,
    # but usually permutation importance can be negative. The spec implies ranking drivers,
    # so we likely care about magnitude. Let's normalize the absolute values.
    abs_importance = np.abs(importance_scores)
    total_importance = np.sum(abs_importance)
    
    if total_importance == 0:
        logger.warning("Total importance is zero. Cannot normalize.")
        normalized_scores = {name: 0.0 for name in feature_names}
    else:
        normalized_scores = {
            name: float(score / total_importance) 
            for name, score in zip(feature_names, abs_importance)
        }

    # 4. Verify sum equals unity within tolerance
    sum_scores = sum(normalized_scores.values())
    is_valid = abs(sum_scores - 1.0) <= tolerance
    
    verification_msg = (
        f"Importance Verification: Sum={sum_scores:.6f}, "
        f"Tolerance={tolerance}, Valid={is_valid}"
    )
    logger.info(verification_msg)

    return normalized_scores

def main():
    setup_logging()
    logger = get_logger("evaluation")
    config = get_config()
    
    # Paths
    base_path = Path(config.project_root)
    data_path = base_path / "data" / "processed" / "aligned_dataset.nc"
    artifacts_path = base_path / "data" / "artifacts"
    logs_dir = base_path / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Permutation Importance Analysis (T023)")

    # Load Data
    df = load_aligned_data(str(data_path))
    feature_cols = ['temp', 'salinity', 'nutrients', 'chlorophyll-a'] # Adjust based on actual schema
    # Filter to only available columns
    available_features = [c for c in ['temp', 'salinity', 'nutrients'] if c in df.columns]
    target_col = 'chlorophyll-a'
    
    if not available_features or target_col not in df.columns:
        logger.error("Required features or target column missing from dataset.")
        return

    X = df[available_features].dropna().values
    y = df.loc[X.index, target_col].values # Align indices after dropna

    if len(X) == 0:
        logger.error("No valid data points after cleaning.")
        return

    # Load Model (Random Forest as per T018)
    models = load_model_artifacts(str(base_path))
    if 'rf' not in models:
        logger.error("Random Forest model not found. Cannot run importance analysis.")
        return
    
    rf_model = models['rf']

    # Run Analysis
    importance_scores = run_permutation_importance_analysis(
        rf_model, 
        X, 
        y, 
        available_features, 
        logger,
        vif_threshold=5.0,
        tolerance=0.01
    )

    # Log Verification Result
    log_path = logs_dir / "importance_verification.log"
    with open(log_path, 'a') as f:
        f.write(f"Task T023 - {datetime.now()}\n")
        f.write(f"Features: {available_features}\n")
        for feat, score in importance_scores.items():
            f.write(f"{feat}: {score:.6f}\n")
        f.write(f"Sum: {sum(importance_scores.values()):.6f}\n")
        f.write(f"Status: {'PASS' if abs(sum(importance_scores.values()) - 1.0) <= 0.01 else 'FAIL'}\n")
        f.write("-" * 40 + "\n")

    # Save Artifact (Optional but good practice)
    output_artifact = artifacts_path / "feature_importance.json"
    with open(output_artifact, 'w') as f:
        json.dump(importance_scores, f, indent=2)
    
    logger.info(f"Permutation importance analysis complete. Results saved to {output_artifact}")

if __name__ == "__main__":
    main()
