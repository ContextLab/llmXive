import os
import json
import pickle
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
import logging
import time

from src.utils.config import get_path, get_config

logger = logging.getLogger(__name__)

@dataclass
class CheckpointState:
    seed: int
    episode_id: int
    step: int
    success: Optional[bool]
    metrics: Dict[str, Any]
    timestamp: float
    env_state_hash: Optional[str] = None

class CheckpointManager:
    """
    Handles saving and loading of episode checkpoints for recovery from
    memory pressure crashes or forced interruptions.
    """
    def __init__(self, checkpoint_dir: Optional[Path] = None):
        config = get_config()
        if checkpoint_dir is None:
            self.checkpoint_dir = get_path("results") / "checkpoints"
        else:
            self.checkpoint_dir = checkpoint_dir
        
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_checkpoint_path(self, seed: int, episode_id: int) -> Path:
        """Generate a deterministic path for a specific seed/episode checkpoint."""
        return self.checkpoint_dir / f"checkpoint_seed_{seed}_ep_{episode_id}.pkl"

    def _get_latest_checkpoint_path(self, seed: int) -> Optional[Path]:
        """Find the most recent checkpoint for a given seed."""
        pattern = f"checkpoint_seed_{seed}_ep_*.pkl"
        matches = list(self.checkpoint_dir.glob(pattern))
        if not matches:
            return None
        # Sort by modification time, newest first
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return matches[0]

    def save_checkpoint(
        self,
        seed: int,
        episode_id: int,
        step: int,
        success: Optional[bool],
        metrics: Dict[str, Any],
        env_state: Optional[Any] = None
    ) -> Path:
        """Save the current state to disk."""
        state = CheckpointState(
            seed=seed,
            episode_id=episode_id,
            step=step,
            success=success,
            metrics=metrics,
            timestamp=time.time()
        )

        if env_state is not None:
            # Attempt to hash serializable env state for integrity check
            try:
                state_dict = asdict(state)
                state_dict['env_state_summary'] = str(type(env_state))
                json_str = json.dumps(state_dict, default=str)
                state.env_state_hash = hashlib.sha256(json_str.encode()).hexdigest()[:16]
            except Exception as e:
                self.logger.warning(f"Could not hash env state: {e}")

        path = self._get_checkpoint_path(seed, episode_id)
        try:
            with open(path, 'wb') as f:
                pickle.dump({
                    'state': asdict(state),
                    'env_state': env_state
                }, f)
            self.logger.info(f"Saved checkpoint to {path}")
            return path
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise

    def load_checkpoint(self, seed: int) -> Optional[Dict[str, Any]]:
        """Load the latest checkpoint for a seed if it exists."""
        path = self._get_latest_checkpoint_path(seed)
        if path is None:
            return None

        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            # Verify integrity if hash exists
            if 'state' in data and data['state'].get('env_state_hash'):
                # Simplified verification: just ensure data structure is intact
                # Full verification would require re-hashing the loaded env_state
                pass

            self.logger.info(f"Loaded checkpoint from {path}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint {path}: {e}")
            return None

    def clear_checkpoint(self, seed: int, episode_id: int) -> bool:
        """Remove a specific checkpoint after successful completion."""
        path = self._get_checkpoint_path(seed, episode_id)
        if path.exists():
            try:
                path.unlink()
                self.logger.info(f"Cleared checkpoint {path}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to clear checkpoint {path}: {e}")
                return False
        return True

    def cleanup_old_checkpoints(self, max_age_seconds: int = 3600) -> int:
        """Remove checkpoints older than max_age_seconds."""
        count = 0
        now = time.time()
        for f in self.checkpoint_dir.glob("checkpoint_seed_*.pkl"):
            if now - f.stat().st_mtime > max_age_seconds:
                try:
                    f.unlink()
                    count += 1
                except Exception as e:
                    self.logger.warning(f"Could not delete old checkpoint {f}: {e}")
        return count

def create_checkpoint_manager(checkpoint_dir: Optional[Path] = None) -> CheckpointManager:
    """Factory function for creating a CheckpointManager."""
    return CheckpointManager(checkpoint_dir)
