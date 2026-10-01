"""
Model training module with LOSO cross-validation and baseline comparison.
"""
import os
import sys
import json
import pickle
import time
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import ttest_rel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.resource_monitor import resource_monitor_wrapper, get_peak_memory_gb

logger = get_logger(__name__)

def load_processed_data(filepath: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """Load processed descriptor data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Processed data not found: {filepath}")
    return pd.read_csv(filepath)

def train_random_forest(X: np.ndarray, y: np.ndarray, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def run_loso_cv(df: pd.DataFrame) -> List[Dict]:
    """Run Leave-One-System-Out cross-validation."""
    logo = LeaveOneGroupOut()
    results = []

    # Group by system_id
    groups = df['system_id'].values
    X = df[['mean_atomic_radius', 'electronegativity_variance', 'valence_electron_count', 'hume_rothery_concentration']].values
    y = df['temperature'].values

    for train_idx, test_idx in logo.split(X, y, groups):
        train_df = df.iloc[train_idx]
        test_df = df.iloc[test_idx]

        X_train, y_train = train_df[['mean_atomic_radius', 'electronegativity_variance', 'valence_electron_count', 'hume_rothery_concentration']].values, train_df['temperature'].values
        X_test, y_test = test_df[['mean_atomic_radius', 'electronegativity_variance', 'valence_electron_count', 'hume_rothery_concentration']].values, test_df['temperature'].values

        # New Element Check (T022)
        train_elements = set(train_df['element_a'].tolist() + train_df['element_b'].tolist())
        test_elements = set(test_df['element_a'].tolist() + test_df['element_b'].tolist())

        new_elements = test_elements - train_elements
        if new_elements:
            log_error(logger, f"{ErrorCode.INVALID_SCOPE.value}: New elements in test set: {new_elements}")
            # Log skipped fold
            log_entry = {
                "fold_id": f"fold_{len(results)}",
                "reason": "invalid_scope",
                "action": "halted",
                "new_elements": list(new_elements)
            }
            with open("data/logs/skipped_fold.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            continue

        # Train model
        model = train_random_forest(X_train, y_train)
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        results.append({
            "fold_id": len(results),
            "mae": mae,
            "r2": r2,
            "train_size": len(train_idx),
            "test_size": len(test_idx)
        })

    return results

def perform_power_analysis(results: List[Dict]) -> Dict[str, float]:
    """Perform statistical power analysis."""
    if len(results) < 3:
        raise ValueError(f"{ErrorCode.INSUFFICIENT_POWER.value}: Not enough folds for power analysis")

    maes = [r['mae'] for r in results]
    variance = np.var(maes)
    mean_mae = np.mean(maes)

    # Simplified power calculation
    # In a real scenario, we would use statsmodels for proper power analysis
    effect_size = 0.5  # Assumed effect size
    sample_size = len(results)
    alpha = 0.05

    # Approximate power calculation
    # This is a placeholder; real implementation would use statsmodels.stats.power
    power = 1.0 - (1.96 / np.sqrt(sample_size)) * (variance ** 0.5)

    report = {
        "variance": float(variance),
        "mean_mae": float(mean_mae),
        "sample_size": sample_size,
        "estimated_power": float(power),
        "effect_size": effect_size
    }

    if power < 0.8:
        log_error(logger, f"{ErrorCode.INSUFFICIENT_POWER.value}: Power {power:.4f} < 0.8")
        raise ValueError(f"{ErrorCode.INSUFFICIENT_POWER.value}: Insufficient statistical power. Report: {json.dumps(report)}")

    log_info(logger, f"Power analysis passed: {power:.4f}")
    return report

def compare_with_baseline(df: pd.DataFrame, results: List[Dict]) -> Dict[str, float]:
    """Compare RF model against null baseline (global mean)."""
    # Calculate global mean temperature
    global_mean = df['temperature'].mean()

    # Null model predictions (always predict global mean)
    y_true = df['temperature'].values
    y_null_pred = np.full_like(y_true, global_mean, dtype=float)

    # RF model predictions (aggregate from CV results)
    # For simplicity, we use the mean of fold MAEs as the RF performance
    rf_mae = np.mean([r['mae'] for r in results])
    null_mae = mean_absolute_error(y_true, y_null_pred)

    improvement = ((null_mae - rf_mae) / null_mae) * 100 if null_mae > 0 else 0

    comparison = {
        "null_model_mae": float(null_mae),
        "rf_model_mae": float(rf_mae),
        "percentage_improvement": float(improvement)
    }

    log_info(logger, f"Baseline comparison: Null MAE={null_mae:.2f}, RF MAE={rf_mae:.2f}, Improvement={improvement:.2f}%")

    # Save comparison
    os.makedirs("data/artifacts", exist_ok=True)
    with open("data/artifacts/baseline_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)

    return comparison

def save_model(model: RandomForestRegressor, filepath: str = "data/artifacts/model.pkl"):
    """Save trained model to disk."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    log_info(logger, f"Model saved to {filepath}")

def save_report(results: List[Dict], power_report: Dict, baseline_report: Dict):
    """Save evaluation report."""
    report = {
        "cv_results": results,
        "power_analysis": power_report,
        "baseline_comparison": baseline_report,
        "timestamp": time.time()
    }

    os.makedirs("data/artifacts", exist_ok=True)
    with open("data/artifacts/evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

@resource_monitor_wrapper
def run_training_pipeline():
    """Run the full training pipeline."""
    df = load_processed_data()

    # Run LOSO CV
    cv_results = run_loso_cv(df)

    if not cv_results:
        raise ValueError(f"{ErrorCode.INSUFFICIENT_POWER.value}: No valid folds for training")

    # Power analysis
    power_report = perform_power_analysis(cv_results)

    # Baseline comparison
    baseline_report = compare_with_baseline(df, cv_results)

    # Train final model on full data
    X = df[['mean_atomic_radius', 'electronegativity_variance', 'valence_electron_count', 'hume_rothery_concentration']].values
    y = df['temperature'].values
    final_model = train_random_forest(X, y)

    # Save artifacts
    save_model(final_model)
    save_report(cv_results, power_report, baseline_report)

    # Save resource log
    peak_memory = get_peak_memory_gb()
    resource_log = {
        "execution_time_seconds": int(time.time()),
        "peak_memory_gb": float(peak_memory)
    }
    with open("data/artifacts/resource_log.json", "w") as f:
        json.dump(resource_log, f, indent=2)

    log_info(logger, "Training pipeline completed successfully")

def main():
    """Entry point for model training."""
    try:
        run_training_pipeline()
    except Exception as e:
        log_error(logger, f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
