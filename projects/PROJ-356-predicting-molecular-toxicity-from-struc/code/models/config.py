"""
Configuration for model hyperparameters and settings.
"""
from typing import Dict, Any

class ModelConfig:
    """Configuration container for model parameters."""

    def __init__(self):
        self.logistic: Dict[str, Any] = {
            "max_iter": 1000,
            "random_state": 42,
            "solver": "lbfgs",
            "cv_folds": 5,
            "cv_repeats": 3,
        }
        self.rule_based: Dict[str, Any] = {
            "config_path": "config/structural_alerts.json",
        }

    def get_logistic_params(self) -> Dict[str, Any]:
        """Return logistic regression parameters."""
        return self.logistic.copy()

    def get_rule_based_params(self) -> Dict[str, Any]:
        """Return rule-based model parameters."""
        return self.rule_based.copy()