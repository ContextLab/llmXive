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
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class GameMetricRecord:
    """Record of metrics for a single game."""
    game_id: int
    specialization_index: float
    retrieval_efficiency: float
    agent_count: int
    context_condition: str

def validate_specialization_range(spec_index: float, agent_count: int) -> ValidationResult:
    """Validate specialization index is within valid range."""
    if not validate_specialization_index(spec_index, agent_count):
        return ValidationResult(
            is_valid=False,
            errors=[f"Specialization index {spec_index} out of range for {agent_count} agents"]
        )
    return ValidationResult(is_valid=True)

def validate_retrieval_range(efficiency: float) -> ValidationResult:
    """Validate retrieval efficiency is within valid range."""
    if not validate_retrieval_efficiency(efficiency):
        return ValidationResult(
            is_valid=False,
            errors=[f"Retrieval efficiency {efficiency} out of range [0, 1]"]
        )
    return ValidationResult(is_valid=True)

def validate_single_game_metrics(record: GameMetricRecord) -> ValidationResult:
    """Validate metrics for a single game."""
    errors = []
    warnings = []
    
    # Validate specialization
    spec_result = validate_specialization_range(record.specialization_index, record.agent_count)
    if not spec_result.is_valid:
        errors.extend(spec_result.errors)
    
    # Validate retrieval
    retrieval_result = validate_retrieval_range(record.retrieval_efficiency)
    if not retrieval_result.is_valid:
        errors.extend(retrieval_result.errors)
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)

def validate_experiment_metrics(results: List[GameMetricRecord], threshold: float = 0.95) -> ValidationResult:
    """
    Validate metrics for an entire experiment.
    
    Args:
        results: List of game metric records
        threshold: Minimum proportion of valid games required (default 0.95)
        
    Returns:
        ValidationResult with experiment-level validation
    """
    if not results:
        return ValidationResult(is_valid=False, errors=["No results to validate"])
    
    valid_count = 0
    errors = []
    warnings = []
    
    for record in results:
        record_result = validate_single_game_metrics(record)
        if record_result.is_valid:
            valid_count += 1
        else:
            errors.extend(record_result.errors)
    
    validation_rate = valid_count / len(results)
    
    if validation_rate < threshold:
        warnings.append(f"Validation rate {validation_rate:.2%} < {threshold:.2%} threshold")
    
    return ValidationResult(
        is_valid=validation_rate >= threshold,
        errors=errors,
        warnings=warnings
    )

def validate_and_filter_records(results: List[GameMetricRecord]) -> Tuple[List[GameMetricRecord], List[GameMetricRecord]]:
    """
    Validate and separate valid/invalid records.
    
    Returns:
        Tuple of (valid_records, invalid_records)
    """
    valid = []
    invalid = []
    
    for record in results:
        if validate_single_game_metrics(record).is_valid:
            valid.append(record)
        else:
            invalid.append(record)
    
    return valid, invalid

def compute_metric_statistics(results: List[GameMetricRecord]) -> Dict[str, Any]:
    """Compute statistics for metrics across results."""
    if not results:
        return {}
    
    spec_values = [r.specialization_index for r in results]
    retrieval_values = [r.retrieval_efficiency for r in results]
    
    return {
        'count': len(results),
        'specialization': {
            'mean': float(np.mean(spec_values)),
            'std': float(np.std(spec_values)),
            'min': float(np.min(spec_values)),
            'max': float(np.max(spec_values))
        },
        'retrieval': {
            'mean': float(np.mean(retrieval_values)),
            'std': float(np.std(retrieval_values)),
            'min': float(np.min(retrieval_values)),
            'max': float(np.max(retrieval_values))
        }
    }

def validate_batch_metrics(results: List[Dict[str, Any]], agent_count: int) -> ValidationResult:
    """
    Validate a batch of results from dictionaries.
    
    Args:
        results: List of dicts with 'specialization_index' and 'retrieval_efficiency'
        agent_count: Number of agents for this batch
        
    Returns:
        ValidationResult
    """
    records = [
        GameMetricRecord(
            game_id=r.get('game_id', i),
            specialization_index=r['specialization_index'],
            retrieval_efficiency=r['retrieval_efficiency'],
            agent_count=agent_count,
            context_condition=r.get('context_condition', 'unknown')
        )
        for i, r in enumerate(results)
    ]
    return validate_experiment_metrics(records)
