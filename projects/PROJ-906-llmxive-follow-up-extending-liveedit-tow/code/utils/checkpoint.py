"""
Checkpointing infrastructure for long-running inference tasks.
Supports saving state, resuming from interruptions, and managing CI limits.
"""
import os
import json
import torch
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from .logger import get_logger

logger = get_logger("checkpoint")


class CheckpointManager:
    """
    Manages saving and loading of experiment state to support resumption.
    Handles CI time limits by tracking progress and allowing restarts.
    """

    def __init__(
        self,
        checkpoint_dir: str = "data/checkpoints",
        experiment_id: str = "default",
        save_interval: int = 10  # Save every N clips or steps
    ):
        """
        Initializes the CheckpointManager.

        Args:
            checkpoint_dir: Directory to store checkpoint files.
            experiment_id: Unique identifier for this experiment run.
            save_interval: Frequency of automatic saves (e.g., every N items).
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.experiment_id = experiment_id
        self.save_interval = save_interval
        
        # Ensure directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.last_save_index = -1
        self.total_processed = 0
        self.current_step = 0
        self._logger = get_logger("checkpoint")

    def get_checkpoint_path(self, step: int) -> Path:
        """Generates the path for a specific step checkpoint."""
        return self.checkpoint_dir / f"{self.experiment_id}_step_{step}.pt"

    def get_latest_checkpoint_path(self) -> Optional[Path]:
        """Finds the most recent checkpoint file."""
        pattern = f"{self.experiment_id}_step_*.pt"
        matches = list(self.checkpoint_dir.glob(pattern))
        if not matches:
            return None
        # Sort by step number in filename
        matches.sort(key=lambda p: int(p.stem.split('_')[-1]))
        return matches[-1]

    def save(
        self,
        state: Dict[str, Any],
        step: int,
        clip_id: Optional[str] = None
    ) -> None:
        """
        Saves the current state to a checkpoint file.

        Args:
            state: Dictionary containing model weights, optimizer state, etc.
            step: Current step index (e.g., clip index).
            clip_id: Optional ID of the clip being processed.
        """
        checkpoint_data = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.experiment_id,
            "state": state,
            "metadata": {
                "clip_id": clip_id,
                "total_processed": self.total_processed
            }
        }

        path = self.get_checkpoint_path(step)
        try:
            torch.save(checkpoint_data, path)
            self.last_save_index = step
            self._logger.info(f"Checkpoint saved at step {step} to {path}")
        except Exception as e:
            self._logger.error(f"Failed to save checkpoint at step {step}: {e}")
            raise

    def load(self) -> Optional[Dict[str, Any]]:
        """
        Loads the latest checkpoint if available.

        Returns:
            The checkpoint data dictionary, or None if no checkpoint exists.
        """
        latest_path = self.get_latest_checkpoint_path()
        if latest_path is None:
            self._logger.info("No existing checkpoint found. Starting fresh.")
            return None

        try:
            data = torch.load(latest_path, map_location="cpu")
            self._logger.info(f"Loaded checkpoint from {latest_path} (Step: {data['step']})")
            return data
        except Exception as e:
            self._logger.warning(f"Failed to load checkpoint {latest_path}: {e}")
            return None

    def should_save(self, current_index: int) -> bool:
        """
        Determines if a save should occur based on the save interval.

        Args:
            current_index: The current item index being processed.

        Returns:
            True if a save is due, False otherwise.
        """
        # Save at start (0), at intervals, and potentially at end (handled externally)
        if current_index == 0:
            return True
        if (current_index + 1) % self.save_interval == 0:
            return True
        return False

    def mark_processed(self, clip_id: str, metrics: Optional[Dict[str, float]] = None) -> None:
        """
        Updates internal counters after a clip is successfully processed.
        Does not save to disk unless `should_save` returns True.
        
        Args:
            clip_id: ID of the processed clip.
            metrics: Optional dictionary of metrics to store in metadata.
        """
        self.total_processed += 1
        self.current_step += 1
        # Note: Actual saving logic is usually handled by the runner loop
        # calling save() explicitly when should_save() is true.
        self._logger.debug(f"Marked clip {clip_id} as processed. Total: {self.total_processed}")

    def resume_from_checkpoint(self, state_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Resumes the experiment from the latest checkpoint.
        
        Args:
            state_dict: Optional pre-loaded state dict to use instead of loading from disk.
        
        Returns:
            The step index to resume from.
        """
        if state_dict is None:
            data = self.load()
            if data is None:
                return 0
            state_dict = data
        
        self.current_step = state_dict.get("step", 0)
        self.total_processed = state_dict.get("metadata", {}).get("total_processed", 0)
        self._logger.info(f"Resuming from step {self.current_step}")
        return self.current_step
