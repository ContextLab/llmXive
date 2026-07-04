"""
Metric validation logic for social memory network experiments.

Implements SC-001: At least 95% of simulated games must produce valid metrics.
Provides validation for single-game metrics and experiment-wide aggregation.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from metrics.specialization import SpecializationMetrics, compute_specialization_index
from metrics.retrieval import RetrievalMetrics, compute_retrieval_efficiency

logger = logging.getLogger(__name__)


@dataclass
class GameMetricRecord:
    """Record of metrics for a single game."""
    game_id: str
    context_condition: str
    agent_count: int
    specialization_index: float
    retrieval_efficiency: float
    is_valid: bool = True
    error_reason: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating a set of game metrics."""
    total_games: int
    valid_games: int
    invalid_games: int
    valid_percentage: float
    passes_threshold: bool
    threshold: float = 0.95
    statistics: Dict[str, Any] = field(default_factory=dict)
    invalid_reasons: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


def validate_single_game_metrics(
    specialization_metrics: Optional[SpecializationMetrics],
    retrieval_metrics: Optional[RetrievalMetrics],
    game_id: str,
    context_condition: str,
    agent_count: int
) -> GameMetricRecord:
    """
    Validate metrics for a single game.

    Args:
        specialization_metrics: Computed specialization metrics or None
        retrieval_metrics: Computed retrieval metrics or None
        game_id: Unique identifier for the game
        context_condition: Context condition (e.g., 'full', 'limited')
        agent_count: Number of agents in the game

    Returns:
        GameMetricRecord with validation status and computed values
    """
    # Check if either metric computation failed
    if specialization_metrics is None and retrieval_metrics is None:
        return GameMetricRecord(
            game_id=game_id,
            context_condition=context_condition,
            agent_count=agent_count,
            specialization_index=float('nan'),
            retrieval_efficiency=float('nan'),
            is_valid=False,
            error_reason="Both specialization and retrieval metrics failed to compute"
        )

    # Extract specialization index
    spec_idx = float('nan')
    if specialization_metrics is not None:
        try:
            spec_idx = float(specialization_metrics.specialization_index)
            if not np.isfinite(spec_idx):
                raise ValueError("Non-finite specialization index")
        except (AttributeError, TypeError, ValueError) as e:
            logger.warning(f"Game {game_id}: Invalid specialization index: {e}")
            spec_idx = float('nan')
    else:
        logger.warning(f"Game {game_id}: No specialization metrics provided")

    # Extract retrieval efficiency
    ret_eff = float('nan')
    if retrieval_metrics is not None:
        try:
            ret_eff = float(retrieval_metrics.efficiency)
            if not np.isfinite(ret_eff):
                raise ValueError("Non-finite retrieval efficiency")
        except (AttributeError, TypeError, ValueError) as e:
            logger.warning(f"Game {game_id}: Invalid retrieval efficiency: {e}")
            ret_eff = float('nan')
    else:
        logger.warning(f"Game {game_id}: No retrieval metrics provided")

    # Determine validity: at least one metric must be valid and finite
    is_valid = np.isfinite(spec_idx) or np.isfinite(ret_eff)

    error_reason = None
    if not is_valid:
        reasons = []
        if not np.isfinite(spec_idx):
            reasons.append("invalid_specialization")
        if not np.isfinite(ret_eff):
            reasons.append("invalid_retrieval")
        error_reason = "; ".join(reasons)

    return GameMetricRecord(
        game_id=game_id,
        context_condition=context_condition,
        agent_count=agent_count,
        specialization_index=spec_idx,
        retrieval_efficiency=ret_eff,
        is_valid=is_valid,
        error_reason=error_reason
    )


def validate_and_filter_records(
    records: List[GameMetricRecord],
    threshold: float = 0.95
) -> ValidationResult:
    """
    Validate a batch of game metric records and compute aggregate statistics.

    Args:
        records: List of GameMetricRecord objects
        threshold: Minimum percentage of valid games required (default 0.95)

    Returns:
        ValidationResult with aggregate statistics and pass/fail status
    """
    total_games = len(records)
    if total_games == 0:
        return ValidationResult(
            total_games=0,
            valid_games=0,
            invalid_games=0,
            valid_percentage=0.0,
            passes_threshold=False,
            threshold=threshold,
            statistics={},
            invalid_reasons={}
        )

    valid_games = sum(1 for r in records if r.is_valid)
    invalid_games = total_games - valid_games
    valid_percentage = valid_games / total_games

    # Count invalid reasons
    invalid_reasons: Dict[str, int] = defaultdict(int)
    for r in records:
        if not r.is_valid and r.error_reason:
            invalid_reasons[r.error_reason] += 1

    # Compute statistics for valid games only
    valid_records = [r for r in records if r.is_valid]
    statistics: Dict[str, Any] = {}

    if valid_records:
        spec_indices = [r.specialization_index for r in valid_records if np.isfinite(r.specialization_index)]
        ret_efficiencies = [r.retrieval_efficiency for r in valid_records if np.isfinite(r.retrieval_efficiency)]

        if spec_indices:
            statistics['specialization'] = {
                'mean': float(np.mean(spec_indices)),
                'std': float(np.std(spec_indices)),
                'min': float(np.min(spec_indices)),
                'max': float(np.max(spec_indices)),
                'count': len(spec_indices)
            }

        if ret_efficiencies:
            statistics['retrieval'] = {
                'mean': float(np.mean(ret_efficiencies)),
                'std': float(np.std(ret_efficiencies)),
                'min': float(np.min(ret_efficiencies)),
                'max': float(np.max(ret_efficiencies)),
                'count': len(ret_efficiencies)
            }

    passes_threshold = valid_percentage >= threshold

    return ValidationResult(
        total_games=total_games,
        valid_games=valid_games,
        invalid_games=invalid_games,
        valid_percentage=valid_percentage,
        passes_threshold=passes_threshold,
        threshold=threshold,
        statistics=statistics,
        invalid_reasons=dict(invalid_reasons)
    )


def compute_metric_statistics(
    records: List[GameMetricRecord]
) -> Dict[str, Any]:
    """
    Compute descriptive statistics for valid metrics.

    Args:
        records: List of GameMetricRecord objects

    Returns:
        Dictionary with mean, std, min, max for each valid metric
    """
    valid_records = [r for r in records if r.is_valid]

    statistics: Dict[str, Any] = {}

    if not valid_records:
        return statistics

    spec_indices = [r.specialization_index for r in valid_records if np.isfinite(r.specialization_index)]
    ret_efficiencies = [r.retrieval_efficiency for r in valid_records if np.isfinite(r.retrieval_efficiency)]

    if spec_indices:
        statistics['specialization_index'] = {
            'mean': float(np.mean(spec_indices)),
            'std': float(np.std(spec_indices)),
            'min': float(np.min(spec_indices)),
            'max': float(np.max(spec_indices)),
            'count': len(spec_indices)
        }

    if ret_efficiencies:
        statistics['retrieval_efficiency'] = {
            'mean': float(np.mean(ret_efficiencies)),
            'std': float(np.std(ret_efficiencies)),
            'min': float(np.min(ret_efficiencies)),
            'max': float(np.max(ret_efficiencies)),
            'count': len(ret_efficiencies)
        }

    return statistics


def validate_experiment_metrics(
    records: List[GameMetricRecord],
    threshold: float = 0.95
) -> Tuple[bool, ValidationResult]:
    """
    Validate experiment-wide metrics against the SC-001 requirement.

    SC-001: At least 95% of games must produce valid metrics.

    Args:
        records: List of GameMetricRecord objects from the experiment
        threshold: Minimum percentage of valid games required (default 0.95)

    Returns:
        Tuple of (passes_threshold, ValidationResult)
    """
    result = validate_and_filter_records(records, threshold)
    return result.passes_threshold, result


def validate_game_result_for_metrics(
    game_result: Dict[str, Any],
    context_condition: str,
    agent_count: int,
    game_id: str
) -> Tuple[Optional[SpecializationMetrics], Optional[RetrievalMetrics], GameMetricRecord]:
    """
    Compute and validate metrics from a raw game result dictionary.

    Args:
        game_result: Dictionary containing game results with 'agent_skills',
                    'retrieved_items', 'total_items', etc.
        context_condition: Context condition string
        agent_count: Number of agents
        game_id: Unique game identifier

    Returns:
        Tuple of (specialization_metrics, retrieval_metrics, validation_record)
    """
    spec_metrics = None
    ret_metrics = None

    try:
        # Compute specialization metrics
        agent_skills = game_result.get('agent_skills', [])
        if agent_skills:
            spec_metrics, _ = compute_specialization_index(agent_skills, num_agents=agent_count)
    except Exception as e:
        logger.warning(f"Game {game_id}: Specialization computation failed: {e}")
        spec_metrics = None

    try:
        # Compute retrieval metrics
        retrieved = game_result.get('retrieved_items', 0)
        total = game_result.get('total_items', 0)
        if total > 0:
            ret_metrics, _ = compute_retrieval_efficiency(retrieved, total, agent_count)
    except Exception as e:
        logger.warning(f"Game {game_id}: Retrieval computation failed: {e}")
        ret_metrics = None

    # Validate the computed metrics
    record = validate_single_game_metrics(
        spec_metrics,
        ret_metrics,
        game_id,
        context_condition,
        agent_count
    )

    return spec_metrics, ret_metrics, record


def main() -> None:
    """
    Main entry point for standalone validation testing.
    Demonstrates validation logic with synthetic test data.
    """
    # Create test records
    test_records: List[GameMetricRecord] = []

    # Simulate 100 games with 97% success rate
    for i in range(100):
        is_valid = i < 97
        test_records.append(GameMetricRecord(
            game_id=f"game_{i:03d}",
            context_condition="full",
            agent_count=5,
            specialization_index=0.85 if is_valid else float('nan'),
            retrieval_efficiency=0.92 if is_valid else float('nan'),
            is_valid=is_valid,
            error_reason="simulated_failure" if not is_valid else None
        ))

    # Validate
    passes, result = validate_experiment_metrics(test_records, threshold=0.95)

    print(f"Total games: {result.total_games}")
    print(f"Valid games: {result.valid_games}")
    print(f"Invalid games: {result.invalid_games}")
    print(f"Valid percentage: {result.valid_percentage:.2%}")
    print(f"Threshold: {result.threshold:.2%}")
    print(f"Passes SC-001: {passes}")

    if result.statistics:
        print("\nStatistics:")
        for metric_name, stats in result.statistics.items():
            print(f"  {metric_name}: mean={stats['mean']:.4f}, std={stats['std']:.4f}")

    if result.invalid_reasons:
        print("\nInvalid reasons:")
        for reason, count in result.invalid_reasons.items():
            print(f"  {reason}: {count}")


if __name__ == "__main__":
    main()