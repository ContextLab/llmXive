import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score

# Import config from the project root structure
# Assuming the script runs from the code directory or we adjust sys.path
# We need to import config to get paths and random seed
try:
    from config import RANDOM_SEED, DATA_PROCESSED, RESULTS_DIR
except ImportError:
    # Fallback if running as script directly without package init
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import RANDOM_SEED, DATA_PROCESSED, RESULTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data_for_sensitivity() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the two specific datasets required for sensitivity analysis:
    1. raw_for_sensitivity.csv (pre-imputation, raw state)
    2. sensitivity_dataset.csv (imputed, low-confidence excluded)
    """
    raw_path = Path(DATA_PROCESSED) / "raw_for_sensitivity.csv"
    sens_path = Path(DATA_PROCESSED) / "sensitivity_dataset.csv"

    if not raw_path.exists():
        raise FileNotFoundError(f"Required file not found: {raw_path}")
    if not sens_path.exists():
        raise FileNotFoundError(f"Required file not found: {sens_path}")

    df_raw = pd.read_csv(raw_path)
    df_sens = pd.read_csv(sens_path)

    logger.info(f"Loaded raw dataset: {len(df_raw)} rows")
    logger.info(f"Loaded sensitivity dataset: {len(df_sens)} rows")

    return df_raw, df_sens

def prepare_features_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepares feature matrix X and target vector y.
    Assumes the dataframe has been preprocessed with encoded features.
    If not, it expects standard columns. We assume T016/T017 have run or
    we are loading the encoded version.
    Based on T016, features are encoded. We need to identify feature columns.
    For this specific task, we assume the CSVs contain the encoded features
    and the target 'yield_strength_mpa'.
    """
    # Identify feature columns (exclude target and metadata)
    target_col = 'yield_strength_mpa'
    exclude_cols = [target_col, 'alloy_family', 'sample_id'] # sample_id might not exist
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        # Fallback if columns are not as expected, try numeric columns
        feature_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col).tolist()

    X = df[feature_cols].values
    y = df[target_col].values

    return X, y

def train_and_evaluate_model(X: np.ndarray, y: np.ndarray, model_name: str) -> Dict[str, float]:
    """
    Trains a specific model type using Cross-Validation to get R2 score.
    We use CV to ensure the metric is robust and comparable between datasets.
    """
    models = {
        'RandomForest': RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1),
        'GradientBoosting': GradientBoostingRegressor(n_estimators=100, random_state=RANDOM_SEED),
        'Ridge': Ridge(alpha=1.0, random_state=RANDOM_SEED)
    }

    if model_name not in models:
        raise ValueError(f"Unknown model: {model_name}")

    model = models[model_name]

    # Use 5-fold CV to get a robust R2 estimate without needing a fixed train/test split here
    # The split logic was done in T017, but for sensitivity of the *process*,
    # we evaluate the model's ability to generalize on the specific dataset provided.
    # Using cross_val_score is standard for comparing dataset quality impacts.
    try:
        scores = cross_val_score(model, X, y, cv=5, scoring='r2', n_jobs=-1)
        mean_r2 = float(np.mean(scores))
        std_r2 = float(np.std(scores))
        return {'r2_mean': mean_r2, 'r2_std': std_r2}
    except Exception as e:
        logger.error(f"Error evaluating {model_name}: {e}")
        return {'r2_mean': np.nan, 'r2_std': np.nan}

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Main logic for T038:
    1. Load raw and sensitivity datasets.
    2. Train models (RF, GB, Ridge) on BOTH datasets.
    3. Compare R2 scores to quantify bias introduced by imputation/filtering.
    4. Save results to results/sensitivity_analysis.json
    """
    logger.info("Starting Sensitivity Analysis (T038)...")

    try:
        df_raw, df_sens = load_data_for_sensitivity()
    except FileNotFoundError as e:
        logger.error(str(e))
        return {"status": "failed", "error": str(e)}

    results = {
        "status": "completed",
        "datasets": {
            "raw": {"rows": len(df_raw)},
            "sensitivity": {"rows": len(df_sens)}
        },
        "models": {}
    }

    models_to_test = ['RandomForest', 'GradientBoosting', 'Ridge']

    for model_name in models_to_test:
        logger.info(f"Processing model: {model_name}")

        # Evaluate on Raw
        X_raw, y_raw = prepare_features_targets(df_raw)
        metrics_raw = train_and_evaluate_model(X_raw, y_raw, model_name)

        # Evaluate on Sensitivity (Imputed/Filtered)
        X_sens, y_sens = prepare_features_targets(df_sens)
        metrics_sens = train_and_evaluate_model(X_sens, y_sens, model_name)

        # Calculate Bias (Difference in performance)
        # Bias = R2_raw - R2_sens (Positive means raw performed better, negative means imputed helped or raw was noisier)
        bias = metrics_raw['r2_mean'] - metrics_sens['r2_mean']

        results["models"][model_name] = {
            "raw_performance": metrics_raw,
            "sensitivity_performance": metrics_sens,
            "bias_r2": bias,
            "interpretation": "Imputation/Filtering caused performance drop" if bias > 0.05 else \
                            "Imputation/Filtering improved performance (denoising)" if bias < -0.05 else \
                            "Minimal impact from imputation/filtering"
        }

    # Save results
    output_path = Path(RESULTS_DIR) / "sensitivity_analysis.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity Analysis complete. Results saved to {output_path}")
    return results

def main():
    """Entry point for the script."""
    results = run_sensitivity_analysis()
    if results.get("status") == "failed":
        sys.exit(1)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
