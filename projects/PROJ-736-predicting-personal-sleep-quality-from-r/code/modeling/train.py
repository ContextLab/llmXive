"""Training pipeline for sleep quality prediction.

Implements nested cross-validation with ElasticNet, checkpoint/resume logic,
and saves predictions and trained model.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Project imports
from config import get_paths, ensure_dirs, get_hyperparameter
from data.feature_engineering import load_filtered_subjects
from modeling.pipeline_factory import NestedCVPipeline, create_pipeline
from utils.logging import get_logger, log_operation, log_stage_start, setup_logging

logger = get_logger("train")


def load_data(processed_dir: str, behavioral_file: str) -> tuple[np.ndarray, np.ndarray, List[str]]:
    """Load connectivity features and sleep scores.

    Args:
        processed_dir: Directory containing .npy connectivity files.
        behavioral_file: Path to behavioral data CSV.

    Returns:
        X: Feature matrix [n_subjects, n_features]
        y: Target vector [n_subjects]
        subject_ids: List of subject IDs
    """
    logger.log_operation("load_data", params={"processed_dir": processed_dir, "behavioral_file": behavioral_file})

    # Load behavioral data
    df = pd.read_csv(behavioral_file)

    # Filter for valid sleep scores
    valid_mask = df['Sleep_Score'].notna() & (df['Sleep_Score'] != "N/A")
    df_valid = df[valid_mask]

    # Get subject IDs
    subject_ids = df_valid['Subject_ID'].tolist()

    # Load connectivity vectors
    X_list = []
    valid_subjects = []
    for sid in subject_ids:
        feature_path = os.path.join(processed_dir, f"{sid}.npy")
        if os.path.exists(feature_path):
            vec = np.load(feature_path)
            X_list.append(vec)
            valid_subjects.append(sid)
        else:
            logger.log_operation("missing_feature_file", params={"subject": sid})

    if len(X_list) == 0:
        raise RuntimeError("No valid feature files found for any subjects.")

    X = np.array(X_list)
    y = df_valid[df_valid['Subject_ID'].isin(valid_subjects)]['Sleep_Score'].values

    logger.log_operation("data_loaded", params={"n_subjects": len(X), "n_features": X.shape[1]})
    return X, y, valid_subjects


def load_checkpoint(checkpoint_path: str) -> Optional[Dict[str, Any]]:
    """Load training checkpoint if exists."""
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r') as f:
            return json.load(f)
    return None


def save_checkpoint(checkpoint_path: str, state: Dict[str, Any]) -> None:
    """Save training checkpoint."""
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    with open(checkpoint_path, 'w') as f:
        json.dump(state, f, indent=2)


def run_training(
    X: np.ndarray,
    y: np.ndarray,
    subject_ids: List[str],
    output_dir: str,
    n_splits: int = 5,
    random_state: int = 42
) -> tuple[np.ndarray, Any]:
    """Run nested cross-validation training with checkpointing.

    Args:
        X: Feature matrix
        y: Target vector
        subject_ids: List of subject IDs
        output_dir: Directory to save outputs
        n_splits: Number of CV splits
        random_state: Random seed

    Returns:
        predictions: Outer-fold predictions [n_subjects, 1]
        model: Trained ElasticNetCV model
    """
    logger.log_operation("run_training", params={"n_subjects": len(X), "n_splits": n_splits})

    # Paths
    checkpoint_path = os.path.join(output_dir, "train_checkpoint.json")
    model_path = os.path.join(output_dir, "model.pkl")
    predictions_path = os.path.join(output_dir, "predictions.npy")

    # Load checkpoint if exists
    checkpoint = load_checkpoint(checkpoint_path)
    start_fold = 0
    if checkpoint:
        start_fold = checkpoint.get("last_completed_fold", 0)
        logger.log_operation("resume_from_checkpoint", params={"start_fold": start_fold})

    # Initialize predictions array
    predictions = np.zeros((len(X), 1))
    predictions.fill(np.nan)

    # Load existing predictions if resuming
    if start_fold > 0 and os.path.exists(predictions_path):
        existing_preds = np.load(predictions_path)
        predictions[:existing_preds.shape[0], :] = existing_preds

    # Create nested CV pipeline (T020a)
    pipeline = create_pipeline()

    # Set up KFold
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    folds = list(kf.split(X))

    # Process folds
    for fold_idx, (train_idx, test_idx) in enumerate(folds):
        if fold_idx < start_fold:
            logger.log_operation("skip_completed_fold", params={"fold": fold_idx})
            continue

        logger.log_operation("processing_fold", params={"fold": fold_idx, "n_train": len(train_idx), "n_test": len(test_idx)})

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Fit and predict
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        # Store predictions
        predictions[test_idx, 0] = y_pred

        # Save checkpoint after each fold
        checkpoint_state = {
            "last_completed_fold": fold_idx + 1,
            "timestamp": time.time(),
            "n_subjects": len(X),
            "n_splits": n_splits
        }
        save_checkpoint(checkpoint_path, checkpoint_state)

    # Final model fit on full data
    logger.log_operation("fitting_final_model", params={"n_subjects": len(X)})
    pipeline.fit(X, y)

    # Save model
    import pickle
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)

    # Save predictions
    np.save(predictions_path, predictions)

    # Clean up checkpoint on success
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)

    logger.log_operation("training_complete", params={"predictions_path": predictions_path, "model_path": model_path})
    return predictions, pipeline


def main() -> int:
    """Main entry point for training script."""
    # Setup logging
    log_file = os.path.join(get_paths()["logs_dir"], "train_run.json")
    setup_logging(log_file)

    logger.log_stage_start("Training Pipeline", {"phase": "US2"})

    try:
        # Get paths
        paths = get_paths()
        processed_dir = paths["processed_dir"]
        behavioral_file = os.path.join(paths["raw_dir"], "behavioral", "hcp1200_behavioral_data.csv")

        # Load data
        X, y, subject_ids = load_data(processed_dir, behavioral_file)

        # Run training
        predictions, model = run_training(
            X=X,
            y=y,
            subject_ids=subject_ids,
            output_dir=paths["processed_dir"],
            n_splits=get_hyperparameter("cv_splits", 5),
            random_state=get_hyperparameter("random_seed", 42)
        )

        logger.log_stage_complete("Training Pipeline")
        return 0

    except Exception as e:
        logger.log_stage_error("Training Pipeline", str(e))
        raise


if __name__ == "__main__":
    sys.exit(main())
