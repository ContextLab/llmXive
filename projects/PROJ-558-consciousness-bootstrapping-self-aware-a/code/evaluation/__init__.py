"""
Evaluation package for metrics, benchmarks, and loss functions.
"""
from .loss_functions import compute_self_consistency_proxy, compute_joint_loss, compute_self_consistency_loss
from .metrics import calculate_self_consistency, calculate_roc_auc, calculate_brier_score, calculate_ece, calculate_calibration_curve, calculate_entropy, aggregate_metrics, calculate_error_detection_calibration
from .results import EvaluationResult
