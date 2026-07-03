"""Metric validation utilities for social memory network experiments.

This module provides validation logic to ensure computed metrics meet
quality thresholds and experiment-level requirements.
"""
from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from .specialization import validate_specialization_index
from .retrieval import validate_retrieval_efficiency

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single game's metrics."""
    game_id: int
    passed: bool
    specialization_valid: bool
    retrieval_valid: bool
    specialization_value: Optional[float] = None
    retrieval_value: Optional[float] = None
    errors: List[str] = field(default_factory=list)


@dataclass
class GameMetricRecord:
    """Record of metrics for a single game, used for experiment-level validation."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int
    passed_validation: bool = True
    errors: List[str] = field(default_factory=list)


def validate_single_game_metrics(
    game_id: int,
    specialization_index: float,
    retrieval_efficiency: float
) -> ValidationResult:
    """Validate metrics for a single game.

    Args:
        game_id: Unique identifier for the game.
        specialization_index: Computed specialization index value.
        retrieval_efficiency: Computed retrieval efficiency value.

    Returns:
        ValidationResult with validation status and any errors.
    """
    errors = []
    spec_valid = True
    ret_valid = True

    # Validate specialization index
    spec_result = validate_specialization_index(specialization_index)
    if not spec_result[0]:
        spec_valid = False
        errors.extend(spec_result[1])

    # Validate retrieval efficiency
    ret_result = validate_retrieval_efficiency(retrieval_efficiency)
    if not ret_result[0]:
        ret_valid = False
        errors.extend(ret_result[1])

    passed = spec_valid and ret_valid

    return ValidationResult(
        game_id=game_id,
        passed=passed,
        specialization_valid=spec_valid,
        retrieval_valid=ret_valid,
        specialization_value=specialization_index,
        retrieval_value=retrieval_efficiency,
        errors=errors
    )


def validate_and_filter_records(
    records: List[GameMetricRecord],
    min_pass_rate: float = 0.95
) -> Tuple[List[GameMetricRecord], float, ValidationResult]:
    """Filter records and validate experiment-level pass rate.

    This function implements the SC-001 requirement: at least 95% of games
    must produce valid metrics.

    Args:
        records: List of game metric records to validate.
        min_pass_rate: Minimum required pass rate (default 0.95 for 95%).

    Returns:
        Tuple of:
            - List of records that passed validation
            - Actual pass rate (fraction of valid records)
            - ValidationResult summarizing experiment-level validation
    """
    if not records:
        return [], 0.0, ValidationResult(
            game_id=-1,
            passed=False,
            specialization_valid=False,
            retrieval_valid=False,
            errors=["No records provided for validation"]
        )

    valid_records = []
    invalid_count = 0
    all_errors: List[str] = []

    for record in records:
        validation = validate_single_game_metrics(
            record.game_id,
            record.specialization_index,
            record.retrieval_efficiency
        )

        if validation.passed:
            valid_records.append(record)
            record.passed_validation = True
        else:
            invalid_count += 1
            record.passed_validation = False
            all_errors.extend([f"Game {record.game_id}: {e}" for e in validation.errors])

    total = len(records)
    pass_rate = (total - invalid_count) / total if total > 0 else 0.0

    # Check against SC-001 requirement (≥95% pass rate)
    threshold_met = pass_rate >= min_pass_rate

    if not threshold_met:
        logger.warning(
            f"Experiment validation FAILED: pass rate {pass_rate:.2%} "
            f"below required {min_pass_rate:.2%}. {invalid_count}/{total} games invalid."
        )
        if all_errors:
            logger.warning(f"Validation errors: {all_errors[:5]}...")  # Log first 5
    else:
        logger.info(
            f"Experiment validation PASSED: pass rate {pass_rate:.2%} "
            f"meets required {min_pass_rate:.2%} threshold."
        )

    return valid_records, pass_rate, ValidationResult(
        game_id=-1,
        passed=threshold_met,
        specialization_valid=True,  # Aggregate check
        retrieval_valid=True,
        errors=all_errors if not threshold_met else []
    )


def compute_metric_statistics(
    records: List[GameMetricRecord],
    filter_invalid: bool = True
) -> Dict[str, Dict[str, float]]:
    """Compute descriptive statistics for metrics.

    Args:
        records: List of game metric records.
        filter_invalid: If True, only include records that passed validation.

    Returns:
        Dictionary with statistics for each metric type.
    """
    data = records if not filter_invalid else [r for r in records if r.passed_validation]

    if not data:
        return {
            "specialization_index": {},
            "retrieval_efficiency": {}
        }

    spec_values = [r.specialization_index for r in data]
    ret_values = [r.retrieval_efficiency for r in data]

    return {
        "specialization_index": {
            "mean": float(np.mean(spec_values)),
            "std": float(np.std(spec_values)),
            "min": float(np.min(spec_values)),
            "max": float(np.max(spec_values)),
            "count": len(spec_values)
        },
        "retrieval_efficiency": {
            "mean": float(np.mean(ret_values)),
            "std": float(np.std(ret_values)),
            "min": float(np.min(ret_values)),
            "max": float(np.max(ret_values)),
            "count": len(ret_values)
        }
    }


def validate_experiment_metrics(
    records: List[GameMetricRecord],
    min_pass_rate: float = 0.95,
    raise_on_failure: bool = False
) -> Tuple[List[GameMetricRecord], ValidationResult]:
    """Validate an entire experiment's metrics against SC-001.

    This is the primary entry point for experiment-level validation.
    It enforces the requirement that ≥95% of games must produce valid metrics.

    Args:
        records: List of all game metric records from the experiment.
        min_pass_rate: Minimum required pass rate (default 0.95 for 95%).
        raise_on_failure: If True, raise ValueError when pass rate is insufficient.

    Returns:
        Tuple of:
            - List of valid records (all records if raise_on_failure is False)
            - ValidationResult with experiment-level status

    Raises:
        ValueError: If raise_on_failure is True and pass rate < min_pass_rate.
    """
    valid_records, pass_rate, result = validate_and_filter_records(
        records, min_pass_rate
    )

    if raise_on_failure and not result.passed:
        raise ValueError(
            f"SC-001 validation failed: pass rate {pass_rate:.2%} "
            f"below required {min_pass_rate:.2%}. {len(result.errors)} errors found."
        )

    return valid_records, result