"""
Configuration management for the simulation engine.

Defines the SimulationConfig dataclass and helper functions to load
configurations from YAML files or environment variables.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal
import os
import yaml

# Supported distribution types
DistributionType = Literal["normal", "skewed", "heteroscedastic"]

@dataclass
class SimulationConfig:
    """
    Configuration for the synthetic data generation simulation.

    Attributes:
        n_samples: Number of samples per group (default 100).
        n_iterations: Number of simulation iterations (default 1000).
        effect_size: Mean difference for alternative hypothesis (default 1.0).
        null_effect_size: Mean difference for null hypothesis (default 0.0).
        base_std: Standard deviation for normal distributions (default 1.0).
        distribution_type: Type of distribution to generate ('normal', 'skewed', 'heteroscedastic').
        seed: Random seed for reproducibility (default 42).
        alpha: Significance level for statistical tests (default 0.05).
        output_dir: Directory to save simulation results.
        log_level: Logging level (default 'INFO').
    """
    n_samples: int = 100
    n_iterations: int = 1000
    effect_size: float = 1.0
    null_effect_size: float = 0.0
    base_std: float = 1.0
    distribution_type: DistributionType = "normal"
    seed: int = 42
    alpha: float = 0.05
    output_dir: str = "data/synthetic"
    log_level: str = "INFO"

    # Skewness parameters for skewed distribution
    skewness_factor: float = 2.0

    # Heteroscedasticity parameters
    hetero_ratio: float = 2.0  # Ratio of std dev between groups

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.n_samples <= 0:
            raise ValueError("n_samples must be positive")
        if self.n_iterations <= 0:
            raise ValueError("n_iterations must be positive")
        if self.base_std <= 0:
            raise ValueError("base_std must be positive")
        if self.distribution_type not in ["normal", "skewed", "heteroscedastic"]:
            raise ValueError(f"Invalid distribution_type: {self.distribution_type}")

    @classmethod
    def from_yaml(cls, config_path: str) -> "SimulationConfig":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file.

        Returns:
            SimulationConfig instance populated with values from the file.
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        if config_dict is None:
            config_dict = {}

        return cls(**config_dict)

    @classmethod
    def from_env(cls) -> "SimulationConfig":
        """
        Load configuration from environment variables.

        Environment variables are prefixed with SIMULATION_.
        Example: SIMULATION_N_SAMPLES, SIMULATION_EFFECT_SIZE.

        Returns:
            SimulationConfig instance populated with environment values.
        """
        env_map = {
            "n_samples": "SIMULATION_N_SAMPLES",
            "n_iterations": "SIMULATION_N_ITERATIONS",
            "effect_size": "SIMULATION_EFFECT_SIZE",
            "null_effect_size": "SIMULATION_NULL_EFFECT_SIZE",
            "base_std": "SIMULATION_BASE_STD",
            "distribution_type": "SIMULATION_DISTRIBUTION_TYPE",
            "seed": "SIMULATION_SEED",
            "alpha": "SIMULATION_ALPHA",
            "output_dir": "SIMULATION_OUTPUT_DIR",
            "log_level": "SIMULATION_LOG_LEVEL",
            "skewness_factor": "SIMULATION_SKEWNESS_FACTOR",
            "hetero_ratio": "SIMULATION_HETERO_RATIO",
        }

        config_kwargs = {}
        for attr, env_var in env_map.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion based on expected attribute type
                if attr in ["n_samples", "n_iterations", "seed"]:
                    config_kwargs[attr] = int(value)
                elif attr in ["effect_size", "null_effect_size", "base_std", "alpha", "skewness_factor", "hetero_ratio"]:
                    config_kwargs[attr] = float(value)
                else:
                    config_kwargs[attr] = value

        return cls(**config_kwargs)

    def to_dict(self) -> dict:
        """
        Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "n_samples": self.n_samples,
            "n_iterations": self.n_iterations,
            "effect_size": self.effect_size,
            "null_effect_size": self.null_effect_size,
            "base_std": self.base_std,
            "distribution_type": self.distribution_type,
            "seed": self.seed,
            "alpha": self.alpha,
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "skewness_factor": self.skewness_factor,
            "hetero_ratio": self.hetero_ratio,
        }

    def __repr__(self) -> str:
        return f"SimulationConfig(n_samples={self.n_samples}, n_iterations={self.n_iterations}, distribution_type='{self.distribution_type}')"

    def save_to_yaml(self, config_path: str) -> None:
        """
        Save the current configuration to a YAML file.

        Args:
            config_path: Path where the YAML file will be written.
        """
        os.makedirs(os.path.dirname(config_path), exist_ok=True) if os.path.dirname(config_path) else None
        with open(config_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

def get_default_config() -> SimulationConfig:
    """
    Create and return a default SimulationConfig instance.

    Returns:
        A SimulationConfig with default parameter values.
    """
    return SimulationConfig()