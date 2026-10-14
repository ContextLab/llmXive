from dataclasses import dataclass, field

@dataclass(frozen=True)
class Config:
    """
    Global configuration for the project.

    Attributes
    ----------
    primary_model : str
        Determines which drift model is used as the primary predictor.
        Allowed values are "linear" (default) and "exponential".
    random_seed : int
        Fixed seed for all stochastic processes to ensure reproducibility.
    """
    primary_model: str = "linear"
    random_seed: int = 42

# Singleton instance used throughout the codebase
CONFIG = Config()
