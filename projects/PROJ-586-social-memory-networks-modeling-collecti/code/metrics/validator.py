"""
Validation utilities for experiment metrics.
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
    is_valid: bool
    validation_rate: float
    total_records: int
    valid_records: int
    invalid_reasons: Dict[str, int] = field(default_factory=dict)

@dataclass
class GameMetricRecord:
    """Record of metrics for a single game."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    is_valid: bool

def validate_specialization_range(
    specialization_index: float
) -> bool:
    """
    Validate that specialization index is in valid range.
    
    Args:
        specialization_index: Computed specialization index
    
    Returns:
        True if valid
    """
    return validate_specialization_index(specialization_index)

def validate_retrieval_range(
    retrieval_efficiency: float
) -> bool:
    """
    Validate that retrieval efficiency is in valid range.
    
    Args:
        retrieval_efficiency: Computed retrieval efficiency
    
    Returns:
        True if valid
    """
    return validate_retrieval_efficiency(retrieval_efficiency, 1)  # num_agents not used in basic range check

def validate_single_game_metrics(
    game_record: GameMetricRecord
) -> bool:
    """
    Validate metrics for a single game.
    
    Args:
        game_record: GameMetricRecord to validate
    
    Returns:
        True if all metrics are valid
    """
    return (
        validate_specialization_range(game_record.specialization_index) and
        validate_retrieval_range(game_record.retrieval_efficiency)
    )

def validate_experiment_metrics(
    records: List[Dict[str, Any]]
) -> ValidationResult:
    """
    Validate all metrics in an experiment.
    
    Args:
        records: List of game result dictionaries with metrics
    
    Returns:
        ValidationResult with validation statistics
    """
    if not records:
        return ValidationResult(
            is_valid=False,
            validation_rate=0.0,
            total_records=0,
            valid_records=0
        )
    
    valid_count = 0
    invalid_reasons: Dict[str, int] = defaultdict(int)
    
    for record in records:
        spec_idx = record.get("specialization_index")
        ret_eff = record.get("retrieval_efficiency")
        
        is_spec_valid = validate_specialization_range(spec_idx) if spec_idx is not None else False
        is_ret_valid = validate_retrieval_range(ret_eff) if ret_eff is not None else False
        
        if is_spec_valid and is_ret_valid:
            valid_count += 1
        else:
            if not is_spec_valid:
                invalid_reasons["specialization_invalid"] += 1
            if not is_ret_valid:
                invalid_reasons["retrieval_invalid"] += 1
    
    validation_rate = valid_count / len(records) if records else 0.0
    
    return ValidationResult(
        is_valid=validation_rate >= 0.95,
        validation_rate=validation_rate,
        total_records=len(records),
        valid_records=valid_count,
        invalid_reasons=dict(invalid_reasons)
    )

def validate_and_filter_records(
    records: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], ValidationResult]:
    """
    Validate records and filter out invalid ones.
    
    Args:
        records: List of game result dictionaries
    
    Returns:
        Tuple of (filtered_records, validation_result)
    """
    validation_result = validate_experiment_metrics(records)
    
    filtered = [
        record for record in records
        if validate_single_game_metrics(GameMetricRecord(
            game_id=record.get("game_id", 0),
            specialization_index=record.get("specialization_index", 0.0),
            retrieval_efficiency=record.get("retrieval_efficiency", 0.0),
            is_valid=True
        ))
    ]
    
    return filtered, validation_result

def compute_metric_statistics(
    records: List[Dict[str, Any]],
    metric_name: str
) -> Dict[str, float]:
    """
    Compute statistics for a specific metric.
    
    Args:
        records: List of game result dictionaries
        metric_name: Name of the metric ("specialization_index" or "retrieval_efficiency")
    
    Returns:
        Dictionary with mean, std, min, max
    """
    values = [r[metric_name] for r in records if metric_name in r and r[metric_name] is not None]
    
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values))
    }

def validate_batch_metrics(
    batch_records: List[Dict[str, Any]],
    min_validation_rate: float = 0.95
) -> ValidationResult:
    """
    Validate a batch of records against a minimum validation rate.
    
    Args:
        batch_records: List of game result dictionaries
        min_validation_rate: Minimum required validation rate
    
    Returns:
        ValidationResult indicating if batch passes
    """
    result = validate_experiment_metrics(batch_records)
    result.is_valid = result.validation_rate >= min_validation_rate
    return result
