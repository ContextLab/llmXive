"""
Metric validation for social memory network experiments.

This module provides validation logic for specialization and retrieval
metrics to ensure they meet quality requirements (SC-001).
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from .specialization import validate_specialization_index
from .retrieval import validate_retrieval_efficiency

@dataclass
class ValidationResult:
    """Result of metric validation."""
    passed: bool
    valid_count: int
    total_count: int
    failure_reasons: List[str] = field(default_factory=list)

@dataclass
class GameMetricRecord:
    """Record of metrics for a single game."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int

def validate_specialization_range(
    specialization: float,
    num_agents: int
) -> bool:
    """
    Validate specialization index is in valid range.
    
    Args:
        specialization: Specialization index value
        num_agents: Number of agents
    
    Returns:
        True if specialization is valid
    """
    return validate_specialization_index(specialization, num_agents)

def validate_retrieval_range(
    efficiency: float
) -> bool:
    """
    Validate retrieval efficiency is in valid range.
    
    Args:
        efficiency: Retrieval efficiency value
    
    Returns:
        True if efficiency is valid
    """
    return validate_retrieval_efficiency(efficiency)

def validate_single_game_metrics(
    game_record: Dict[str, Any]
) -> ValidationResult:
    """
    Validate metrics for a single game.
    
    Args:
        game_record: Dictionary with game metrics
    
    Returns:
        ValidationResult indicating pass/fail
    """
    num_agents = game_record.get("agent_count", 3)
    specialization = game_record.get("specialization_index", 0.0)
    retrieval = game_record.get("retrieval_efficiency", 0.0)
    
    reasons = []
    
    if not validate_specialization_range(specialization, num_agents):
        reasons.append(f"Specialization {specialization} out of range for {num_agents} agents")
    
    if not validate_retrieval_range(retrieval):
        reasons.append(f"Retrieval efficiency {retrieval} out of valid range")
    
    passed = len(reasons) == 0
    
    return ValidationResult(
        passed=passed,
        valid_count=1 if passed else 0,
        total_count=1,
        failure_reasons=reasons
    )

def validate_experiment_metrics(
    game_records: List[Dict[str, Any]],
    min_valid_rate: float = 0.95
) -> ValidationResult:
    """
    Validate all metrics for an experiment (SC-001 requirement).
    
    Args:
        game_records: List of game metric records
        min_valid_rate: Minimum required validation rate (default 95%)
    
    Returns:
        ValidationResult with experiment-level validation
    """
    if not game_records:
        return ValidationResult(
            passed=False,
            valid_count=0,
            total_count=0,
            failure_reasons=["No game records to validate"]
        )
    
    valid_count = 0
    all_reasons = []
    
    for record in game_records:
        result = validate_single_game_metrics(record)
        if result.passed:
            valid_count += 1
        else:
            all_reasons.extend(result.failure_reasons)
    
    validation_rate = valid_count / len(game_records)
    passed = validation_rate >= min_valid_rate
    
    return ValidationResult(
        passed=passed,
        valid_count=valid_count,
        total_count=len(game_records),
        failure_reasons=all_reasons[:10]  # Limit reasons for readability
    )

def validate_and_filter_records(
    game_records: List[Dict[str, Any]],
    min_valid_rate: float = 0.95
) -> Tuple[List[Dict[str, Any]], ValidationResult]:
    """
    Validate and filter records, returning only valid ones.
    
    Args:
        game_records: List of game metric records
        min_valid_rate: Minimum required validation rate
    
    Returns:
        Tuple of (valid records, validation result)
    """
    valid_records = []
    valid_count = 0
    
    for record in game_records:
        result = validate_single_game_metrics(record)
        if result.passed:
            valid_records.append(record)
            valid_count += 1
    
    validation_result = validate_experiment_metrics(game_records, min_valid_rate)
    
    return valid_records, validation_result

def compute_metric_statistics(
    game_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute statistics for metrics across all games.
    
    Args:
        game_records: List of game metric records
    
    Returns:
        Dictionary with metric statistics
    """
    if not game_records:
        return {}
    
    specializations = [r.get("specialization_index", 0.0) for r in game_records]
    retrievals = [r.get("retrieval_efficiency", 0.0) for r in game_records]
    
    return {
        "specialization": {
            "mean": float(np.mean(specializations)),
            "std": float(np.std(specializations)),
            "min": float(np.min(specializations)),
            "max": float(np.max(specializations))
        },
        "retrieval": {
            "mean": float(np.mean(retrievals)),
            "std": float(np.std(retrievals)),
            "min": float(np.min(retrievals)),
            "max": float(np.max(retrievals))
        },
        "total_games": len(game_records)
    }

def validate_batch_metrics(
    batch_records: List[List[Dict[str, Any]]],
    min_valid_rate: float = 0.95
) -> List[ValidationResult]:
    """
    Validate metrics for multiple batches of games.
    
    Args:
        batch_records: List of batch record lists
        min_valid_rate: Minimum required validation rate
    
    Returns:
        List of ValidationResult for each batch
    """
    results = []
    for batch in batch_records:
        result = validate_experiment_metrics(batch, min_valid_rate)
        results.append(result)
    return results

if __name__ == "__main__":
    # Test validation
    test_records = [
        {"game_id": 0, "specialization_index": 0.5, "retrieval_efficiency": 1.2, "agent_count": 3},
        {"game_id": 1, "specialization_index": 1.0, "retrieval_efficiency": 1.5, "agent_count": 3},
    ]
    
    result = validate_experiment_metrics(test_records)
    print(f"Validation passed: {result.passed}")
    print(f"Valid: {result.valid_count}/{result.total_count}")
