"""
Checkpoint and Restart mechanism for Monte Carlo simulations.

This module implements a robust checkpointing system that:
1. Persists the current state of Monte Carlo replicates to `state/checkpoint.json`.
2. Enforces the Constitution Principle VI: Exactly 100 replicates are required.
3. Fails loudly if the limit is exceeded or if a run is attempted with an invalid state.
4. Supports restart from the last completed replicate.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import logger setup from existing project infrastructure
from src.logger import get_logger

# Constants
MONTE_CARLO_REPLICATE_LIMIT = 100
CHECKPOINT_FILE_NAME = "checkpoint.json"
STATE_DIR_NAME = "state"

# Ensure the project root is in the path if running as a script
if __name__ == "__main__":
    # Add parent directory to path to allow imports if running directly
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

class CheckpointError(Exception):
    """Custom exception for checkpoint-related errors."""
    pass

class CheckpointManager:
    """
    Manages the state of Monte Carlo simulations, enforcing the 100 replicate limit.
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize the CheckpointManager.

        Args:
            state_dir: Path to the state directory. Defaults to 'state' relative to project root.
        """
        if state_dir is None:
            # Determine project root relative to this file
            state_dir = Path(__file__).parent.parent.parent / "state"
        
        self.state_dir = state_dir
        self.checkpoint_path = self.state_dir / CHECKPOINT_FILE_NAME
        self.logger = get_logger(__name__)
        
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_checkpoint(self) -> Dict[str, Any]:
        """
        Load the checkpoint file if it exists.

        Returns:
            Dictionary containing checkpoint data (replicate_count, results, etc.).
            Returns a default structure if file does not exist.

        Raises:
            CheckpointError: If the checkpoint file is corrupted or invalid.
        """
        if not self.checkpoint_path.exists():
            self.logger.info("No existing checkpoint found. Starting fresh.")
            return {
                "replicate_count": 0,
                "completed_replicates": [],
                "results_summary": {},
                "status": "initialized"
            }

        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if "replicate_count" not in data:
                raise CheckpointError("Checkpoint file missing 'replicate_count'.")
            
            self.logger.info(f"Loaded checkpoint: {data['replicate_count']} replicates completed.")
            return data

        except json.JSONDecodeError as e:
            raise CheckpointError(f"Checkpoint file corrupted (JSON decode error): {e}")
        except Exception as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}")

    def save_checkpoint(self, data: Dict[str, Any]) -> None:
        """
        Save the current state to the checkpoint file.

        Args:
            data: Dictionary containing the current simulation state.
        """
        try:
            # Atomic write: write to temp file then rename
            temp_path = self.checkpoint_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            os.replace(temp_path, self.checkpoint_path)
            self.logger.debug(f"Checkpoint saved to {self.checkpoint_path}")
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            raise

    def get_next_replicate_id(self, current_state: Dict[str, Any]) -> int:
        """
        Determine the ID of the next replicate to run.

        Args:
            current_state: The loaded checkpoint state.

        Returns:
            The next replicate ID (1-indexed).
        """
        count = current_state.get("replicate_count", 0)
        next_id = count + 1
        self.logger.info(f"Next replicate ID: {next_id}")
        return next_id

    def enforce_replicate_limit(self, current_count: int) -> None:
        """
        Enforce the Constitution Principle VI: 100 replicates limit.

        This method MUST fail the run if the limit is exceeded.
        NO fallback to 50 replicates or any other number.

        Args:
            current_count: The number of replicates completed so far.

        Raises:
            CheckpointError: If the limit is exceeded.
        """
        if current_count > MONTE_CARLO_REPLICATE_LIMIT:
            error_msg = (
                f"CRITICAL ERROR: Replicate limit exceeded. "
                f"Current count: {current_count}, Limit: {MONTE_CARLO_REPLICATE_LIMIT}. "
                f"Per Constitution Principle VI, exactly {MONTE_CARLO_REPLICATE_LIMIT} replicates are required. "
                f"The run has exceeded this limit and must be terminated."
            )
            self.logger.critical(error_msg)
            raise CheckpointError(error_msg)

        if current_count == MONTE_CARLO_REPLICATE_LIMIT:
            self.logger.info(f"Target of {MONTE_CARLO_REPLICATE_LIMIT} replicates reached. Simulation complete.")

    def update_state(self, current_state: Dict[str, Any], replicate_id: int, result: Any) -> Dict[str, Any]:
        """
        Update the checkpoint state with a new replicate result.

        Args:
            current_state: The current state dictionary.
            replicate_id: The ID of the completed replicate.
            result: The result data from the replicate.

        Returns:
            Updated state dictionary.
        """
        current_state["replicate_count"] = replicate_id
        if "completed_replicates" not in current_state:
            current_state["completed_replicates"] = []
        
        current_state["completed_replicates"].append(replicate_id)
        current_state["status"] = "running" if replicate_id < MONTE_CARLO_REPLICATE_LIMIT else "completed"

        # Enforce limit immediately after update
        self.enforce_replicate_limit(replicate_id)

        return current_state

    def is_complete(self, current_state: Dict[str, Any]) -> bool:
        """
        Check if the simulation has completed all required replicates.

        Args:
            current_state: The current state dictionary.

        Returns:
            True if exactly 100 replicates are completed, False otherwise.
        """
        return current_state.get("replicate_count", 0) >= MONTE_CARLO_REPLICATE_LIMIT

    def reset(self) -> None:
        """
        Reset the checkpoint by removing the checkpoint file.
        Use with caution.
        """
        if self.checkpoint_path.exists():
            self.checkpoint_path.unlink()
            self.logger.info("Checkpoint reset.")

def main():
    """
    Demonstrate the checkpoint mechanism.
    This function simulates a loop that would run in the Monte Carlo runner.
    """
    manager = CheckpointManager()
    
    # Load existing state
    state = manager.load_checkpoint()
    
    # Check if already complete
    if manager.is_complete(state):
        print(f"Simulation already complete with {state['replicate_count']} replicates.")
        return

    # Determine starting point
    next_id = manager.get_next_replicate_id(state)
    
    # Simulate running replicates (in real usage, this loop would be in the runner)
    # We simulate up to the limit to demonstrate the enforcement
    print(f"Starting simulation from replicate {next_id}. Limit: {MONTE_CARLO_REPLICATE_LIMIT}.")
    
    try:
        for i in range(next_id, MONTE_CARLO_REPLICATE_LIMIT + 1):
            # Simulate work
            # print(f"Running replicate {i}...")
            
            # Update state
            state = manager.update_state(state, i, {"status": "success", "replicate_id": i})
            
            # Save checkpoint after each replicate
            manager.save_checkpoint(state)
            
            # Check completion
            if manager.is_complete(state):
                print(f"Successfully completed {MONTE_CARLO_REPLICATE_LIMIT} replicates.")
                break
    
        # Test the limit enforcement by trying to go one past
        # This would happen if a bug in the runner tried to run one too many
        try:
            state = manager.update_state(state, MONTE_CARLO_REPLICATE_LIMIT + 1, {"status": "should_fail"})
            print("ERROR: Should have raised an exception for exceeding limit.")
        except CheckpointError as e:
            print(f"Correctly caught limit enforcement error: {str(e)[:100]}...")

    except CheckpointError as e:
        print(f"Checkpoint error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()