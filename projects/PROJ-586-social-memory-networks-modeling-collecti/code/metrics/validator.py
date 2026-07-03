"""Metric validation utilities for social memory network experiments.

Implements validation logic to ensure:
- ≥95% of games produce valid metrics (SC-001)
- Metrics are within expected ranges
- Statistical summaries of metric distributions
"""
from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from metrics.specialization import SpecializationMetrics, compute_specialization_index
from metrics.retrieval import RetrievalMetrics, compute_retrieval_efficiency

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single game's metrics."""
    game_id: str
    specialization_valid: bool
    retrieval_valid: bool
    specialization_index: Optional[float] = None
    retrieval_efficiency: Optional[float] = None
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.specialization_valid and self.retrieval_valid


@dataclass
class GameMetricRecord:
    """Record of metrics for a single game, used for experiment-level validation."""
    game_id: str
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    is_valid: bool
    errors: List[str] = field(default_factory=list)


def validate_single_game_metrics(
    game_id: str,
    specialization_metrics: Optional[SpecializationMetrics],
    retrieval_metrics: Optional[RetrievalMetrics],
    agent_count: int
) -> ValidationResult:
    """Validate metrics for a single game.

    Args:
        game_id: Unique identifier for the game
        specialization_metrics: Computed specialization metrics (or None)
        retrieval_metrics: Computed retrieval metrics (or None)
        agent_count: Number of agents in the game

    Returns:
        ValidationResult with validation status and any errors
    """
    errors = []
    spec_valid = False
    ret_valid = False
    spec_idx = None
    ret_eff = None

    # Validate specialization metrics
    if specialization_metrics is None:
        errors.append("Specialization metrics are None")
    else:
        try:
            spec_idx = specialization_metrics.specialization_index
            if spec_idx is None:
                errors.append("Specialization index is None")
            elif not (0.0 <= spec_idx <= 1.0):
                errors.append(f"Specialization index {spec_idx} out of range [0, 1]")
            else:
                spec_valid = True
        except Exception as e:
            errors.append(f"Specialization metric validation error: {str(e)}")

    # Validate retrieval metrics
    if retrieval_metrics is None:
        errors.append("Retrieval metrics are None")
    else:
        try:
            ret_eff = retrieval_metrics.efficiency
            if ret_eff is None:
                errors.append("Retrieval efficiency is None")
            elif not (0.0 <= ret_eff <= 1.0):
                errors.append(f"Retrieval efficiency {ret_eff} out of range [0, 1]")
            else:
                ret_valid = True
        except Exception as e:
            errors.append(f"Retrieval metric validation error: {str(e)}")

    return ValidationResult(
        game_id=game_id,
        specialization_valid=spec_valid,
        retrieval_valid=ret_valid,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff,
        errors=errors
    )


def validate_and_filter_records(
    records: List[GameMetricRecord],
    min_success_rate: float = 0.95
) -> Tuple[List[GameMetricRecord], ValidationResult]:
    """Validate a batch of game records and check success rate.

    Args:
        records: List of game metric records to validate
        min_success_rate: Minimum required success rate (default 0.95 for SC-001)

    Returns:
        Tuple of (valid_records, validation_summary)
    """
    valid_records = [r for r in records if r.is_valid]
    total_count = len(records)
    valid_count = len(valid_records)

    if total_count == 0:
        success_rate = 0.0
    else:
        success_rate = valid_count / total_count

    # Check against SC-001 requirement
    sc001_passed = success_rate >= min_success_rate

    summary = ValidationResult(
        game_id="experiment_summary",
        specialization_valid=sc001_passed,
        retrieval_valid=sc001_passed,
        errors=[] if sc001_passed else [
            f"Success rate {success_rate:.2%} below threshold {min_success_rate:.2%}"
        ]
    )

    if not sc001_passed:
        logger.warning(
            f"SC-001 validation failed: {valid_count}/{total_count} "
            f"games produced valid metrics ({success_rate:.2%})"
        )
    else:
        logger.info(
            f"SC-001 validation passed: {valid_count}/{total_count} "
            f"games produced valid metrics ({success_rate:.2%})"
        )

    return valid_records, summary


def compute_metric_statistics(
    records: List[GameMetricRecord]
) -> Dict[str, Dict[str, float]]:
    """Compute descriptive statistics for metric distributions.

    Args:
        records: List of game metric records

    Returns:
        Dictionary with statistics for specialization and retrieval metrics
    """
    if not records:
        return {
            "specialization": {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
            "retrieval": {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        }

    spec_values = [r.specialization_index for r in records if r.is_valid]
    ret_values = [r.retrieval_efficiency for r in records if r.is_valid]

    def compute_stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        arr = np.array(values)
        return {
            "count": len(values),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr))
        }

    return {
        "specialization": compute_stats(spec_values),
        "retrieval": compute_stats(ret_values)
    }


def validate_experiment_metrics(
    records: List[GameMetricRecord],
    min_success_rate: float = 0.95
) -> Dict[str, Any]:
    """Perform comprehensive validation of an experiment's metrics.

    This function implements SC-001: at least 95% of games must produce valid metrics.

    Args:
        records: List of all game metric records from the experiment
        min_success_rate: Minimum required success rate (default 0.95)

    Returns:
        Dictionary containing:
        - success_rate: Overall validation success rate
        - sc001_passed: Boolean indicating if SC-001 requirement is met
        - valid_count: Number of valid records
        - total_count: Total number of records
        - statistics: Descriptive statistics for metrics
        - errors: List of validation errors if any
    """
    valid_records, summary = validate_and_filter_records(records, min_success_rate)

    total_count = len(records)
    valid_count = len(valid_records)
    success_rate = valid_count / total_count if total_count > 0 else 0.0

    stats = compute_metric_statistics(records)

    result = {
        "success_rate": success_rate,
        "sc001_passed": success_rate >= min_success_rate,
        "valid_count": valid_count,
        "total_count": total_count,
        "min_success_rate": min_success_rate,
        "statistics": stats,
        "errors": summary.errors
    }

    return result


def validate_game_result_for_metrics(
    game_id: str,
    agent_skills: List[int],
    retrieved_items: int,
    total_items: int,
    agent_count: int
) -> ValidationResult:
    """Convenience function to validate metrics computed from raw game data.

    Args:
        game_id: Unique game identifier
        agent_skills: List of skill assignments for each agent
        retrieved_items: Number of items successfully retrieved
        total_items: Total number of items to retrieve
        agent_count: Number of agents in the game

    Returns:
        ValidationResult with computed and validated metrics
    """
    # Compute specialization metrics
    try:
        spec_metrics, spec_idx = compute_specialization_index(
            agent_skills, num_agents=agent_count
        )
    except Exception as e:
        spec_metrics = None
        spec_idx = None
        logger.debug(f"Failed to compute specialization for game {game_id}: {e}")

    # Compute retrieval metrics
    try:
        ret_metrics, ret_eff = compute_retrieval_efficiency(
            retrieved_items, total_items, agent_count
        )
    except Exception as e:
        ret_metrics = None
        ret_eff = None
        logger.debug(f"Failed to compute retrieval for game {game_id}: {e}")

    return validate_single_game_metrics(
        game_id, spec_metrics, ret_metrics, agent_count
    )


def main() -> None:
    """Entry point for standalone validation testing."""
    # Example usage
    test_records = [
        GameMetricRecord(
            game_id=f"game_{i}",
            specialization_index=0.5 + (i % 10) * 0.05,
            retrieval_efficiency=0.7 + (i % 5) * 0.05,
            context_condition="full",
            agent_count=5,
            is_valid=True
        )
        for i in range(100)
    ]

    # Add some invalid records
    test_records[10].is_valid = False
    test_records[10].errors = ["Simulated validation failure"]
    test_records[50].is_valid = False
    test_records[50].errors = ["Simulated validation failure"]

    result = validate_experiment_metrics(test_records)

    print(f"Validation Result:")
    print(f"  Total games: {result['total_count']}")
    print(f"  Valid games: {result['valid_count']}")
    print(f"  Success rate: {result['success_rate']:.2%}")
    print(f"  SC-001 passed: {result['sc001_passed']}")
    print(f"  Errors: {result['errors']}")

    if result['sc001_passed']:
        print("\n✓ Experiment meets SC-001 requirement (≥95% valid metrics)")
    else:
        print(f"\n✗ Experiment FAILED SC-001 requirement (need ≥{result['min_success_rate']:.2%}, got {result['success_rate']:.2%})")


if __name__ == "__main__":
    main()