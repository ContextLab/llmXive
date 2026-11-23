"""
Metrics module initialization.
"""
from .fidelity import compute_lpips, compute_ssim, compute_fidelity_scores, main
from .latency import evaluate_latency_pass_fail, calculate_moving_average_latency
__all__ = [
    "compute_lpips",
    "compute_ssim",
    "compute_fidelity_scores",
    "main",
    "evaluate_latency_pass_fail",
    "calculate_moving_average_latency"
]
