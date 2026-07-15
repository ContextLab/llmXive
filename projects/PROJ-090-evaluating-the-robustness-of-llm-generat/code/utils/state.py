"""
Experiment state management for tracking sample counts and budget caps.

This module provides a singleton-style state manager to track:
- Total samples processed (original + perturbed)
- Budget caps for generation limits
- Current counts for monitoring against caps

Thread-safe for potential parallel execution scenarios.
"""
import json
import os
import threading
from pathlib import Path
from typing import Dict, Optional, Any

from config import ensure_directories


class ExperimentState:
    """
    Singleton-like state manager for experiment tracking.

    Tracks sample counts and enforces budget caps across the pipeline.
    State is persisted to disk in data/logs/state.json for recovery.
    """

    _instance: Optional['ExperimentState'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, state_file: Optional[str] = None):
        if self._initialized:
            return

        self._initialized = True
        self._state_file = state_file or "data/logs/experiment_state.json"
        self._lock = threading.Lock()

        # Initialize state structure
        self._state = {
            "total_samples": 0,
            "original_tasks": 0,
            "perturbed_tasks": 0,
            "budget_cap": 1000,  # Default cap, can be overridden
            "current_generation_count": 0,
            "max_generations": 1000,
            "started_at": None,
            "last_updated": None,
            "status": "initialized"
        }

        # Load existing state if available
        self._load_state()

    def _load_state(self) -> None:
        """Load state from disk if it exists."""
        state_path = Path(self._state_file)
        if state_path.exists():
            try:
                with open(state_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge loaded state with defaults
                    for key, value in loaded.items():
                        if key in self._state:
                            self._state[key] = value
            except (json.JSONDecodeError, IOError) as e:
                # If state file is corrupted, start fresh
                self._state["status"] = "corrupted_recovered"

    def _save_state(self) -> None:
        """Persist state to disk."""
        import datetime
        self._state["last_updated"] = datetime.datetime.now().isoformat()

        # Ensure directory exists
        ensure_directories()

        state_path = Path(self._state_file)
        with open(state_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    def reset(self, budget_cap: Optional[int] = None, max_generations: Optional[int] = None) -> None:
        """
        Reset state to initial values.

        Args:
            budget_cap: New budget cap for total samples
            max_generations: New limit for generation count
        """
        with self._lock:
            import datetime
            self._state = {
                "total_samples": 0,
                "original_tasks": 0,
                "perturbed_tasks": 0,
                "budget_cap": budget_cap or self._state["budget_cap"],
                "current_generation_count": 0,
                "max_generations": max_generations or self._state["max_generations"],
                "started_at": datetime.datetime.now().isoformat(),
                "last_updated": None,
                "status": "running"
            }
            self._save_state()

    def increment_original(self, count: int = 1) -> bool:
        """
        Increment original task count.

        Args:
            count: Number of original tasks to add

        Returns:
            True if increment succeeded, False if budget exceeded
        """
        with self._lock:
            if self._state["total_samples"] + count > self._state["budget_cap"]:
                self._state["status"] = "budget_exceeded"
                self._save_state()
                return False

            self._state["original_tasks"] += count
            self._state["total_samples"] += count
            self._save_state()
            return True

    def increment_perturbed(self, count: int = 1) -> bool:
        """
        Increment perturbed task count.

        Args:
            count: Number of perturbed tasks to add

        Returns:
            True if increment succeeded, False if budget exceeded
        """
        with self._lock:
            if self._state["total_samples"] + count > self._state["budget_cap"]:
                self._state["status"] = "budget_exceeded"
                self._save_state()
                return False

            self._state["perturbed_tasks"] += count
            self._state["total_samples"] += count
            self._save_state()
            return True

    def increment_generation(self, count: int = 1) -> bool:
        """
        Increment generation count (used for budget cap logic).

        Args:
            count: Number of generations to add

        Returns:
            True if increment succeeded, False if max_generations exceeded
        """
        with self._lock:
            if self._state["current_generation_count"] + count > self._state["max_generations"]:
                self._state["status"] = "generation_limit_reached"
                self._save_state()
                return False

            self._state["current_generation_count"] += count
            self._save_state()
            return True

    def get_remaining_budget(self) -> int:
        """Get remaining sample budget."""
        with self._lock:
            return max(0, self._state["budget_cap"] - self._state["total_samples"])

    def get_remaining_generations(self) -> int:
        """Get remaining generation count."""
        with self._lock:
            return max(0, self._state["max_generations"] - self._state["current_generation_count"])

    def is_budget_exceeded(self) -> bool:
        """Check if budget cap has been exceeded."""
        with self._lock:
            return self._state["total_samples"] >= self._state["budget_cap"]

    def is_generation_limit_reached(self) -> bool:
        """Check if generation limit has been reached."""
        with self._lock:
            return self._state["current_generation_count"] >= self._state["max_generations"]

    def get_state(self) -> Dict[str, Any]:
        """Get a copy of current state."""
        with self._lock:
            return self._state.copy()

    def set_budget_cap(self, cap: int) -> None:
        """Update the budget cap."""
        with self._lock:
            self._state["budget_cap"] = cap
            self._save_state()

    def set_max_generations(self, limit: int) -> None:
        """Update the maximum generation limit."""
        with self._lock:
            self._state["max_generations"] = limit
            self._save_state()

    def finalize(self) -> None:
        """Mark experiment as completed."""
        with self._lock:
            import datetime
            self._state["status"] = "completed"
            self._state["last_updated"] = datetime.datetime.now().isoformat()
            self._save_state()


# Convenience functions for direct access
def get_state() -> Dict[str, Any]:
    """Get current experiment state."""
    return ExperimentState().get_state()

def reset_state(budget_cap: Optional[int] = None, max_generations: Optional[int] = None) -> None:
    """Reset experiment state."""
    ExperimentState().reset(budget_cap, max_generations)

def increment_samples(count: int = 1, is_perturbed: bool = False) -> bool:
    """Increment sample count (original or perturbed)."""
    state = ExperimentState()
    if is_perturbed:
        return state.increment_perturbed(count)
    return state.increment_original(count)

def increment_generations(count: int = 1) -> bool:
    """Increment generation count."""
    return ExperimentState().increment_generation(count)

def get_remaining() -> Dict[str, int]:
    """Get remaining budget and generation counts."""
    state = ExperimentState()
    return {
        "samples": state.get_remaining_budget(),
        "generations": state.get_remaining_generations()
    }

def is_exhausted() -> bool:
    """Check if either budget or generation limit is exhausted."""
    state = ExperimentState()
    return state.is_budget_exceeded() or state.is_generation_limit_reached()

def main():
    """CLI entry point for state management testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Experiment state management CLI")
    parser.add_argument("--reset", action="store_true", help="Reset state")
    parser.add_argument("--budget", type=int, help="Set budget cap")
    parser.add_argument("--generations", type=int, help="Set max generations")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--sample", type=int, default=1, help="Add sample count")
    parser.add_argument("--perturbed", action="store_true", help="Mark as perturbed sample")
    parser.add_argument("--generation", type=int, default=1, help="Add generation count")

    args = parser.parse_args()

    if args.reset:
        reset_state(args.budget, args.generations)
        print("State reset complete.")
    elif args.status:
        state = get_state()
        print(json.dumps(state, indent=2))
    elif args.sample > 0:
        result = increment_samples(args.sample, args.perturbed)
        if result:
            print(f"Added {args.sample} sample(s). Remaining: {get_remaining()['samples']}")
        else:
            print("Budget exceeded!")
    elif args.generation > 0:
        result = increment_generations(args.generation)
        if result:
            print(f"Added {args.generation} generation(s). Remaining: {get_remaining()['generations']}")
        else:
            print("Generation limit reached!")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()