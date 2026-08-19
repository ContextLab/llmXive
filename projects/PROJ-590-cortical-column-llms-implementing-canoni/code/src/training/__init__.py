"""
Training Package - Contains training loops and homeostasis utilities.
"""
from .trainer import (
    TrainingConfig,
    TrainingMetrics,
    get_resource_usage,
    calculate_mae,
    train_epoch,
    evaluate,
    run_training,
)
from .homeostasis import (
    HomeostasisConfig,
    ActivityStats,
    calculate_current_ei_ratio,
    scale_weights,
    log_gradient_norms,
    enforce_ei_ratio,
    apply_ei_balance_constraint,
    verify_ei_balance,
    HomeostaticScaler,
    apply_scaling_hook,
)

__all__ = [
    "TrainingConfig",
    "TrainingMetrics",
    "get_resource_usage",
    "calculate_mae",
    "train_epoch",
    "evaluate",
    "run_training",
    "HomeostasisConfig",
    "ActivityStats",
    "calculate_current_ei_ratio",
    "scale_weights",
    "log_gradient_norms",
    "enforce_ei_ratio",
    "apply_ei_balance_constraint",
    "verify_ei_balance",
    "HomeostaticScaler",
    "apply_scaling_hook",
]
