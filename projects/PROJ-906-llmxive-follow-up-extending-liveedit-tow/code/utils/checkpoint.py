"""
Checkpointing infrastructure for the llmXive pipeline.
Handles state serialization, resume capability, and CI limit management.
"""
import os
import json
import torch
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# Import config and logger
try:
    from config import ensure_directories
    from utils.logger import get_logger
except ImportError:
    # Fallback for standalone execution
    def ensure_directories(base: str = "data"):
        os.makedirs(base, exist_ok=True)
        os.makedirs(os.path.join(base, "flow"), exist_ok=True)
        os.makedirs(os.path.join(base, "metrics"), exist_ok=True)
    
    # Fallback logger
    import logging
    def get_logger(name: Optional[str] = None) -> logging.Logger:
        logger = logging.getLogger(name or "checkpoint")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

logger = get_logger("checkpoint")
CHECKPOINT_DIR = "data/checkpoints"

class CheckpointManager:
    """
    Manages saving and loading of pipeline states.
    """
    def __init__(self, run_id: str, checkpoint_dir: Optional[str] = None):
        """
        Initializes the CheckpointManager.

        Args:
            run_id: Unique identifier for the current run.
            checkpoint_dir: Directory to store checkpoints. Defaults to data/checkpoints.
        """
        self.run_id = run_id
        self.checkpoint_dir = checkpoint_dir or CHECKPOINT_DIR
        self.logger = get_logger(f"checkpoint.{run_id}")
        
        # Ensure checkpoint directory exists
        ensure_directories(self.checkpoint_dir)
        
        self.file_path = os.path.join(self.checkpoint_dir, f"{run_id}.json")
        self.logger.info(f"CheckpointManager initialized for run_id: {run_id}")

    def save_state(self, state: Dict[str, Any]) -> None:
        """
        Saves the current state to a JSON file.

        Args:
            state: Dictionary containing the state to save (e.g., model weights, optimizer state, current step).
        """
        try:
            # Serialize torch tensors to CPU and lists/arrays if needed
            serializable_state = {}
            for key, value in state.items():
                if isinstance(value, torch.Tensor):
                    serializable_state[key] = value.cpu().numpy().tolist()
                elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
                    serializable_state[key] = value
                else:
                    # Try to convert other types to string or skip
                    try:
                        serializable_state[key] = json.dumps(value)
                    except TypeError:
                        self.logger.warning(f"Skipping non-serializable key: {key}")
            
            with open(self.file_path, 'w') as f:
                json.dump(serializable_state, f, indent=2)
            
            self.logger.info(f"State saved to {self.file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
            raise

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Loads the state from the JSON file if it exists.

        Returns:
            Dictionary containing the loaded state, or None if file doesn't exist.
        """
        if not os.path.exists(self.file_path):
            self.logger.warning(f"Checkpoint file not found: {self.file_path}")
            return None

        try:
            with open(self.file_path, 'r') as f:
                loaded_state = json.load(f)
            
            # Convert lists back to numpy arrays/tensors if necessary
            # For now, returning raw JSON data. The caller should handle conversion.
            self.logger.info(f"State loaded from {self.file_path}")
            return loaded_state
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            raise

    def delete_checkpoint(self) -> bool:
        """
        Deletes the checkpoint file.

        Returns:
            True if deleted, False if file didn't exist or error occurred.
        """
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                self.logger.info(f"Checkpoint deleted: {self.file_path}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to delete checkpoint: {e}")
                return False
        return False

def save_state(state: Dict[str, Any], run_id: str, checkpoint_dir: Optional[str] = None) -> None:
    """
    Convenience function to save state using a CheckpointManager.

    Args:
        state: Dictionary containing the state to save.
        run_id: Unique identifier for the run.
        checkpoint_dir: Directory to store checkpoints.
    """
    manager = CheckpointManager(run_id, checkpoint_dir)
    manager.save_state(state)

def load_state(run_id: str, checkpoint_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load state using a CheckpointManager.

    Args:
        run_id: Unique identifier for the run.
        checkpoint_dir: Directory to store checkpoints.

    Returns:
        Dictionary containing the loaded state, or None if not found.
    """
    manager = CheckpointManager(run_id, checkpoint_dir)
    return manager.load_state()
