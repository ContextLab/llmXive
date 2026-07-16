"""
Experiment state management module.

Tracks sample counts, generation counts, and enforces budget caps for the
robustness evaluation pipeline. Provides thread-safe operations for concurrent
execution scenarios.
"""
import json
import os
import threading
from pathlib import Path
from typing import Dict, Optional, Any, List

from config import ensure_directories

# Default configuration values
DEFAULT_MAX_SAMPLES = 1000
DEFAULT_MAX_GENERATIONS = 5000
STATE_FILE_NAME = "experiment_state.json"

# Global state instance with thread lock
_state_lock = threading.Lock()
_current_state: Optional["ExperimentState"] = None
_state_file_path: Optional[Path] = None


class ExperimentState:
    """
    Represents the current state of the experiment execution.

    Tracks:
    - Total samples processed (original + perturbed)
    - Total generations attempted
    - Budget caps (max samples, max generations)
    - Start time and last update time
    - Status flags (exhausted, paused, completed)
    """

    def __init__(
        self,
        max_samples: int = DEFAULT_MAX_SAMPLES,
        max_generations: int = DEFAULT_MAX_GENERATIONS,
        samples_processed: int = 0,
        generations_attempted: int = 0,
        start_time: Optional[str] = None,
        last_update: Optional[str] = None,
        status: str = "initialized"
    ):
        self.max_samples = max_samples
        self.max_generations = max_generations
        self.samples_processed = samples_processed
        self.generations_attempted = generations_attempted
        self.start_time = start_time or self._get_timestamp()
        self.last_update = last_update or self._get_timestamp()
        self.status = status

    @staticmethod
    def _get_timestamp() -> str:
        """Return current ISO format timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "max_samples": self.max_samples,
            "max_generations": self.max_generations,
            "samples_processed": self.samples_processed,
            "generations_attempted": self.generations_attempted,
            "start_time": self.start_time,
            "last_update": self.last_update,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExperimentState":
        """Create ExperimentState from dictionary."""
        return cls(
            max_samples=data.get("max_samples", DEFAULT_MAX_SAMPLES),
            max_generations=data.get("max_generations", DEFAULT_MAX_GENERATIONS),
            samples_processed=data.get("samples_processed", 0),
            generations_attempted=data.get("generations_attempted", 0),
            start_time=data.get("start_time"),
            last_update=data.get("last_update"),
            status=data.get("status", "initialized")
        )

    def update(self, **kwargs: Any) -> None:
        """Update state fields with provided values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_update = self._get_timestamp()

    def is_exhausted(self) -> bool:
        """Check if any budget cap has been reached."""
        return (
            self.samples_processed >= self.max_samples or
            self.generations_attempted >= self.max_generations
        )

    def remaining_samples(self) -> int:
        """Calculate remaining sample budget."""
        return max(0, self.max_samples - self.samples_processed)

    def remaining_generations(self) -> int:
        """Calculate remaining generation budget."""
        return max(0, self.max_generations - self.generations_attempted)


def get_state_file_path() -> Path:
    """Get the path to the state file."""
    global _state_file_path
    if _state_file_path is None:
        ensure_directories()
        _state_file_path = Path("data") / "logs" / STATE_FILE_NAME
    return _state_file_path


def get_state() -> ExperimentState:
    """
    Get the current experiment state, loading from disk if available.

    Thread-safe: uses a lock to prevent race conditions during state loading.
    """
    global _current_state

    with _state_lock:
        if _current_state is None:
            state_path = get_state_file_path()
            if state_path.exists():
                try:
                    with open(state_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        _current_state = ExperimentState.from_dict(data)
                except (json.JSONDecodeError, KeyError) as e:
                    # Corrupted state file - reset to default
                    _current_state = ExperimentState()
            else:
                _current_state = ExperimentState()
        return _current_state


def reset_state(max_samples: Optional[int] = None, max_generations: Optional[int] = None) -> ExperimentState:
    """
    Reset the experiment state to initial values.

    Args:
        max_samples: New max samples limit (uses default if None)
        max_generations: New max generations limit (uses default if None)

    Returns:
        The reset ExperimentState instance.
    """
    global _current_state

    with _state_lock:
        _current_state = ExperimentState(
            max_samples=max_samples if max_samples is not None else DEFAULT_MAX_SAMPLES,
            max_generations=max_generations if max_generations is not None else DEFAULT_MAX_GENERATIONS,
            status="reset"
        )
        save_state(_current_state)
        return _current_state


def save_state(state: Optional[ExperimentState] = None) -> None:
    """
    Save the current state to disk.

    Args:
        state: State to save. If None, uses the current global state.
    """
    if state is None:
        state = get_state()

    state_path = get_state_file_path()
    ensure_directories()

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)


def increment_samples(count: int = 1) -> int:
    """
    Increment the samples processed counter.

    Args:
        count: Number of samples to add (default: 1)

    Returns:
        The new total samples processed count.
    """
    state = get_state()
    state.samples_processed += count
    state.update(status="running" if not state.is_exhausted() else "exhausted")
    save_state(state)
    return state.samples_processed


def increment_generations(count: int = 1) -> int:
    """
    Increment the generations attempted counter.

    Args:
        count: Number of generations to add (default: 1)

    Returns:
        The new total generations attempted count.
    """
    state = get_state()
    state.generations_attempted += count
    state.update(status="running" if not state.is_exhausted() else "exhausted")
    save_state(state)
    return state.generations_attempted


def get_remaining() -> Dict[str, int]:
    """
    Get the remaining budget counts.

    Returns:
        Dictionary with 'samples' and 'generations' keys.
    """
    state = get_state()
    return {
        "samples": state.remaining_samples(),
        "generations": state.remaining_generations()
    }


def is_exhausted() -> bool:
    """
    Check if the experiment budget is exhausted.

    Returns:
        True if any budget cap has been reached, False otherwise.
    """
    state = get_state()
    return state.is_exhausted()


def set_budget_caps(max_samples: int, max_generations: int) -> None:
    """
    Update the budget caps for the experiment.

    Args:
        max_samples: New maximum samples limit
        max_generations: New maximum generations limit
    """
    state = get_state()
    state.max_samples = max_samples
    state.max_generations = max_generations
    state.update(status="running")
    save_state(state)


def get_state_summary() -> Dict[str, Any]:
    """
    Get a summary of the current experiment state.

    Returns:
        Dictionary containing key state metrics.
    """
    state = get_state()
    return {
        "samples_processed": state.samples_processed,
        "max_samples": state.max_samples,
        "remaining_samples": state.remaining_samples(),
        "generations_attempted": state.generations_attempted,
        "max_generations": state.max_generations,
        "remaining_generations": state.remaining_generations(),
        "status": state.status,
        "is_exhausted": state.is_exhausted(),
        "start_time": state.start_time,
        "last_update": state.last_update
    }


def main() -> None:
    """
    CLI entry point for state management utilities.

    Usage:
        python code/utils/state.py [command] [args]

    Commands:
        status       - Display current state summary
        reset        - Reset state to initial values
        set-caps     - Update budget caps (requires --samples and --generations)
        increment    - Increment counters (requires --samples and/or --generations)
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Experiment state management utility"
    )
    parser.add_argument(
        "command",
        choices=["status", "reset", "set-caps", "increment"],
        help="Command to execute"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Number of samples (for set-caps or increment)"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=None,
        help="Number of generations (for set-caps or increment)"
    )

    args = parser.parse_args()

    if args.command == "status":
        summary = get_state_summary()
        print(json.dumps(summary, indent=2))

    elif args.command == "reset":
        reset_state()
        print("State reset successfully.")
        print(json.dumps(get_state_summary(), indent=2))

    elif args.command == "set-caps":
        if args.samples is None or args.generations is None:
            print("Error: --samples and --generations are required for set-caps", file=sys.stderr)
            sys.exit(1)
        set_budget_caps(args.samples, args.generations)
        print(f"Budget caps updated: max_samples={args.samples}, max_generations={args.generations}")
        print(json.dumps(get_state_summary(), indent=2))

    elif args.command == "increment":
        samples_added = args.samples if args.samples is not None else 0
        generations_added = args.generations if args.generations is not None else 0

        if samples_added > 0:
            new_total = increment_samples(samples_added)
            print(f"Samples incremented by {samples_added}. Total: {new_total}")

        if generations_added > 0:
            new_total = increment_generations(generations_added)
            print(f"Generations incremented by {generations_added}. Total: {new_total}")

        print(json.dumps(get_state_summary(), indent=2))


if __name__ == "__main__":
    main()