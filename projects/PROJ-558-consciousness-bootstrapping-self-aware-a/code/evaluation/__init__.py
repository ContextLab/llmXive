"""
Evaluation metrics, benchmark runners, and result entities.
Includes self-consistency metrics, calibration, and benchmark execution.
"""
from .metrics import (
    calculate_self_consistency,
    calculate_roc_auc,
    calculate_brier_score,
    calculate_ece,
    calculate_error_detection_calibration,
)
from .results import EvaluationResult
from .loss_functions import compute_self_consistency_proxy, compute_joint_loss

__all__ = [
    "calculate_self_consistency",
    "calculate_roc_auc",
    "calculate_brier_score",
    "calculate_ece",
    "calculate_error_detection_calibration",
    "EvaluationResult",
    "compute_self_consistency_proxy",
    "compute_joint_loss",
]
