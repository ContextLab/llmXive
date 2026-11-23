"""
Train Final RF Baseline Model (T016a)

This script trains a single Random Forest model on the entire cleaned dataset
using the best hyperparameters found during the Nested Cross-Validation (T016).
It saves the final model artifact to data/artifacts/final_rf_baseline.pkl.
"""
import os
import sys
import json
import logging
import argparse
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config.seeds import get_seed, ensure_seeded
from models.baseline_rf import (
    generate_morgan_fingerprint,
    load_processed_data,
    prepare_features_and_targets,
    train_random_forest,
    evaluate_model,
    save_model as save_rf_model
)
from training.log_baseline_operations import (
    ensure_log_directory,
    log_baseline_training_metrics,
    log_model_save_operation
)

logger = logging.getLogger(__name__)

def load_best_hyperparameters(hyperparams_path: str) -> Dict[str, Any]:
    """
    Load the best hyperparameters from the Nested CV results.
    Expects a JSON file containing the aggregated best params.
    """
    path = Path(hyperparams_path)
    if not path.exists():
        raise FileNotFoundError(f"Best hyperparameters file not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # The Nested CV task (T016) should save the best params found across folds
    # We assume the structure includes a 'best_params' key or similar
    if 'best_params' in data:
        return data['best_params']
    elif 'best_hyperparameters' in data:
        return data['best_hyperparameters']
    else:
        # Fallback: try to find any dict-like structure that looks like params
        for key, value in data.items():
            if isinstance(value, dict) and 'n_estimators' in value:
                logger.warning(f"Using hyperparameters found under key '{key}'")
                return value
        
        raise ValueError(f"Could not find best hyperparameters in {path}. "
                         f"Expected a 'best_params' or 'best_hyperparameters' key.")

def main(args: argparse.Namespace) -> None:
    """
    Main entry point for training the final Random Forest baseline.
    """
    # Setup paths
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    artifacts_dir = data_dir / "artifacts"
    results_dir = project_root / "results"
    logs_dir = data_dir / "logs"

    # Ensure directories exist
    ensure_log_directory(logs_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    log_file = logs_dir / "train_final_rf.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info("Starting Final RF Baseline Training (T016a)")

    # Set seeds for reproducibility
    seed = get_seed()
    ensure_seeded(seed)
    logger.info(f"Random seed set to: {seed}")

    # Paths to inputs
    fingerprints_path = processed_dir / "fingerprints.npz"
    targets_path = processed_dir / "cleaned_targets.json" # Assuming targets are saved here or extracted from cleaned_graphs.pkl
    hyperparams_path = args.hyperparams_file or (processed_dir / "rf_cv_best_params.json")
    output_model_path = artifacts_dir / "final_rf_baseline.pkl"
    output_metrics_path = results_dir / "final_baseline_metrics.json"

    # Verify inputs exist
    if not fingerprints_path.exists():
        raise FileNotFoundError(f"Missing fingerprints file: {fingerprints_path}. "
                                "Please run T012a (featurize) first.")
    
    if not hyperparams_path.exists():
        raise FileNotFoundError(f"Missing best hyperparameters file: {hyperparams_path}. "
                                "Please run T016 (Nested CV) first.")

    logger.info(f"Loading best hyperparameters from: {hyperparams_path}")
    best_params = load_best_hyperparameters(str(hyperparams_path))
    logger.info(f"Best hyperparameters: {best_params}")

    # Load processed data
    logger.info("Loading processed data (fingerprints and targets)...")
    X, y, molecule_ids = prepare_features_and_targets(
        fingerprints_path=fingerprints_path,
        targets_path=targets_path if targets_path.exists() else None
    )
    
    if X is None or y is None:
        raise RuntimeError("Failed to load features or targets. "
                           "Check that T005 and T012a completed successfully.")
    
    logger.info(f"Loaded {len(X)} samples for final training.")

    # Train the final model on the ENTIRE dataset
    logger.info("Training final Random Forest model on entire dataset...")
    model = train_random_forest(X, y, **best_params)
    
    # Evaluate on the training set (as a sanity check, though not the true test metric)
    # Note: The true performance metric comes from the Nested CV (T016).
    # This is just to ensure the model is valid.
    train_rmse, train_r2 = evaluate_model(model, X, y)
    logger.info(f"Final model training set RMSE: {train_rmse:.4f}, R²: {train_r2:.4f}")

    # Save the model
    logger.info(f"Saving model to: {output_model_path}")
    save_rf_model(model, str(output_model_path))
    
    if not output_model_path.exists():
        raise RuntimeError(f"Model file {output_model_path} was not created.")
    
    logger.info("Model saved successfully.")

    # Log metrics and save operation
    log_baseline_training_metrics(
        rmse=train_rmse,
        r2=train_r2,
        model_type="Random Forest (Final)",
        hyperparameters=best_params,
        sample_count=len(X)
    )
    
    log_model_save_operation(
        model_path=str(output_model_path),
        model_type="Random Forest",
        size_bytes=output_model_path.stat().st_size
    )

    # Save final metrics summary (for quick reference)
    final_metrics = {
        "model_type": "Random Forest (Final Baseline)",
        "training_rmse": float(train_rmse),
        "training_r2": float(train_r2),
        "hyperparameters": best_params,
        "sample_count": len(X),
        "seed": seed,
        "model_path": str(output_model_path)
    }
    
    with open(output_metrics_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    logger.info(f"Final metrics saved to: {output_metrics_path}")
    logger.info("Final RF Baseline Training (T016a) completed successfully.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Final RF Baseline Model (T016a)")
    parser.add_argument(
        "--hyperparams_file",
        type=str,
        default=None,
        help="Path to JSON file containing best hyperparameters from T016. "
             "Defaults to data/processed/rf_cv_best_params.json"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args)