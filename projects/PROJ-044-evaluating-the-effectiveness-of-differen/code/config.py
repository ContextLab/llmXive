"""
Configuration management for the Differential Privacy Federated Learning experiments.

Defines the base configuration dataclass and validation logic for experiment parameters.
"""
from dataclasses import dataclass, field
from typing import Literal, Optional
import os
import json
from pathlib import Path


# Valid dataset names restricted to FEMNIST per plan.md Gap Analysis
VALID_DATASETS = Literal["femnist"]
VALID_ALPHA_VALUES = [0.05, 0.1, 0.5, 1.0]
VALID_EPSILON_VALUES = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0]


@dataclass(frozen=True)
class Config:
    """
    Base configuration for DP-FL experiments.

    Attributes:
        seed: Random seed for reproducibility.
        alpha: Dirichlet distribution parameter for client heterogeneity.
               Lower values (e.g., 0.1) create high heterogeneity.
        epsilon: Target privacy budget (Differential Privacy).
        dataset: Name of the dataset to use. Only 'femnist' is supported.
    """
    seed: int = 42
    alpha: float = 0.5
    epsilon: float = 1.0
    dataset: VALID_DATASETS = "femnist"

    # Derived paths (computed on demand to avoid mutation)
    _base_dir: Path = field(default=Path("."), repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.seed < 0:
            raise ValueError(f"Seed must be non-negative, got {self.seed}")

        if self.alpha <= 0:
            raise ValueError(f"Alpha must be positive, got {self.alpha}")

        if self.epsilon < 0:
            raise ValueError(f"Epsilon must be non-negative, got {self.epsilon}")

        # Strict validation: Only 'femnist' is allowed.
        # 'shakespeare' is explicitly excluded per plan.md Gap Analysis.
        if self.dataset != "femnist":
            raise ValueError(
                "Shakespeare excluded per plan.md Gap Analysis (no verified source)."
            )

    @property
    def data_dir(self) -> Path:
        """Path to the raw data directory."""
        return self._base_dir / "data" / "raw"

    @property
    def partition_dir(self) -> Path:
        """Path to the partitions directory."""
        return self._base_dir / "data" / "partitions"

    @property
    def results_dir(self) -> Path:
        """Path to the results directory."""
        return self._base_dir / "results"

    @property
    def log_dir(self) -> Path:
        """Path to the logs directory."""
        return self._base_dir / "logs"

    def to_dict(self) -> dict:
        """Convert configuration to a dictionary."""
        return {
            "seed": self.seed,
            "alpha": self.alpha,
            "epsilon": self.epsilon,
            "dataset": self.dataset,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict, base_dir: Optional[Path] = None) -> "Config":
        """
        Create a Config instance from a dictionary.

        Args:
            data: Dictionary containing configuration keys.
            base_dir: Optional base directory path. Defaults to current working directory.

        Returns:
            A new Config instance.
        """
        base = base_dir or Path(".")
        # Enforce default to femnist if not provided, but validation will catch invalid ones
        dataset_val = data.get("dataset", "femnist")
        return cls(
            seed=data.get("seed", 42),
            alpha=data.get("alpha", 0.5),
            epsilon=data.get("epsilon", 1.0),
            dataset=dataset_val,
        )

    @classmethod
    def from_json_file(cls, path: str, base_dir: Optional[Path] = None) -> "Config":
        """
        Load configuration from a JSON file.

        Args:
            path: Path to the JSON configuration file.
            base_dir: Optional base directory path.

        Returns:
            A new Config instance.
        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data, base_dir)

    def save(self, path: str) -> None:
        """
        Save configuration to a JSON file.

        Args:
            path: Path where the JSON file will be saved.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            f.write(self.to_json())


def get_default_config() -> Config:
    """Return a default configuration instance."""
    return Config()


def load_config_from_env() -> Config:
    """
    Load configuration from environment variables.

    Falls back to defaults if environment variables are not set.

    Returns:
        A Config instance populated from environment variables.
    """
    seed = int(os.getenv("EXPERIMENT_SEED", "42"))
    alpha = float(os.getenv("EXPERIMENT_ALPHA", "0.5"))
    epsilon = float(os.getenv("EXPERIMENT_EPSILON", "1.0"))
    dataset = os.getenv("EXPERIMENT_DATASET", "femnist")

    return Config(
        seed=seed,
        alpha=alpha,
        epsilon=epsilon,
        dataset=dataset,
    )