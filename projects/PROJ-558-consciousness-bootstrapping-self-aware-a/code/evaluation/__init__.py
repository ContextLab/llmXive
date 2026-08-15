"""
Evaluation metrics and benchmarking tools.
"""
from .metrics import calculate_self_consistency, calculate_ece, calculate_brier_score
from .results import EvaluationResult
from .loss_functions import compute_joint_loss, compute_self_consistency_proxy
