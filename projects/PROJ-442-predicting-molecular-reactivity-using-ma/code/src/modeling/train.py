from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from src.utils.logging import get_logger, log_operation
from src.modeling.config import load_config
from src.utils.state_manager import register_artifact, update_stage_status

# Fix for deprecated import location in some sklearn versions
try:
    from scipy.stats import spearmanr
except ImportError:
    from scipy.stats import spearmanr as spearmanr


logger = get_logger("train")


def load_target_data(
    feature_path: str, target_path: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load feature matrix and target variable.

    Args:
        feature_path: Path to feature_matrix.parquet
        target_path: Optional path to target file. If None, assumes target is
                     in the feature file under a 'target' column.

    Returns:
        Tuple of (features_df, target_series)
    """
    log_operation("load_target_data", input=feature_path, target=target_path)

    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Feature file not found: {feature_path}")

    df = pd.read_parquet(feature_path)

    if target_path:
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Target file not found: {target_path}")
        target_df = pd.read_csv(target_path)
        if "target" not in target_df.columns:
            raise ValueError(f"Target file missing 'target' column: {target_path}")
        target = target_df["target"]
        features = df
    else:
        if "target" not in df.columns:
            raise ValueError(
                f"Feature file missing 'target' column: {feature_path}"
            )
        target = df["target"]
        features = df.drop(columns=["target"])

    return features, target


def normalize_target(target: pd.Series) -> Tuple[pd.Series, Dict[str, float]]:
    """Normalize target variable using Z-score.

    Args:
        target: Target series

    Returns:
        Tuple of (normalized_target, params) where params contains mean and std
    """
    log_operation("normalize_target")
    mean_val = target.mean()
    std_val = target.std()
    if std_val == 0:
        std_val = 1.0
    normalized = (target - mean_val) / std_val
    return normalized, {"mean": float(mean_val), "std": float(std_val)}


def train_xgboost_model(
    features: pd.DataFrame,
    target: pd.Series,
    config: Dict[str, Any],
    cv_results_path: Optional[str] = None,
) -> Tuple[xgb.XGBRegressor, Dict[str, Any]]:
    """Train XGBoost model with 5-fold CV.

    Args:
        features: Feature DataFrame
        target: Target Series
        config: Configuration dictionary
        cv_results_path: Optional path to save CV results CSV

    Returns:
        Tuple of (trained_model, metrics_dict)
    """
    log_operation("train_xgboost_model", n_features=features.shape[1])

    # Get hyperparameters from config
    params = config.get("model", {}).get("xgboost", {})
    n_estimators = params.get("n_estimators", 100)
    max_depth = params.get("max_depth", 6)
    learning_rate = params.get("learning_rate", 0.1)
    subsample = params.get("subsample", 0.8)
    colsample_bytree = params.get("colsample_bytree", 0.8)
    random_state = params.get("random_state", 42)

    # Initialize model
    model = xgb.XGBRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        random_state=random_state,
        n_jobs=-1,
        eval_metric="rmse",
    )

    # 5-fold Cross-Validation
    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_scores = []
    cv_predictions = np.zeros(len(target))
    cv_true_values = np.zeros(len(target))

    start_time = time.time()

    for fold_idx, (train_idx, val_idx) in enumerate(kf.split(features)):
        X_train, X_val = features.iloc[train_idx], features.iloc[val_idx]
        y_train, y_val = target.iloc[train_idx], target.iloc[val_idx]

        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        y_pred = model.predict(X_val)
        cv_predictions[val_idx] = y_pred
        cv_true_values[val_idx] = y_val.values

        # Calculate Spearman correlation for this fold
        try:
            rho, p_value = spearmanr(y_val, y_pred)
            cv_scores.append({"fold": fold_idx + 1, "spearman_rho": rho})
        except Exception as e:
            logger.warning(f"Fold {fold_idx + 1} Spearman calculation failed: {e}")
            cv_scores.append({"fold": fold_idx + 1, "spearman_rho": None})

    elapsed_time = time.time() - start_time

    # Calculate aggregate metrics
    try:
        final_rho, final_p_value = spearmanr(cv_true_values, cv_predictions)
    except Exception:
        final_rho = 0.0
        final_p_value = 1.0

    metrics = {
        "mean_spearman_rho": np.mean([s["spearman_rho"] for s in cv_scores if s["spearman_rho"] is not None])
        if any(s["spearman_rho"] is not None for s in cv_scores)
        else 0.0,
        "overall_spearman_rho": float(final_rho),
        "overall_p_value": float(final_p_value),
        "runtime_seconds": elapsed_time,
        "cv_fold_results": cv_scores,
        "hyperparameters": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
        },
    }

    # Save CV results if path provided
    if cv_results_path:
        cv_df = pd.DataFrame({
            "fold": [s["fold"] for s in cv_scores],
            "spearman_rho": [s["spearman_rho"] for s in cv_scores],
        })
        # Ensure directory exists
        Path(cv_results_path).parent.mkdir(parents=True, exist_ok=True)
        cv_df.to_csv(cv_results_path, index=False)
        logger.info(f"Saved CV results to {cv_results_path}")

    # Train final model on all data
    model.fit(features, target)

    return model, metrics


def run_training_pipeline(
    feature_path: str,
    model_output_path: str,
    log_output_path: str,
    config_path: str,
    cv_results_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full training pipeline.

    Args:
        feature_path: Path to feature matrix
        model_output_path: Path to save trained model JSON
        log_output_path: Path to save training log JSON
        config_path: Path to config file
        cv_results_path: Optional path to save CV results

    Returns:
        Training metrics dictionary
    """
    log_operation(
        "run_training_pipeline",
        feature_path=feature_path,
        model_output_path=model_output_path,
        config_path=config_path,
    )

    # Load config
    config = load_config(config_path)

    # Load data
    features, target = load_target_data(feature_path)
    logger.info(f"Loaded {len(features)} samples with {features.shape[1]} features")

    # Normalize target
    normalized_target, norm_params = normalize_target(target)

    # Train model
    model, metrics = train_xgboost_model(
        features, normalized_target, config, cv_results_path
    )

    # Save model
    Path(model_output_path).parent.mkdir(parents=True, exist_ok=True)
    model.save_model(model_output_path)
    logger.info(f"Saved model to {model_output_path}")

    # Register artifact
    register_artifact(model_output_path, stage="modeling", artifact_type="model")

    # Prepare training log
    training_log = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature_file": feature_path,
        "model_file": model_output_path,
        "n_samples": len(features),
        "n_features": features.shape[1],
        "target_normalization": norm_params,
        "metrics": metrics,
        "config_path": config_path,
    }

    # Save training log
    Path(log_output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_output_path, "w") as f:
        json.dump(training_log, f, indent=2, default=str)
    logger.info(f"Saved training log to {log_output_path}")

    # Register training log artifact
    register_artifact(log_output_path, stage="modeling", artifact_type="log")

    # Update stage status
    update_stage_status(
        stage="modeling",
        status="completed",
        artifacts=[model_output_path, log_output_path],
    )

    return training_log


def main():
    """Main entry point for training script."""
    import argparse

    parser = argparse.ArgumentParser(description="Train XGBoost model")
    parser.add_argument(
        "--config",
        type=str,
        default="code/src/modeling/config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--features",
        type=str,
        default="data/processed/feature_matrix.parquet",
        help="Path to feature matrix",
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="data/models/xgboost_model.json",
        help="Path to save model",
    )
    parser.add_argument(
        "--log-output",
        type=str,
        default="data/processed/training_log.json",
        help="Path to save training log",
    )
    parser.add_argument(
        "--cv-results",
        type=str,
        default="data/results/cv_results.csv",
        help="Path to save CV results",
    )

    args = parser.parse_args()

    try:
        run_training_pipeline(
            feature_path=args.features,
            model_output_path=args.model_output,
            log_output_path=args.log_output,
            config_path=args.config,
            cv_results_path=args.cv_results,
        )
        logger.info("Training completed successfully")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
