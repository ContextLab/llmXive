"""Validation logic for metrics."""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from metrics.specialization import compute_specialization_index, validate_specialization_index
from metrics.retrieval import compute_retrieval_efficiency, validate_retrieval_efficiency


@dataclass
class GameMetricRecord:
    game_id: str
    specialization_index: float
    retrieval_efficiency: float
    context_condition: str
    agent_count: int


@dataclass
class ValidationResult:
    valid: bool
    message: str
    filtered_count: int = 0
    total_count: int = 0


def validate_single_game_metrics(
    spec_idx: float, 
    ret_eff: float
) -> Tuple[bool, str]:
    """Validates metrics for a single game."""
    spec_valid, spec_msg = validate_specialization_index(spec_idx)
    if not spec_valid:
        return False, f"Specialization: {spec_msg}"
    
    # Retrieval efficiency should be between 0 and 1
    if not (0.0 <= ret_eff <= 1.0):
        return False, f"Retrieval efficiency {ret_eff} out of range [0, 1]"
    
    return True, "OK"


def validate_and_filter_records(
    records: List[Dict[str, Any]], 
    min_success_rate: float = 0.95
) -> ValidationResult:
    """
    Validates a list of game records.
    
    Per SC-001: ≥95% games must produce valid metrics.
    """
    valid_records = []
    invalid_count = 0
    
    for rec in records:
        try:
            spec = float(rec.get('specialization_index', -1))
            ret = float(rec.get('retrieval_efficiency', -1))
            
            is_valid, _ = validate_single_game_metrics(spec, ret)
            if is_valid:
                valid_records.append(rec)
            else:
                invalid_count += 1
        except (ValueError, TypeError):
            invalid_count += 1
    
    total = len(records)
    if total == 0:
        return ValidationResult(valid=False, message="No records to validate")
    
    success_rate = len(valid_records) / total
    is_experiment_valid = success_rate >= min_success_rate
    
    return ValidationResult(
        valid=is_experiment_valid,
        message=f"Validated {len(valid_records)}/{total} ({success_rate:.2%}). Threshold: {min_success_rate:.0%}",
        filtered_count=invalid_count,
        total_count=total
    )


def compute_metric_statistics(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """Computes basic statistics for the metrics."""
    if not records:
        return {}
    
    specs = [float(r['specialization_index']) for r in records]
    rets = [float(r['retrieval_efficiency']) for r in records]
    
    return {
        "mean_specialization": float(np.mean(specs)),
        "std_specialization": float(np.std(specs)),
        "mean_retrieval": float(np.mean(rets)),
        "std_retrieval": float(np.std(rets))
    }


def validate_experiment_metrics(records: List[Dict[str, Any]]) -> bool:
    """Validates the entire experiment result set."""
    result = validate_and_filter_records(records)
    return result.valid


def validate_game_result_for_metrics(result: Dict[str, Any]) -> bool:
    """Validates a single game result dictionary."""
    if 'specialization_index' not in result or 'retrieval_efficiency' not in result:
        return False
    return validate_single_game_metrics(
        result['specialization_index'], 
        result['retrieval_efficiency']
    )[0]
