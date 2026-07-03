"""
Metric validation utilities to ensure computed values are within expected ranges.
Implements SC-001 requirement: >= 95% of games must produce valid metrics.
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict

from .specialization import validate_specialization_index
from .retrieval import validate_retrieval_efficiency

@dataclass
class ValidationResult:
    """Result of a metric validation check."""
    is_valid: bool
    message: str
    metric_name: str
    value: float

@dataclass
class GameMetricRecord:
    """Record of metrics for a single game."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    is_valid: bool
    validation_message: str

def validate_single_game_metrics(specialization_index: float, 
                                retrieval_efficiency: float,
                                game_id: Optional[int] = None) -> ValidationResult:
    """
    Validate metrics for a single game.
    
    Args:
        specialization_index: Computed specialization index
        retrieval_efficiency: Computed retrieval efficiency
        game_id: Optional game identifier for logging
        
    Returns:
        ValidationResult indicating validity and reason
    """
    # Validate specialization index
    spec_valid, spec_msg = validate_specialization_index(specialization_index)
    if not spec_valid:
        return ValidationResult(
            is_valid=False,
            message=f"Specialization index invalid: {spec_msg}",
            metric_name="specialization_index",
            value=specialization_index
        )
    
    # Validate retrieval efficiency
    ret_valid, ret_msg = validate_retrieval_efficiency(retrieval_efficiency)
    if not ret_valid:
        return ValidationResult(
            is_valid=False,
            message=f"Retrieval efficiency invalid: {ret_msg}",
            metric_name="retrieval_efficiency",
            value=retrieval_efficiency
        )
    
    return ValidationResult(
        is_valid=True,
        message="All metrics valid",
        metric_name="all",
        value=0.0
    )

def validate_and_filter_records(results: List[Any]) -> Tuple[List[GameMetricRecord], float]:
    """
    Validate a list of game results and filter invalid ones.
    
    Args:
        results: List of GameResult objects (or dict-like objects with metrics)
        
    Returns:
        Tuple of (valid records list, pass rate)
    """
    valid_records = []
    total = len(results)
    
    for r in results:
        # Support both object attribute access and dict access
        if hasattr(r, 'specialization_index'):
            spec_idx = r.specialization_index
            ret_eff = r.retrieval_efficiency
            gid = getattr(r, 'game_id', -1)
        elif isinstance(r, dict):
            spec_idx = r.get('specialization_index', 0.0)
            ret_eff = r.get('retrieval_efficiency', 0.0)
            gid = r.get('game_id', -1)
        else:
            # Fallback for unknown types
            continue
            
        validation = validate_single_game_metrics(
            spec_idx,
            ret_eff,
            gid
        )
        
        record = GameMetricRecord(
            game_id=gid,
            specialization_index=spec_idx,
            retrieval_efficiency=ret_eff,
            is_valid=validation.is_valid,
            validation_message=validation.message
        )
        
        if validation.is_valid:
            valid_records.append(record)
    
    pass_rate = len(valid_records) / total if total > 0 else 0.0
    return valid_records, pass_rate

def compute_metric_statistics(records: List[GameMetricRecord]) -> Dict[str, float]:
    """
    Compute basic statistics for validated metrics.
    
    Args:
        records: List of valid GameMetricRecord objects
        
    Returns:
        Dictionary of statistics
    """
    if not records:
        return {
            'count': 0,
            'specialization_mean': 0.0,
            'specialization_std': 0.0,
            'retrieval_mean': 0.0,
            'retrieval_std': 0.0
        }
    
    specs = [r.specialization_index for r in records]
    rets = [r.retrieval_efficiency for r in records]
    
    return {
        'count': len(records),
        'specialization_mean': float(np.mean(specs)),
        'specialization_std': float(np.std(specs)),
        'retrieval_mean': float(np.mean(rets)),
        'retrieval_std': float(np.std(rets))
    }

def validate_experiment_metrics(results: List[Any]) -> Dict[str, Any]:
    """
    Validate an entire experiment's results and return summary.
    
    Args:
        results: List of GameResult objects (or dict-like objects)
        
    Returns:
        Dictionary with validation summary
    """
    valid_records, pass_rate = validate_and_filter_records(results)
    stats = compute_metric_statistics(valid_records)
    
    return {
        'total_games': len(results),
        'valid_games': len(valid_records),
        'pass_rate': pass_rate,
        'meets_sc001': pass_rate >= 0.95,
        'statistics': stats
    }