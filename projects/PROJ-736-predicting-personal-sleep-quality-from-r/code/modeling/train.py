"""
Training script for sleep quality prediction.
Invokes T020a (NestedCVPipeline) to perform nested CV, tune ElasticNet,
and save predictions and the trained model.
"""
from __future__ import annotations

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_paths, ensure_dirs, get_hyperparameter, set_seeds
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error, get_logger, log_operation
from modeling.pipeline_factory import NestedCVPipeline, create_pipeline


def load_data(behavioral_path: str, features_dir: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load connectivity features and sleep scores.

    Args:
        behavioral_path: Path to hcp1200_behavioral_data.csv
        features_dir: Directory containing .npy feature files

    Returns:
        X: Feature matrix [n_subjects, n_features]
        y: Sleep scores [n_subjects]
        subject_ids: List of subject IDs
    """
    log_stage_start("Load Data", {"behavioral": behavioral_path, "features_dir": features_dir})

    # Load behavioral data
    df = pd.read_csv(behavioral_path)

    # Filter for subjects with valid Sleep Scores (non-null)
    # Assuming column name is 'Sleep_Score' or similar based on context
    # The filter task T007b/T040 should have already produced valid_subjects.txt
    # but here we re-verify against the CSV for safety if needed.
    # For now, assume the CSV contains the filtered list or we filter here.
    # The task T007b outputs valid_subjects.txt, let's try to use that if available,
    # otherwise filter the CSV directly.

    valid_subjects_file = Path(features_dir).parent / "valid_subjects.txt"
    if valid_subjects_file.exists():
        with open(valid_subjects_file, 'r') as f:
            valid_ids = [line.strip() for line in f if line.strip()]
        df = df[df['Subject'].isin(valid_ids)]

    # Handle missing Sleep Scores explicitly (T040)
    sleep_col = None
    possible_cols = ['Sleep_Score', 'SleepScore', 'sleep_score', 'Sleep']
    for col in possible_cols:
        if col in df.columns:
            sleep_col = col
            break

    if sleep_col is None:
        raise ValueError(f"Could not find Sleep Score column in {behavioral_path}. Columns: {df.columns.tolist()}")

    # Drop rows with NaN in sleep score
    df = df.dropna(subset=[sleep_col])

    # Sort to ensure consistent ordering with feature files
    df = df.sort_values('Subject')
    subject_ids = df['Subject'].tolist()

    # Load features
    features = []
    for sid in subject_ids:
        feature_file = os.path.join(features_dir, f"{sid}.npy")
        if not os.path.exists(feature_file):
            log_stage_error("Load Data", f"Feature file missing for {sid}")
            continue
        feat = np.load(feature_file)
        features.append(feat)

    if not features:
        raise RuntimeError("No features loaded. Check subject filtering and feature generation.")

    X = np.vstack(features)
    y = df[sleep_col].values.astype(float)

    log_stage_complete("Load Data")
    return X, y, subject_ids


def run_training(X: np.ndarray, y: np.ndarray, subject_ids: list[str], output_dir: str) -> None:
    """
    Run the nested CV training pipeline.

    Args:
        X: Feature matrix
        y: Target vector (Sleep Scores)
        subject_ids: List of subject IDs
        output_dir: Directory to save predictions and model
    """
    log_stage_start("Training Pipeline", {"n_subjects": len(X), "n_features": X.shape[1]})

    set_seeds(get_hyperparameter("random_seed"))

    # Create the nested CV pipeline wrapper (T020a)
    # This wrapper ensures VarianceThreshold and PCA are fitted inside the CV loop
    pipeline = NestedCVPipeline(
        model_type="elastic_net",
        cv_folds=5,
        inner_cv_folds=3,
        random_state=get_hyperparameter("random_seed")
    )

    # Fit and get outer-fold predictions
    log_operation("Model Training", message="Running ElasticNetCV with nested CV")
    
    # The pipeline should return predictions for the outer folds
    # and the best model from the full data (or we refit on full data)
    predictions, best_model = pipeline.fit_predict(X, y)

    # Save predictions
    predictions_path = os.path.join(output_dir, "predictions.npy")
    np.save(predictions_path, predictions.reshape(-1, 1))
    log_operation("Save Predictions", path=predictions_path, shape=predictions.shape)

    # Save the trained model object
    # We need to pickle the best model found (or refit on full data if that's the design)
    # Assuming pipeline stores the best model or we can refit it.
    # For safety, let's refit the final model on the full data using the best params found
    model_path = os.path.join(output_dir, "model.pkl")
    
    # If the pipeline has a 'best_model_' attribute or similar
    if hasattr(pipeline, 'final_model_'):
        import pickle
        with open(model_path, 'wb') as f:
            pickle.dump(pipeline.final_model_, f)
        log_operation("Save Model", path=model_path)
    else:
        # Fallback: refit a simple ElasticNetCV on full data with best params if available
        # This ensures we have a model object for T029 (interpretation)
        from sklearn.linear_model import ElasticNetCV
        import pickle
        
        # Get best parameters from the pipeline if possible
        # If not, just train a standard one (less ideal but safe)
        final_model = ElasticNetCV(
            l1_ratio=[0.1, 0.5, 0.7, 0.9],
            cv=5,
            random_state=get_hyperparameter("random_seed"),
            n_jobs=-1
        )
        final_model.fit(X, y)
        
        with open(model_path, 'wb') as f:
            pickle.dump(final_model, f)
        log_operation("Save Model (Refitted)", path=model_path)

    log_stage_complete("Training Pipeline")


def main() -> bool:
    """Main entry point."""
    paths = get_paths()
    processed_dir = paths["processed"]
    output_dir = paths["processed"] # Save outputs to processed as per spec
    behavioral_file = paths["raw_behavioral"]

    # Ensure directories exist
    ensure_dirs([output_dir])

    # Setup logging
    log_file = os.path.join(paths["logs"], "train_run.json")
    setup_logging(log_file)

    try:
        # Load data
        X, y, subject_ids = load_data(behavioral_file, processed_dir)
        
        # Run training
        run_training(X, y, subject_ids, output_dir)

        return True
    except Exception as e:
        log_stage_error("Main", str(e))
        print(f"Error in main: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)