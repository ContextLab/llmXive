"""
Parity checker utility for enforcing rule-evaluation budget constraints.

This module provides functionality to track and enforce strict parity of total
rule evaluations across different training conditions (Sequential, Mixed, Co-evolving).
It ensures that no condition exceeds the allocated budget, preventing wasted compute.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


class ParityError(Exception):
    """Raised when a rule evaluation count exceeds the allocated budget."""
    pass


@dataclass
class EvaluationStats:
    """Statistics tracking for rule evaluations."""
    total_evaluations: int = 0
    budget: int = 0
    condition: str = ""
    current_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationStats':
        """Create instance from dictionary."""
        return cls(**data)


class ParityChecker:
    """
    Utility class for checking and enforcing evaluation parity across training runs.

    This checker ensures that the total number of rule evaluations does not exceed
    the allocated budget during training. It is designed to be called at every
    generation step in the training loop to fail fast if the budget is exceeded.
    """

    def __init__(self, budget: int, condition: str):
        """
        Initialize the parity checker.

        Args:
            budget: Maximum allowed number of rule evaluations.
            condition: Name of the training condition (e.g., 'sequential', 'mixed', 'coevolving').
        """
        if budget <= 0:
            raise ValueError("Budget must be a positive integer")
        self.budget = budget
        self.condition = condition
        self.current_count = 0
        self.history: List[Dict[str, Any]] = []

    def check_and_enforce(self, increment: int = 1) -> None:
        """
        Check if the current count plus increment exceeds the budget.

        Args:
            increment: Number of evaluations to add (default 1).

        Raises:
            ParityError: If the count would exceed the budget.
        """
        if increment < 0:
            raise ValueError("Increment must be non-negative")

        new_count = self.current_count + increment

        if new_count > self.budget:
            raise ParityError(
                f"Parity violation: {self.condition} condition would exceed budget. "
                f"Current: {self.current_count}, Increment: {increment}, "
                f"Budget: {self.budget}, Projected: {new_count}"
            )

        self.current_count = new_count
        self.history.append({
            'count': self.current_count,
            'increment': increment,
            'remaining': self.budget - self.current_count
        })

    def get_remaining(self) -> int:
        """Get the remaining budget."""
        return self.budget - self.current_count

    def is_exhausted(self) -> bool:
        """Check if the budget is fully exhausted."""
        return self.current_count >= self.budget

    def get_stats(self) -> EvaluationStats:
        """Get current evaluation statistics."""
        return EvaluationStats(
            total_evaluations=self.current_count,
            budget=self.budget,
            condition=self.condition,
            current_count=self.current_count
        )

    def save_history(self, output_path: Path) -> None:
        """
        Save the evaluation history to a JSON file.

        Args:
            output_path: Path to save the history file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({
                'condition': self.condition,
                'budget': self.budget,
                'final_count': self.current_count,
                'history': self.history
            }, f, indent=2)


def check_and_enforce_parity(budget: int, current_count: int, condition: str = "unknown") -> int:
    """
    Standalone function to check and enforce parity constraints.

    This function is designed to be called during the training loop to ensure
    the hard integer cap is not exceeded in real-time.

    Args:
        budget: Maximum allowed number of rule evaluations.
        current_count: Current count of rule evaluations.
        condition: Name of the training condition for error reporting.

    Returns:
        The updated count (same as input if no increment).

    Raises:
        ParityError: If the current count exceeds the budget.
    """
    if current_count > budget:
        raise ParityError(
            f"Parity violation: {condition} condition has exceeded budget. "
            f"Current: {current_count}, Budget: {budget}"
        )
    return current_count


def verify_run_parity(
    results_dir: Path,
    expected_budget: int,
    conditions: List[str]
) -> Dict[str, Any]:
    """
    Verify that multiple training runs have achieved parity in rule evaluations.

    Args:
        results_dir: Directory containing parity history files.
        expected_budget: The expected budget that all runs should match.
        conditions: List of condition names to verify.

    Returns:
        Dictionary with verification results for each condition.

    Raises:
        ParityError: If any condition does not match the expected budget.
    """
    results = {}
    all_parity = True

    for condition in conditions:
        history_file = results_dir / f"parity_history_{condition}.json"
        if not history_file.exists():
            results[condition] = {
                'verified': False,
                'error': 'History file not found'
            }
            all_parity = False
            continue

        with open(history_file, 'r') as f:
            data = json.load(f)

        actual_count = data.get('final_count', 0)
        actual_budget = data.get('budget', 0)

        if actual_count != expected_budget:
            results[condition] = {
                'verified': False,
                'actual_count': actual_count,
                'expected_count': expected_budget,
                'error': 'Count mismatch'
            }
            all_parity = False
        elif actual_budget != expected_budget:
            results[condition] = {
                'verified': False,
                'actual_budget': actual_budget,
                'expected_budget': expected_budget,
                'error': 'Budget mismatch'
            }
            all_parity = False
        else:
            results[condition] = {
                'verified': True,
                'count': actual_count,
                'budget': actual_budget
            }

    if not all_parity:
        raise ParityError("Parity verification failed for one or more conditions")

    return results


def main() -> None:
    """
    Main entry point for parity checker CLI.

    This function provides a simple CLI for testing the parity checker functionality.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Parity Checker Utility')
    parser.add_argument('--budget', type=int, required=True, help='Evaluation budget')
    parser.add_argument('--condition', type=str, default='test', help='Condition name')
    parser.add_argument('--steps', type=int, default=10, help='Number of steps to simulate')
    parser.add_argument('--output', type=str, default=None, help='Output file for history')

    args = parser.parse_args()

    checker = ParityChecker(budget=args.budget, condition=args.condition)

    try:
        for i in range(args.steps):
            checker.check_and_enforce(increment=1)
            print(f"Step {i+1}: Count = {checker.current_count}, Remaining = {checker.get_remaining()}")

        if args.output:
            checker.save_history(Path(args.output))
            print(f"History saved to {args.output}")

        print(f"\nFinal: {checker.get_stats().to_dict()}")

    except ParityError as e:
        print(f"Parity Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import sys
    main()
