"""
Experiment state management for tracking sample counts and budget caps.

This module provides a thread-safe mechanism to track the number of samples
processed, generations attempted, and remaining budget for the experiment.
State is persisted to disk to allow recovery across runs.
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict, field
from datetime import datetime

from config import ensure_directories, get_budget_generations


@dataclass
class ExperimentState:
    """
    Represents the current state of the experiment.

    Attributes:
        total_samples: Total number of unique samples (tasks) processed.
        total_generations: Total number of generation attempts made.
        budget_limit: Maximum allowed generations (from config).
        start_time: Timestamp when the experiment started.
        last_update: Timestamp of the last state update.
        samples_by_type: Count of samples processed by perturbation type.
        generations_by_type: Count of generations by perturbation type.
        status: Current status ('running', 'completed', 'exhausted').
    """
    total_samples: int = 0
    total_generations: int = 0
    budget_limit: int = 0
    start_time: Optional[str] = None
    last_update: Optional[str] = None
    samples_by_type: Dict[str, int] = field(default_factory=dict)
    generations_by_type: Dict[str, int] = field(default_factory=dict)
    status: str = "running"

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentState":
        """Create state from dictionary."""
        return cls(**data)


_state_lock = threading.Lock()
_current_state: Optional[ExperimentState] = None
_state_file_path: Optional[Path] = None


def get_state_file_path() -> Path:
    """Get the path to the state file."""
    ensure_directories()
    return Path("data/logs/experiment_state.json")


def get_state() -> ExperimentState:
    """
    Get the current experiment state, loading from disk if necessary.

    Returns:
        The current ExperimentState object.
    """
    global _current_state, _state_file_path

    with _state_lock:
        if _current_state is not None:
            return _current_state

        _state_file_path = get_state_file_path()
        if _state_file_path.exists():
            try:
                with open(_state_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _current_state = ExperimentState.from_dict(data)
                    return _current_state
            except (json.JSONDecodeError, KeyError) as e:
                # Corrupted state file, reset
                _current_state = _create_initial_state()
        else:
            _current_state = _create_initial_state()

        return _current_state


def _create_initial_state() -> ExperimentState:
    """Create a new initial state."""
    state = ExperimentState(
        budget_limit=get_budget_generations(),
        start_time=datetime.now().isoformat(),
        last_update=datetime.now().isoformat(),
        status="running"
    )
    return state


def reset_state() -> None:
    """Reset the state to initial values."""
    global _current_state
    with _state_lock:
        _current_state = _create_initial_state()
        save_state()


def save_state() -> None:
    """
    Save the current state to disk.

    Raises:
        IOError: If writing to the state file fails.
    """
    global _current_state, _state_file_path

    with _state_lock:
        if _current_state is None:
            _current_state = get_state()

        _current_state.last_update = datetime.now().isoformat()

        if _state_file_path is None:
            _state_file_path = get_state_file_path()

        _current_state.status = "completed" if is_exhausted() else "running"

        with open(_state_file_path, "w", encoding="utf-8") as f:
            json.dump(_current_state.to_dict(), f, indent=2)


def increment_samples(count: int = 1, sample_type: str = "original") -> None:
    """
    Increment the sample count.

    Args:
        count: Number of samples to add.
        sample_type: Type of sample (e.g., 'original', 'synonym', 'typo').
    """
    with _state_lock:
        state = get_state()
        state.total_samples += count

        if sample_type not in state.samples_by_type:
            state.samples_by_type[sample_type] = 0
        state.samples_by_type[sample_type] += count

        save_state()


def increment_generations(count: int = 1, generation_type: str = "original") -> None:
    """
    Increment the generation count.

    Args:
        count: Number of generations to add.
        generation_type: Type of generation (e.g., 'original', 'synonym', 'typo').
    """
    with _state_lock:
        state = get_state()
        state.total_generations += count

        if generation_type not in state.generations_by_type:
            state.generations_by_type[generation_type] = 0
        state.generations_by_type[generation_type] += count

        # Check if budget is exhausted
        if state.total_generations >= state.budget_limit:
            state.status = "exhausted"

        save_state()


def get_remaining() -> int:
    """
    Get the remaining generation budget.

    Returns:
        Number of generations remaining before budget is exhausted.
    """
    state = get_state()
    return max(0, state.budget_limit - state.total_generations)


def is_exhausted() -> bool:
    """
    Check if the generation budget is exhausted.

    Returns:
        True if budget is exhausted, False otherwise.
    """
    state = get_state()
    return state.total_generations >= state.budget_limit


def set_budget_caps(new_limit: Optional[int] = None) -> None:
    """
    Update the budget limit.

    Args:
        new_limit: New budget limit. If None, uses config value.
    """
    with _state_lock:
        state = get_state()
        if new_limit is not None:
            state.budget_limit = new_limit
        else:
            state.budget_limit = get_budget_generations()
        save_state()


def get_state_summary() -> Dict[str, Any]:
    """
    Get a summary of the current state.

    Returns:
        Dictionary with key state metrics.
    """
    state = get_state()
    return {
        "total_samples": state.total_samples,
        "total_generations": state.total_generations,
        "budget_limit": state.budget_limit,
        "remaining": get_remaining(),
        "status": state.status,
        "samples_by_type": state.samples_by_type,
        "generations_by_type": state.generations_by_type,
        "start_time": state.start_time,
        "last_update": state.last_update,
        "exhausted": is_exhausted()
    }


def main() -> None:
    """
    Command-line interface for state management.

    Usage:
        python -m utils.state [command] [args]

    Commands:
        status      - Show current state summary
        reset       - Reset state to initial values
        remaining   - Show remaining budget
        set-limit   - Set new budget limit
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.state <command>")
        print("Commands: status, reset, remaining, set-limit <value>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        summary = get_state_summary()
        print(json.dumps(summary, indent=2))
    elif command == "reset":
        reset_state()
        print("State reset successfully.")
    elif command == "remaining":
        remaining = get_remaining()
        print(f"Remaining budget: {remaining}")
    elif command == "set-limit":
        if len(sys.argv) < 3:
            print("Error: set-limit requires a value")
            sys.exit(1)
        try:
            new_limit = int(sys.argv[2])
            set_budget_caps(new_limit)
            print(f"Budget limit set to {new_limit}")
        except ValueError:
            print("Error: Invalid limit value")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()