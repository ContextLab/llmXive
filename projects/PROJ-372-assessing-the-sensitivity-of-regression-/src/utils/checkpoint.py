"""
Checkpoint mechanism for saving and loading experiment state.

This module defines the schema for checkpoint state used by T024 (resampling)
and T037 (documentation/reporting) to prevent schema drift and ensure
reproducibility.

Schema Definition:
------------------
A checkpoint is a JSON object with the following structure:
{
    "experiment_id": str,           # Unique identifier for the run
    "task_id": str,                 # ID of the task generating this checkpoint (e.g., "T024")
    "timestamp": str,               # ISO 8601 timestamp of the checkpoint creation
    "status": str,                  # "running", "completed", "failed", "paused"
    "progress": {                   # Task-specific progress metrics
        "total_items": int,         # Total number of items to process
        "processed_items": int,     # Number of items processed so far
        "current_item": int | None, # Currently processing item index
        "percent_complete": float   # 0.0 to 1.0
    },
    "intermediate_results": list,   # List of partial results (e.g., subset stats)
    "metadata": {                   # Key-value pairs for context
        "dataset_name": str,
        "sample_size_tier": int,    # Percentage (10, 25, 50, 75, 90)
        "random_seed": int,
        "model_type": str,          # e.g., "ols", "hlm"
        "config_hash": str          # Hash of configuration used
    },
    "error_log": list | None        # List of error messages if status is "failed"
}
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.config import get_artifacts_dir


CHECKPOINT_SCHEMA_VERSION = "1.0.0"


class CheckpointError(Exception):
    """Exception raised for checkpoint-related errors."""
    pass


def _ensure_directory(path: Path) -> None:
    """Ensure the directory for the checkpoint file exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _create_checkpoint_structure(
    experiment_id: str,
    task_id: str,
    status: str = "running",
    metadata: Optional[Dict[str, Any]] = None,
    progress: Optional[Dict[str, Any]] = None,
    intermediate_results: Optional[List[Any]] = None,
    error_log: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a checkpoint dictionary following the defined schema.

    Args:
        experiment_id: Unique identifier for the experiment run.
        task_id: ID of the task generating this checkpoint.
        status: Current status ("running", "completed", "failed", "paused").
        metadata: Optional metadata dictionary.
        progress: Optional progress dictionary.
        intermediate_results: Optional list of intermediate results.
        error_log: Optional list of error messages.

    Returns:
        Dictionary conforming to the checkpoint schema.
    """
    if progress is None:
        progress = {
            "total_items": 0,
            "processed_items": 0,
            "current_item": None,
            "percent_complete": 0.0,
        }

    if metadata is None:
        metadata = {}

    if intermediate_results is None:
        intermediate_results = []

    if error_log is None:
        error_log = []

    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "experiment_id": experiment_id,
        "task_id": task_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "progress": progress,
        "intermediate_results": intermediate_results,
        "metadata": metadata,
        "error_log": error_log,
    }


def save_checkpoint(
    checkpoint_data: Dict[str, Any],
    checkpoint_dir: Optional[str] = None,
    filename: Optional[str] = None,
) -> Path:
    """
    Save checkpoint data to a JSON file.

    Args:
        checkpoint_data: Dictionary conforming to the checkpoint schema.
        checkpoint_dir: Directory to save the checkpoint. Defaults to artifacts/checkpoints.
        filename: Optional filename. If None, generated from experiment_id and timestamp.

    Returns:
        Path to the saved checkpoint file.

    Raises:
        CheckpointError: If the checkpoint data is invalid or cannot be serialized.
    """
    # Validate required fields
    required_fields = ["experiment_id", "task_id", "timestamp", "status"]
    for field in required_fields:
        if field not in checkpoint_data:
            raise CheckpointError(f"Missing required field: {field}")

    if checkpoint_dir is None:
        checkpoint_dir = str(Path(get_artifacts_dir()) / "checkpoints")

    checkpoint_path = Path(checkpoint_dir)

    if filename is None:
        # Generate filename from experiment_id and timestamp
        ts = checkpoint_data["timestamp"].replace(":", "-").replace(".", "-")
        filename = f"checkpoint_{checkpoint_data['experiment_id']}_{ts}.json"

    full_path = checkpoint_path / filename
    _ensure_directory(full_path)

    try:
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
    except (TypeError, ValueError) as e:
        raise CheckpointError(f"Failed to serialize checkpoint data: {e}")

    return full_path


def load_checkpoint(checkpoint_path: str) -> Dict[str, Any]:
    """
    Load checkpoint data from a JSON file.

    Args:
        checkpoint_path: Path to the checkpoint file.

    Returns:
        Dictionary containing the checkpoint data.

    Raises:
        CheckpointError: If the file does not exist, is invalid JSON, or schema mismatch.
    """
    path = Path(checkpoint_path)

    if not path.exists():
        raise CheckpointError(f"Checkpoint file not found: {checkpoint_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise CheckpointError(f"Invalid JSON in checkpoint file: {e}")

    # Validate schema version
    if "schema_version" not in data:
        raise CheckpointError("Checkpoint missing schema_version field")

    if data["schema_version"] != CHECKPOINT_SCHEMA_VERSION:
        raise CheckpointError(
            f"Schema version mismatch: expected {CHECKPOINT_SCHEMA_VERSION}, "
            f"got {data['schema_version']}"
        )

    # Validate required fields
    required_fields = ["experiment_id", "task_id", "timestamp", "status"]
    for field in required_fields:
        if field not in data:
            raise CheckpointError(f"Checkpoint missing required field: {field}")

    return data


def update_checkpoint(
    checkpoint_path: str,
    status: Optional[str] = None,
    progress: Optional[Dict[str, Any]] = None,
    new_result: Optional[Any] = None,
    error: Optional[str] = None,
    metadata_updates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load an existing checkpoint, update it, and save it back.

    Args:
        checkpoint_path: Path to the checkpoint file.
        status: Optional new status.
        progress: Optional new progress dictionary.
        new_result: Optional new intermediate result to append.
        error: Optional error message to append to error_log.
        metadata_updates: Optional dictionary of metadata updates.

    Returns:
        Updated checkpoint dictionary.

    Raises:
        CheckpointError: If loading or saving fails.
    """
    data = load_checkpoint(checkpoint_path)

    if status is not None:
        data["status"] = status

    if progress is not None:
        data["progress"] = progress

    if new_result is not None:
        data["intermediate_results"].append(new_result)

    if error is not None:
        data["error_log"].append(error)
        data["status"] = "failed"

    if metadata_updates is not None:
        data["metadata"].update(metadata_updates)

    # Update timestamp
    data["timestamp"] = datetime.utcnow().isoformat() + "Z"

    save_checkpoint(data, checkpoint_path=str(Path(checkpoint_path).parent), filename=Path(checkpoint_path).name)

    return data


def create_progress_tracker(
    experiment_id: str,
    task_id: str,
    total_items: int,
    metadata: Optional[Dict[str, Any]] = None,
    checkpoint_dir: Optional[str] = None,
) -> tuple[Path, int]:
    """
    Create an initial checkpoint for tracking progress.

    Args:
        experiment_id: Unique identifier for the experiment.
        task_id: ID of the task.
        total_items: Total number of items to process.
        metadata: Optional metadata.
        checkpoint_dir: Optional directory for checkpoints.

    Returns:
        Tuple of (checkpoint_path, initial_processed_count).
    """
    progress = {
        "total_items": total_items,
        "processed_items": 0,
        "current_item": None,
        "percent_complete": 0.0,
    }

    checkpoint_data = _create_checkpoint_structure(
        experiment_id=experiment_id,
        task_id=task_id,
        status="running",
        metadata=metadata,
        progress=progress,
    )

    checkpoint_path = save_checkpoint(checkpoint_data, checkpoint_dir=checkpoint_dir)

    return checkpoint_path, 0


def advance_progress(
    checkpoint_path: str,
    processed_count: int,
    current_item: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update checkpoint to reflect progress advancement.

    Args:
        checkpoint_path: Path to the checkpoint file.
        processed_count: Number of items processed so far.
        current_item: Index of currently processing item.

    Returns:
        Updated checkpoint dictionary.
    """
    data = load_checkpoint(checkpoint_path)
    total = data["progress"]["total_items"]

    progress = {
        "total_items": total,
        "processed_items": processed_count,
        "current_item": current_item,
        "percent_complete": processed_count / total if total > 0 else 0.0,
    }

    return update_checkpoint(checkpoint_path, progress=progress)


def finalize_checkpoint(
    checkpoint_path: str,
    status: str = "completed",
    final_results: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Mark a checkpoint as completed or failed.

    Args:
        checkpoint_path: Path to the checkpoint file.
        status: Final status ("completed" or "failed").
        final_results: Optional list of final results to append.

    Returns:
        Finalized checkpoint dictionary.
    """
    data = load_checkpoint(checkpoint_path)

    if final_results is not None:
        data["intermediate_results"].extend(final_results)

    return update_checkpoint(checkpoint_path, status=status)
