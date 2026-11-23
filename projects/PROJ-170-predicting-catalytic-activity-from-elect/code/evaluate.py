import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import r2_score, mean_absolute_error, pearsonr
import shap
import matplotlib.pyplot as plt

from config import get_project_root, get_output_path, get_data_path
from logging_config import get_logger

logger = get_logger(__name__)

def load_test_split_metadata() -> Dict[str, Any]:
    """Load the metadata saved during the train/test split."""
    root = get_project_root()
    metadata_path = root / "outputs" / "split_metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Split metadata not found at {metadata_path}")
    with open(metadata_path, "r") as f:
        return json.load(f)

def load_test_data() -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """Load test features and target."""
    root = get_project_root()
    # Assuming the split metadata contains the path or we load from a standard location
    # Based on T024, the split happens in memory but we need the actual data for evaluation.
    # The task T020 produces aligned_dataset.csv. We need to load it and filter by the test indices.
    # However, T024 likely saved the test set or indices. Let's assume we load the full aligned set
    # and the metadata tells us which rows are test.
    
    # Re-reading T024: "split into train/test sets". Usually, this implies saving the splits or indices.
    # Let's load the split metadata to find the test indices.
    metadata = load_test_split_metadata()
    
    # Load the full aligned dataset
    data_path = get_data_path() / "processed" / "aligned_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Get test indices from metadata (assuming it saved indices or a mask)
    # If metadata has 'test_indices', use them.
    if 'test_indices' in metadata:
        test_df = df.iloc[metadata['test_indices']].reset_index(drop=True)
    else:
        # Fallback: if metadata has a 'test_mask' or similar, or if the split was saved as a file.
        # Given the constraints, we assume test_indices are in metadata.
        raise ValueError("test_indices not found in split_metadata.json")

    # Separate features and target
    # Target is 'energy_change' based on T015
    target_col = 'energy_change'
    feature_cols = [col for col in test_df.columns if col != target_col]
    
    X_test = test_df[feature_cols]
    y_test = test_df[target_col]
    
    return X_test, y_test, feature_cols

def load_models() -> Tuple[Any, Any]:
    """Load the full XGBoost model and the reduced XGBoost model."""
    root = get_project_root()
    models_dir = root / "code" / "models"
    
    full_model_path = models_dir / "best_xgboost.json"
    reduced_model_path = models_dir / "best_reduced_xgboost.json"
    
    if not full_model_path.exists():
        raise FileNotFoundError(f"Full model not found at {full_model_path}")
    if not reduced_model_path.exists():
        raise FileNotFoundError(f"Reduced model not found at {reduced_model_path}")
    
    full_model = xgb.XGBRegressor()
    full_model.load_model(str(full_model_path))
    
    reduced_model = xgb.XGBRegressor()
    reduced_model.load_model(str(reduced_model_path))
    
    return full_model, reduced_model

def compute_absolute_errors(y_true: pd.Series, y_pred: np.ndarray) -> pd.Series:
    """Compute absolute errors."""
    return pd.Series(np.abs(y_true - y_pred), index=y_true.index)

def run_statistical_test_paired(errors_full: pd.Series, errors_reduced: pd.Series) -> Dict[str, Any]:
    """Run paired statistical test (t-test or Wilcoxon) on error differences."""
    from scipy import stats
    
    diff = errors_full - errors_reduced
    normality_p = stats.shapiro(diff)[1]
    
    if normality_p > 0.05:
        stat, p_val = stats.ttest_rel(errors_full, errors_reduced)
        test_type = "paired_t_test"
    else:
        stat, p_val = stats.wilcoxon(errors_full, errors_reduced)
        test_type = "wilcoxon_signed_rank"
    
    return {
        "test_type": test_type,
        "statistic": float(stat),
        "p_value": float(p_val),
        "normality_p_value": float(normality_p)
    }

def run_statistical_test_absolute(errors: pd.Series) -> Dict[str, Any]:
    """Run normality check on absolute errors."""
    from scipy import stats
    stat, p_val = stats.shapiro(errors)
    decision = "use_t_test" if p_val > 0.05 else "use_wilcoxon"
    return {
        "test_type": "shapiro_absolute",
        "statistic": float(stat),
        "p_value": float(p_val),
        "decision": decision
    }

def save_metrics(metrics: Dict[str, Any]) -> None:
    """Save metrics to outputs/metrics.json."""
    root = get_project_root()
    output_path = get_output_path()
    metrics_path = output_path / "metrics.json"
    
    # Load existing metrics if present to append
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            existing = json.load(f)
        existing.update(metrics)
        metrics = existing
    
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

def rank_descriptors_by_shap(shap_values: np.ndarray, feature_names: List[str]) -> List[Dict[str, Any]]:
    """Rank descriptors by mean absolute SHAP impact."""
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    rankings = []
    for i, name in enumerate(feature_names):
        rankings.append({"feature": name, "mean_abs_shap": float(mean_abs_shap[i])})
    rankings.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
    return rankings

def generate_feature_importance_plot(rankings: List[Dict[str, Any]], top_n: int = 5) -> Path:
    """Generate a bar plot of top N descriptors."""
    root = get_project_root()
    output_path = get_output_path()
    plot_path = output_path / "feature_importance.png"
    
    top_features = rankings[:top_n]
    features = [r["feature"] for r in top_features]
    values = [r["mean_abs_shap"] for r in top_features]
    
    plt.figure(figsize=(10, 6))
    plt.barh(features, values)
    plt.xlabel("Mean Absolute SHAP Impact")
    plt.ylabel("Descriptor")
    plt.title(f"Top {top_n} Feature Importance")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    
    logger.info(f"Feature importance plot saved to {plot_path}")
    return plot_path

def train_reduced_model_with_tuning(X_train: pd.DataFrame, y_train: pd.Series, feature_subset: List[str]) -> Any:
    """Train a reduced model with independent hyperparameter tuning."""
    X_sub = X_train[feature_subset]
    
    # Grid search for reduced model
    param_grid = {
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1],
        "n_estimators": [50, 100, 200]
    }
    
    model = xgb.XGBRegressor(random_state=42, objective='reg:squarederror')
    from sklearn.model_selection import GridSearchCV
    
    grid_search = GridSearchCV(
        model, param_grid, cv=3, scoring='r2', n_jobs=-1
    )
    grid_search.fit(X_sub, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"Reduced model best params: {grid_search.best_params_}")
    return best_model

def run_evaluation() -> Dict[str, Any]:
    """Main evaluation function: compute metrics, SHAP, and verify SC-003."""
    # 1. Load data
    X_test, y_test, feature_cols = load_test_data()
    full_model, reduced_model = load_models()
    
    # 2. Get reduced model features (we need to know which features were used)
    # The reduced model was trained on a subset. We need to infer this or load it.
    # T036 says "Train a reduced model using only the top-ranked SHAP descriptors".
    # We need to know how many top descriptors were used. 
    # Since T036 is already done, we assume the reduced model's feature names are stored or we can infer from the model's feature_importances_.
    # However, XGBRegressor doesn't store feature names after saving in JSON easily without re-instantiating with them.
    # Let's assume the reduced model was trained on the top 5 features (common practice) or we load the list from a file if T036 saved it.
    # To be robust, let's look at the reduced model's feature_importances_ and map them to the full feature list.
    # But we need the mapping. 
    # Alternative: T036 should have saved the list of features used. Let's assume it saved `outputs/reduced_features.json` or similar.
    # If not, we can't reliably know. 
    # Let's assume the reduced model was trained on the top 5 features from T034.
    # We need to re-run SHAP on the FULL model to get the top 5 features again, as T034 did.
    
    # Re-compute SHAP on full model to get top features (since we don't have the saved list)
    # We need the full training data for SHAP background.
    # T024 saved split metadata. Let's load the training data similarly.
    metadata = load_test_split_metadata()
    data_path = get_data_path() / "processed" / "aligned_dataset.csv"
    df = pd.read_csv(data_path)
    train_indices = metadata.get('train_indices')
    if train_indices is None:
        raise ValueError("train_indices not found in split_metadata.json")
    X_train = df.iloc[train_indices][feature_cols]
    
    # Compute SHAP for full model
    explainer = shap.TreeExplainer(full_model)
    shap_values = explainer.shap_values(X_train)
    rankings = rank_descriptors_by_shap(shap_values, feature_cols)
    top_5_features = [r["feature"] for r in rankings[:5]]
    
    # 3. Predictions
    y_pred_full = full_model.predict(X_test)
    y_pred_reduced = reduced_model.predict(X_test)
    
    # 4. Metrics
    r2_full = r2_score(y_test, y_pred_full)
    r2_reduced = r2_score(y_test, y_pred_reduced)
    mae_full = mean_absolute_error(y_test, y_pred_full)
    mae_reduced = mean_absolute_error(y_test, y_pred_reduced)
    
    # 5. SC-003 Verification
    ratio = r2_reduced / r2_full if r2_full != 0 else 0.0
    sc003_status = "PASSED" if ratio >= 0.50 else "FAILED"
    
    logger.info(f"SC-003 Verification: Reduced R2={r2_reduced:.4f}, Full R2={r2_full:.4f}, Ratio={ratio:.4f}, Status={sc003_status}")
    
    # 6. Prepare metrics dict
    metrics = {
        "full_model": {
            "r2": float(r2_full),
            "mae": float(mae_full)
        },
        "reduced_model": {
            "r2": float(r2_reduced),
            "mae": float(mae_reduced)
        },
        "sc003_verification": {
            "reduced_r2": float(r2_reduced),
            "full_r2": float(r2_full),
            "ratio": float(ratio),
            "status": sc003_status,
            "threshold": 0.50
        }
    }
    
    # 7. Save metrics
    save_metrics(metrics)
    
    return metrics

def main():
    """Entry point for evaluation script."""
    try:
        metrics = run_evaluation()
        print(json.dumps(metrics, indent=2))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()