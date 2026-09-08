"""
Parity Checker Module for Co-Evolving Policy Distillation.

This module enforces strict parity in rule evaluations across different
training conditions (Sequential, Mixed-task, Co-evolving) as required by
SC-002. It provides mechanisms to cap evaluations during generation,
track evaluation counts, and verify parity across runs.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


class ParityError(Exception):
    """Exception raised when parity constraints are violated."""
    pass


@dataclass
class EvaluationStats:
    """
    Statistics for rule evaluations in a single training run.

    Attributes:
        total_evaluations: Total number of rule evaluations performed.
        task_evaluations: Dict mapping task_id to evaluation count for that task.
        checksum: SHA-256 hash of the evaluation distribution for integrity.
        condition: The training condition name (e.g., 'sequential', 'mixed', 'coevolving').
        seed: Random seed used for this run.
    """
    total_evaluations: int
    task_evaluations: Dict[str, int]
    checksum: str
    condition: str
    seed: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationStats':
        """Create from dictionary."""
        return cls(**data)


class ParityChecker:
    """
    Enforces hard integer caps on rule evaluations and verifies parity.

    This class is used during the generation loop to ensure that:
    1. No run exceeds the configured maximum evaluation budget.
    2. The total evaluations match exactly across all three conditions.
    3. The distribution of evaluations across tasks is consistent.
    """

    def __init__(self, max_evaluations: int, expected_tasks: List[str]):
        """
        Initialize the parity checker.

        Args:
            max_evaluations: The hard cap on total rule evaluations per run.
            expected_tasks: List of task IDs that should be evaluated.
        """
        self.max_evaluations = max_evaluations
        self.expected_tasks = set(expected_tasks)
        self.current_count = 0
        self.task_counts: Dict[str, int] = {task: 0 for task in expected_tasks}
        self._evaluation_log: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Reset the counter for a new run."""
        self.current_count = 0
        self.task_counts = {task: 0 for task in self.expected_tasks}
        self._evaluation_log = []

    def record_evaluation(self, task_id: str, count: int = 1) -> None:
        """
        Record rule evaluations for a specific task.

        Args:
            task_id: The identifier of the task being evaluated.
            count: Number of evaluations to record (default 1).

        Raises:
            ParityError: If recording this evaluation would exceed the cap.
        """
        if task_id not in self.expected_tasks:
            raise ParityError(f"Unknown task_id: {task_id}. Expected one of {self.expected_tasks}")

        if self.current_count + count > self.max_evaluations:
            raise ParityError(
                f"Evaluation cap exceeded: current={self.current_count}, "
                f"adding={count}, max={self.max_evaluations}"
            )

        self.current_count += count
        self.task_counts[task_id] += count
        self._evaluation_log.append({
            "task_id": task_id,
            "count": count,
            "total_so_far": self.current_count
        })

    def clamp_to_cap(self, task_id: str, requested_count: int) -> int:
        """
        Clamp the requested evaluation count to the remaining budget.

        This enforces the hard cap during the generation loop.

        Args:
            task_id: The task being evaluated.
            requested_count: The number of evaluations requested.

        Returns:
            The actual number of evaluations that can be performed.

        Raises:
            ParityError: If the task_id is invalid.
        """
        if task_id not in self.expected_tasks:
            raise ParityError(f"Unknown task_id: {task_id}")

        remaining = self.max_evaluations - self.current_count
        if remaining <= 0:
            return 0

        actual_count = min(requested_count, remaining)
        self.record_evaluation(task_id, actual_count)
        return actual_count

    def get_stats(self, condition: str, seed: int) -> EvaluationStats:
        """
        Generate statistics for the current run.

        Args:
            condition: The training condition name.
            seed: The random seed used.

        Returns:
            An EvaluationStats object with the run's metrics.
        """
        # Create a canonical representation for checksumming
        canonical_data = {
            "total": self.current_count,
            "tasks": {k: v for k, v in sorted(self.task_counts.items())}
        }
        json_str = json.dumps(canonical_data, sort_keys=True)
        checksum = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

        return EvaluationStats(
            total_evaluations=self.current_count,
            task_evaluations=dict(self.task_counts),
            checksum=checksum,
            condition=condition,
            seed=seed
        )

    def verify_exact_parity(self, stats_list: List[EvaluationStats]) -> None:
        """
        Verify that all provided stats have identical total evaluations.

        Args:
            stats_list: List of EvaluationStats from different conditions.

        Raises:
            ParityError: If totals do not match exactly.
        """
        if len(stats_list) < 2:
            return  # Nothing to compare

        target_total = stats_list[0].total_evaluations
        target_checksum = stats_list[0].checksum

        for stats in stats_list[1:]:
            if stats.total_evaluations != target_total:
                raise ParityError(
                    f"Parity mismatch: {stats.condition} has {stats.total_evaluations} "
                    f"evaluations, expected {target_total}"
                )
            if stats.checksum != target_checksum:
                raise ParityError(
                    f"Checksum mismatch: {stats.condition} has checksum "
                    f"{stats.checksum}, expected {target_checksum}"
                )


def verify_run_parity(
    results_dir: Path,
    conditions: List[str],
    max_evaluations: int
) -> Dict[str, Any]:
    """
    Load results from multiple conditions and verify evaluation parity.

    This function reads the evaluation statistics from result files generated
    by the training loop and ensures they meet the SC-002 requirement of
    exact parity across conditions.

    Args:
        results_dir: Directory containing result JSON files.
        conditions: List of condition names to check (e.g., ['sequential', 'mixed', 'coevolving']).
        max_evaluations: The expected total evaluation count per run.

    Returns:
        A dictionary with verification results and statistics.

    Raises:
        ParityError: If parity cannot be verified.
    """
    stats_by_condition = {}

    for condition in conditions:
        result_file = results_dir / f"{condition}_results.json"
        if not result_file.exists():
            raise ParityError(f"Result file missing for {condition}: {result_file}")

        with open(result_file, 'r') as f:
            data = json.load(f)

        # Extract evaluation stats from the result file
        # Expected structure: {"stats": {"total_evaluations": ..., "task_evaluations": ...}}
        if "stats" not in data:
            raise ParityError(f"Missing 'stats' in {result_file}")

        stats_data = data["stats"]
        stats = EvaluationStats(
            total_evaluations=stats_data.get("total_evaluations", 0),
            task_evaluations=stats_data.get("task_evaluations", {}),
            checksum=stats_data.get("checksum", ""),
            condition=condition,
            seed=stats_data.get("seed", 0)
        )

        if stats.total_evaluations != max_evaluations:
            raise ParityError(
                f"Condition {condition} has {stats.total_evaluations} evaluations, "
                f"expected {max_evaluations}"
            )

        stats_by_condition[condition] = stats

    # Verify exact parity across all conditions
    checker = ParityChecker(max_evaluations, [])
    checker.verify_exact_parity(list(stats_by_condition.values()))

    return {
        "verified": True,
        "conditions": conditions,
        "max_evaluations": max_evaluations,
        "stats": {cond: stats.to_dict() for cond, stats in stats_by_condition.items()}
    }