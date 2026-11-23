"""
T106: Re-run SHAP and SC-003 verification.

Execute SHAP analysis on the trained XGBoost model, rank descriptors by
mean absolute SHAP impact, generate feature importance plot, and train
a reduced top-5 model to verify SC-003 (R² ratio >= 0.50).
"""

import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import shap
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import r2_score, mean_absolute_error

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def load_best_xgboost_model() -> xgb.XGBRegressor:
    """Load the best XGBoost model saved during training."""
    model_path = paths.code("models", "best_xgboost.json")
    if not model_path.exists():
        raise FileNotFoundError(f"Best XGBoost model not found at {model_path}")
    
    model = xgb.XGBRegressor()
    model.load_model(str(model_path))
    log.info(f"Loaded best XGBoost model from {model_path}")
    return model


def load_test_data() -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Load test features and target from aligned dataset."""
    aligned_path = paths.data("processed", "aligned_dataset.csv")
    if not aligned_path.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {aligned_path}")
    
    df = pd.read_csv(aligned_path)
    
    # Load split metadata to identify test indices
    split_metadata_path = paths.outputs("split_metadata.json")
    if not split_metadata_path.exists():
        raise FileNotFoundError(f"Split metadata not found at {split_metadata_path}")
    
    with open(split_metadata_path, 'r') as f:
        split_metadata = json.load(f)
    
    test_indices = split_metadata.get("test_indices", [])
    if not test_indices:
        raise ValueError("No test indices found in split metadata")
    
    df_test = df.iloc[test_indices].reset_index(drop=True)
    
    # Identify feature columns (exclude target and id columns)
    target_col = "experimental_tof"
    id_cols = ["catalyst_id", "excluded_from_training"]
    feature_cols = [col for col in df_test.columns 
                   if col not in [target_col] + id_cols 
                   and not col.startswith("_")]
    
    X_test = df_test[feature_cols].copy()
    y_test = df_test[target_col].copy()
    
    log.info(f"Loaded test data: {len(X_test)} samples, {len(feature_cols)} features")
    return X_test, y_test, feature_cols


def compute_shap_values(model: xgb.XGBRegressor, 
                       X_test: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """Compute SHAP values using TreeExplainer."""
    log.info("Computing SHAP values...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    log.info(f"SHAP values shape: {shap_values.shape}")
    return shap_values, X_test.columns.tolist()


def rank_descriptors_by_shap(shap_values: np.ndarray, 
                             feature_names: List[str]) -> List[Dict[str, Any]]:
    """Rank descriptors by mean absolute SHAP impact."""
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
    
    rankings = []
    for idx, (feature_name, shap_impact) in enumerate(zip(feature_names, mean_abs_shap)):
        rankings.append({
            "rank": idx + 1,
            "descriptor_name": feature_name,
            "mean_absolute_shap_value": float(shap_impact)
        })
    
    # Sort by mean absolute SHAP value (descending)
    rankings = sorted(rankings, key=lambda x: x["mean_absolute_shap_value"], reverse=True)
    
    # Update ranks after sorting
    for idx, ranking in enumerate(rankings):
        ranking["rank"] = idx + 1
    
    log.info("Top 5 descriptors by SHAP impact:")
    for ranking in rankings[:5]:
        log.info(f"  {ranking['rank']}. {ranking['descriptor_name']}: "
                f"{ranking['mean_absolute_shap_value']:.6f}")
    
    return rankings


def generate_feature_importance_plot(rankings: List[Dict[str, Any]], 
                                    top_n: int = 5) -> Path:
    """Generate and save a bar plot of top N descriptors."""
    top_rankings = rankings[:top_n]
    
    descriptors = [r["descriptor_name"] for r in top_rankings]
    shap_values = [r["mean_absolute_shap_value"] for r in top_rankings]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(descriptors, shap_values, color="steelblue")
    
    ax.set_xlabel("Mean Absolute SHAP Value", fontsize=12)
    ax.set_ylabel("Descriptor", fontsize=12)
    ax.set_title(f"Top {top_n} Feature Importance (SHAP)", fontsize=14, fontweight="bold")
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, shap_values)):
        ax.text(value, i, f" {value:.4f}", va="center", fontsize=10)
    
    plt.tight_layout()
    
    output_path = paths.figures("feature_importance.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    log.info(f"Saved feature importance plot to {output_path}")
    plt.close(fig)
    
    return output_path


def load_training_data() -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """Load training features and target from aligned dataset."""
    aligned_path = paths.data("processed", "aligned_dataset.csv")
    if not aligned_path.exists():
        raise FileNotFoundError(f"Aligned dataset not found at {aligned_path}")
    
    df = pd.read_csv(aligned_path)
    
    # Load split metadata to identify training indices
    split_metadata_path = paths.outputs("split_metadata.json")
    if not split_metadata_path.exists():
        raise FileNotFoundError(f"Split metadata not found at {split_metadata_path}")
    
    with open(split_metadata_path, 'r') as f:
        split_metadata = json.load(f)
    
    train_indices = split_metadata.get("train_indices", [])
    if not train_indices:
        raise ValueError("No training indices found in split metadata")
    
    df_train = df.iloc[train_indices].reset_index(drop=True)
    
    # Identify feature columns (exclude target and id columns)
    target_col = "experimental_tof"
    id_cols = ["catalyst_id", "excluded_from_training"]
    feature_cols = [col for col in df_train.columns 
                   if col not in [target_col] + id_cols 
                   and not col.startswith("_")]
    
    X_train = df_train[feature_cols].copy()
    y_train = df_train[target_col].copy()
    
    log.info(f"Loaded training data: {len(X_train)} samples, {len(feature_cols)} features")
    return X_train, y_train, feature_cols


def train_reduced_model(X_train: pd.DataFrame, 
                       y_train: pd.Series,
                       top_descriptors: List[str]) -> xgb.XGBRegressor:
    """Train XGBoost model using only top descriptors with grid search."""
    log.info(f"Training reduced model with {len(top_descriptors)} descriptors: {top_descriptors}")
    
    # Select only the top descriptors
    X_train_reduced = X_train[top_descriptors].copy()
    
    # Use the same grid as the full model (from FR-004)
    param_grid = {
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1],
        "n_estimators": [200]
    }
    
    base_model = xgb.XGBRegressor(
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=5,
        scoring="r2",
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train_reduced, y_train)
    
    best_model = grid_search.best_estimator_
    log.info(f"Best reduced model params: {grid_search.best_params_}")
    log.info(f"Best reduced model CV R²: {grid_search.best_score_:.4f}")
    
    return best_model


def evaluate_reduced_model(model_full: xgb.XGBRegressor,
                          model_reduced: xgb.XGBRegressor,
                          X_test: pd.DataFrame,
                          y_test: pd.Series,
                          top_descriptors: List[str]) -> Dict[str, Any]:
    """Evaluate reduced model and compute SC-003 ratio."""
    # Full model predictions
    y_pred_full = model_full.predict(X_test)
    r2_full = r2_score(y_test, y_pred_full)
    mae_full = mean_absolute_error(y_test, y_pred_full)
    
    # Reduced model predictions
    X_test_reduced = X_test[top_descriptors].copy()
    y_pred_reduced = model_reduced.predict(X_test_reduced)
    r2_reduced = r2_score(y_test, y_pred_reduced)
    mae_reduced = mean_absolute_error(y_test, y_pred_reduced)
    
    # SC-003: R² ratio
    ratio = r2_reduced / r2_full if r2_full > 0 else 0.0
    sc003_status = "PASS" if ratio >= 0.50 else "FAIL"
    
    log.info(f"Full model R²: {r2_full:.4f}, MAE: {mae_full:.4f}")
    log.info(f"Reduced model R²: {r2_reduced:.4f}, MAE: {mae_reduced:.4f}")
    log.info(f"SC-003 R² ratio: {ratio:.4f}")
    log.info(f"SC-003 status: {sc003_status}")
    
    return {
        "full_model_r2": float(r2_full),
        "full_model_mae": float(mae_full),
        "reduced_model_r2": float(r2_reduced),
        "reduced_model_mae": float(mae_reduced),
        "ratio": float(ratio),
        "SC-003_status": sc003_status,
        "top_descriptors": top_descriptors
    }


def save_shap_ranking(rankings: List[Dict[str, Any]]) -> Path:
    """Save SHAP rankings to JSON."""
    output_path = paths.outputs("shap_ranking.json")
    with open(output_path, 'w') as f:
        json.dump(rankings, f, indent=2)
    log.info(f"Saved SHAP rankings to {output_path}")
    return output_path


def save_sc003_verification(sc003_data: Dict[str, Any]) -> Path:
    """Save SC-003 verification results to JSON."""
    output_path = paths.outputs("sc003_verification.json")
    with open(output_path, 'w') as f:
        json.dump(sc003_data, f, indent=2)
    log.info(f"Saved SC-003 verification to {output_path}")
    return output_path


def main():
    """Main entry point for SHAP analysis and SC-003 verification."""
    try:
        log.info("=" * 80)
        log.info("T106: SHAP Analysis and SC-003 Verification")
        log.info("=" * 80)
        
        # Load best model
        model_full = load_best_xgboost_model()
        
        # Load test data
        X_test, y_test, feature_cols = load_test_data()
        
        # Compute SHAP values
        shap_values, feature_names = compute_shap_values(model_full, X_test)
        
        # Rank descriptors
        rankings = rank_descriptors_by_shap(shap_values, feature_names)
        
        # Save SHAP rankings
        save_shap_ranking(rankings)
        
        # Generate feature importance plot
        generate_feature_importance_plot(rankings, top_n=5)
        
        # Get top 5 descriptors
        top_5_descriptors = [r["descriptor_name"] for r in rankings[:5]]
        log.info(f"Top 5 descriptors: {top_5_descriptors}")
        
        # Load training data for reduced model training
        X_train, y_train, _ = load_training_data()
        
        # Train reduced model with top 5 descriptors
        model_reduced = train_reduced_model(X_train, y_train, top_5_descriptors)
        
        # Evaluate reduced model and compute SC-003
        sc003_data = evaluate_reduced_model(
            model_full, model_reduced, X_test, y_test, top_5_descriptors
        )
        
        # Save SC-003 verification
        save_sc003_verification(sc003_data)
        
        log.info("=" * 80)
        log.info("T106 completed successfully")
        log.info("=" * 80)
        
        return 0
    
    except Exception as e:
        log.error(f"Error in T106: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
