import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from sklearn.linear_model import RidgeCV, Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error
import pandas as pd
from config import ensure_directories
from utils import get_logger, read_csv, write_json

logger = get_logger(__name__)

def load_cleaned_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned data CSV."""
    logger.info(f"Loading cleaned data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} subjects")
    return df

def prepare_model_data(df: pd.DataFrame, target_col: str = "MWQ_Score") -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare X (features) and y (target) from the dataframe.
    Returns scaled features, target, and feature names.
    """
    feature_cols = ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
    # Ensure all required columns exist
    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")

    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def run_ridge_regression_with_nested_cv(X: np.ndarray, y: np.ndarray, feature_names: List[str], alphas: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Run Ridge regression with nested 5-fold CV for alpha tuning.
    Returns metrics and best alpha.
    """
    if alphas is None:
        alphas = [0.1, 1.0, 10.0, 100.0]

    outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    inner_cv = KFold(n_splits=5, shuffle=True, random_state=42)

    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('ridge', RidgeCV(alphas=alphas, cv=inner_cv))
    ])

    # Outer loop for evaluation
    mae_scores = []
    r2_scores = []
    y_pred_list = []
    y_true_list = []

    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)

        mae_scores.append(mean_absolute_error(y_test, y_pred))
        r2_scores.append(r2_score(y_test, y_pred))
        y_pred_list.extend(y_pred)
        y_true_list.extend(y_test)

    return {
        "mean_mae": float(np.mean(mae_scores)),
        "std_mae": float(np.std(mae_scores)),
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores)),
        "pearson_r": float(np.corrcoef(y_true_list, y_pred_list)[0, 1]),
        "best_alpha": float(pipe.named_steps['ridge'].alpha_),
        "predictions": y_pred_list,
        "actuals": y_true_list
    }

def run_null_distribution_analysis(X: np.ndarray, y: np.ndarray, feature_names: List[str], n_permutations: int = 1000, alphas: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Generate null distribution by permuting y and running the full pipeline.
    """
    if alphas is None:
        alphas = [0.1, 1.0, 10.0, 100.0]

    outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    inner_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('ridge', RidgeCV(alphas=alphas, cv=inner_cv))
    ])

    null_maes = []
    logger.info(f"Running {n_permutations} permutations for null distribution...")

    for i in range(n_permutations):
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i + 1}/{n_permutations}")
        
        y_perm = y.copy()
        np.random.shuffle(y_perm)
        
        maes = []
        for train_idx, test_idx in outer_cv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_perm_test = y_perm[train_idx], y_perm[test_idx]
            
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            maes.append(mean_absolute_error(y_perm_test, y_pred))
        
        null_maes.append(np.mean(maes))

    return {
        "null_mean_mae": float(np.mean(null_maes)),
        "null_std_mae": float(np.std(null_maes)),
        "null_distribution": null_maes
    }

def run_reduced_model_analysis(X: np.ndarray, y: np.ndarray, feature_names: List[str], alphas: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Run Reduced Model: Y ~ FD + DVARS + Age + Sex (excluding Global_Signal_SD).
    Returns metrics for the reduced model.
    """
    # Identify indices for covariates only (exclude Global_Signal_SD which is usually first)
    # Based on prepare_model_data order: ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age", "Sex"]
    covariate_indices = [1, 2, 3, 4] # Mean_FD, Mean_DVARS, Age, Sex
    
    if alphas is None:
        alphas = [0.1, 1.0, 10.0, 100.0]

    X_reduced = X[:, covariate_indices]
    reduced_feature_names = [feature_names[i] for i in covariate_indices]

    outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    inner_cv = KFold(n_splits=5, shuffle=True, random_state=42)

    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('ridge', RidgeCV(alphas=alphas, cv=inner_cv))
    ])

    mae_scores = []
    r2_scores = []
    y_pred_list = []
    y_true_list = []

    for train_idx, test_idx in outer_cv.split(X_reduced):
        X_train, X_test = X_reduced[train_idx], X_reduced[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)

        mae_scores.append(mean_absolute_error(y_test, y_pred))
        r2_scores.append(r2_score(y_test, y_pred))
        y_pred_list.extend(y_pred)
        y_true_list.extend(y_test)

    return {
        "mean_mae": float(np.mean(mae_scores)),
        "std_mae": float(np.std(mae_scores)),
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores)),
        "pearson_r": float(np.corrcoef(y_true_list, y_pred_list)[0, 1]),
        "best_alpha": float(pipe.named_steps['ridge'].alpha_),
        "feature_names": reduced_feature_names,
        "predictions": y_pred_list,
        "actuals": y_true_list
    }

def calculate_delta_r2(full_model_results: Dict, reduced_model_results: Dict) -> float:
    """
    Calculate Delta R² = R²_full - R²_reduced.
    """
    delta_r2 = full_model_results["mean_r2"] - reduced_model_results["mean_r2"]
    return float(delta_r2)

def main():
    """
    Main entry point for T023: Reduced Model Analysis and Delta R² calculation.
    """
    ensure_directories()
    
    data_path = "data/processed/cleaned_data.csv"
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "delta_r2.json"

    logger.info("Starting Reduced Model Analysis (T023)...")

    try:
        df = load_cleaned_data(data_path)
        X, y, feature_names = prepare_model_data(df)
        
        logger.info("Running Full Model (for reference)...")
        full_results = run_ridge_regression_with_nested_cv(X, y, feature_names)
        logger.info(f"Full Model R²: {full_results['mean_r2']:.4f}")

        logger.info("Running Reduced Model (Y ~ FD + DVARS + Age + Sex)...")
        reduced_results = run_reduced_model_analysis(X, y, feature_names)
        logger.info(f"Reduced Model R²: {reduced_results['mean_r2']:.4f}")

        delta_r2 = calculate_delta_r2(full_results, reduced_results)
        logger.info(f"Delta R² (Full - Reduced): {delta_r2:.4f}")

        result_output = {
            "full_model_r2": full_results["mean_r2"],
            "reduced_model_r2": reduced_results["mean_r2"],
            "delta_r2": delta_r2,
            "full_model_mae": full_results["mean_mae"],
            "reduced_model_mae": reduced_results["mean_mae"],
            "methodology": "Y ~ FD + DVARS + Age + Sex (excluding Global_Signal_SD)",
            "covariates": reduced_results["feature_names"]
        }

        write_json(result_output, str(output_path))
        logger.info(f"Results written to {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise

    return result_output

if __name__ == "__main__":
    main()