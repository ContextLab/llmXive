"""
Checkpointing utility for the modeling pipeline.

This module provides functionality to save intermediate model state and partial
results after each Cross-Validation (CV) fold. This is critical for:
1. Resuming interrupted long-running training jobs (LOOCV or large RF).
2. Auditing the progression of model performance.
3. Preventing total data loss in case of hardware failure.

Checkpoints are stored as JSON (for metrics) and Pickle (for model objects)
in the `results/checkpoints/` directory.
"""

import os
import json
import pickle
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

# Import project utilities to ensure path consistency
from utils.config import get_results_path, get_project_root
from utils.logging_config import get_logger

# Constants
CHECKPOINT_DIR_NAME = "checkpoints"
MODEL_EXT = ".pkl"
METRICS_EXT = ".json"
TIMESTAMP_FMT = "%Y%m%d_%H%M%S"

logger = get_logger(__name__)

def _get_checkpoint_dir() -> Path:
    """Returns the path to the checkpoints directory, creating it if necessary."""
    results_path = get_results_path()
    checkpoint_dir = results_path / CHECKPOINT_DIR_NAME
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir

def _generate_run_id() -> str:
    """Generates a unique run ID based on timestamp and a hash of the current process."""
    timestamp = datetime.now().strftime(TIMESTAMP_FMT)
    # Add a random component to avoid collisions in rapid sequential runs
    import random
    suffix = f"{random.randint(1000, 9999)}"
    return f"run_{timestamp}_{suffix}"

def save_model_checkpoint(
    model: Any,
    run_id: str,
    fold_index: int,
    model_type: str,
    hyperparams: Dict[str, Any],
    metrics: Optional[Dict[str, float]] = None
) -> Dict[str, str]:
    """
    Saves a model object and its associated metadata to disk.

    Args:
        model: The trained estimator (e.g., RandomForestRegressor, SVR).
        run_id: Unique identifier for this training session.
        fold_index: The index of the current CV fold (0-based).
        model_type: String identifier (e.g., 'RF', 'SVR').
        hyperparams: Dictionary of the model's hyperparameters.
        metrics: Optional dictionary of metrics calculated for this fold.

    Returns:
        A dictionary containing the paths to the saved artifacts.
    """
    checkpoint_dir = _get_checkpoint_dir()
    timestamp = datetime.now().strftime(TIMESTAMP_FMT)

    # Create filenames
    model_filename = f"{run_id}_{model_type}_fold{fold_index}_{timestamp}{MODEL_EXT}"
    metrics_filename = f"{run_id}_{model_type}_fold{fold_index}_{timestamp}{METRICS_EXT}"

    model_path = checkpoint_dir / model_filename
    metrics_path = checkpoint_dir / metrics_filename

    # Save Model
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model checkpoint saved: {model_path}")
    except Exception as e:
        logger.error(f"Failed to save model checkpoint: {e}")
        raise

    # Save Metrics/Metadata
    checkpoint_data = {
        "run_id": run_id,
        "fold_index": fold_index,
        "model_type": model_type,
        "hyperparameters": hyperparams,
        "metrics": metrics or {},
        "timestamp": timestamp,
        "status": "completed"
    }

    try:
        with open(metrics_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Metrics checkpoint saved: {metrics_path}")
    except Exception as e:
        logger.error(f"Failed to save metrics checkpoint: {e}")
        raise

    return {
        "model_path": str(model_path),
        "metrics_path": str(metrics_path)
    }

def load_model_checkpoint(path: str) -> Any:
    """
    Loads a model object from a checkpoint file.

    Args:
        path: Absolute or relative path to the .pkl file.

    Returns:
        The loaded model object.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Checkpoint file not found: {path}")

    if path_obj.suffix != MODEL_EXT:
        raise ValueError(f"Invalid checkpoint file extension: {path_obj.suffix}. Expected {MODEL_EXT}")

    logger.info(f"Loading model from: {path}")
    with open(path_obj, 'rb') as f:
        return pickle.load(f)

def load_metrics_checkpoint(path: str) -> Dict[str, Any]:
    """
    Loads metrics/metadata from a checkpoint JSON file.

    Args:
        path: Absolute or relative path to the .json file.

    Returns:
        Dictionary containing checkpoint data.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Metrics checkpoint file not found: {path}")

    if path_obj.suffix != METRICS_EXT:
        raise ValueError(f"Invalid metrics file extension: {path_obj.suffix}. Expected {METRICS_EXT}")

    with open(path_obj, 'r') as f:
        return json.load(f)

def get_latest_checkpoints(run_id: Optional[str] = None, model_type: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Retrieves a list of all checkpoint files in the directory.
    Optionally filters by run_id and model_type.

    Args:
        run_id: Optional filter for specific run ID.
        model_type: Optional filter for specific model type (e.g., 'RF', 'SVR').

    Returns:
        List of dictionaries containing file paths and metadata.
    """
    checkpoint_dir = _get_checkpoint_dir()
    checkpoints = []

    if not checkpoint_dir.exists():
        return checkpoints

    for file_path in checkpoint_dir.iterdir():
        if file_path.suffix == MODEL_EXT:
            # Parse filename: run_{id}_{type}_fold{N}_{ts}.pkl
            stem = file_path.stem
            parts = stem.split('_')
            
            # Basic parsing logic to extract info if possible
            # Format: run_<id>_<type>_fold<N>_<timestamp>
            # We assume at least 4 parts if valid
            metadata = {
                "file_path": str(file_path),
                "filename": file_path.name,
                "type": "model"
            }
            
            # Try to extract run_id and model_type from filename if not provided
            if len(parts) >= 4:
                # parts[0] is 'run'
                # parts[1] is timestamp (if no custom run_id) or part of run_id
                # This parsing is heuristic; for robustness, we rely on the JSON metadata
                # But we can try to match filters
                pass

            # Filter logic
            if run_id and run_id not in stem:
                continue
            if model_type and model_type not in stem:
                continue

            checkpoints.append(metadata)

    # Sort by modification time, newest first
    checkpoints.sort(key=lambda x: x["file_path"], reverse=True)
    return checkpoints

def resume_from_checkpoint(
    run_id: str,
    model_type: str,
    max_folds: int
) -> List[int]:
    """
    Determines which folds have already been completed for a specific run.

    Args:
        run_id: The run ID to check.
        model_type: The model type (e.g., 'RF', 'SVR').
        max_folds: The total number of folds planned.

    Returns:
        A list of fold indices that are already completed.
    """
    checkpoints = get_latest_checkpoints(run_id=run_id, model_type=model_type)
    completed_folds = []

    for cp in checkpoints:
        try:
            # Load metrics to verify status
            metrics_path = cp["file_path"].replace(MODEL_EXT, METRICS_EXT)
            if Path(metrics_path).exists():
                data = load_metrics_checkpoint(metrics_path)
                if data.get("status") == "completed":
                    fold_idx = data.get("fold_index")
                    if fold_idx is not None:
                        completed_folds.append(fold_idx)
        except Exception as e:
            logger.warning(f"Could not parse checkpoint {cp['file_path']}: {e}")

    # Filter out any folds >= max_folds (shouldn't happen, but safety)
    completed_folds = [f for f in completed_folds if f < max_folds]
    
    if completed_folds:
        logger.info(f"Resuming: Found {len(completed_folds)} completed folds: {completed_folds}")
    else:
        logger.info(f"Resuming: No completed folds found for run {run_id}. Starting from scratch.")

    return sorted(completed_folds)

def finalize_run(run_id: str, model_type: str, final_metrics: Dict[str, Any]) -> str:
    """
    Writes a final summary for a completed run.

    Args:
        run_id: The run ID.
        model_type: The model type.
        final_metrics: Aggregated metrics for the entire run.

    Returns:
        Path to the final summary file.
    """
    checkpoint_dir = _get_checkpoint_dir()
    timestamp = datetime.now().strftime(TIMESTAMP_FMT)
    summary_filename = f"{run_id}_{model_type}_final_{timestamp}{METRICS_EXT}"
    summary_path = checkpoint_dir / summary_filename

    summary_data = {
        "run_id": run_id,
        "model_type": model_type,
        "final_metrics": final_metrics,
        "completed_at": timestamp,
        "status": "finalized"
    }

    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)

    logger.info(f"Run finalized: {summary_path}")
    return str(summary_path)