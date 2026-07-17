"""
Environment configuration management for the molecular conformational landscape project.

This module provides centralized configuration for:
- File system paths (data, models, outputs)
- Hyperparameters (batch size, learning rate, latent dimensions)
- CPU thread limits and resource constraints
- Environment variable overrides
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

# Import existing utilities
from utils.logging import get_project_logger
from utils.seeds import set_seed_from_environment

logger = get_project_logger(__name__)


@dataclass
class PathConfig:
    """Configuration for all project file paths."""
    root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_raw: Path = field(init=False)
    data_processed: Path = field(init=False)
    data_calculations: Path = field(init=False)
    data_metadata: Path = field(init=False)
    models: Path = field(init=False)
    figures: Path = field(init=False)
    logs: Path = field(init=False)
    contracts: Path = field(init=False)

    def __post_init__(self):
        """Initialize derived paths relative to root."""
        self.data_raw = self.root / "data" / "raw"
        self.data_processed = self.root / "data" / "processed"
        self.data_calculations = self.root / "data" / "calculation_metadata"
        self.data_metadata = self.root / "data" / "calculation_metadata"
        self.models = self.root / "code" / "models" / "checkpoints"
        self.figures = self.root / "figures"
        self.logs = self.root / "logs"
        self.contracts = self.root / "code" / "contracts"

        # Ensure directories exist
        for path in [
            self.data_raw, self.data_processed, self.data_calculations,
            self.models, self.figures, self.logs, self.contracts
        ]:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {path}")


@dataclass
class HyperParams:
    """Configuration for model hyperparameters and training settings."""
    # VAE Architecture
    latent_dim: int = 64
    hidden_dim: int = 256
    num_layers: int = 2
    activation: str = "relu"

    # Training
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    num_epochs: int = 50
    early_stopping_patience: int = 5

    # Loss weights
    kl_weight: float = 0.001
    reconstruction_weight: float = 1.0

    # Data
    max_smiles_length: int = 200
    num_conformers: int = 10
    conformer_seed: int = 42

    # Evaluation
    alpha_sensitivity: float = 0.05
    bonferroni_adjustment: bool = True
    min_sample_size: int = 1000


@dataclass
class ResourceConfig:
    """Configuration for computational resources and constraints."""
    # CPU constraints (per SC-005)
    num_workers: int = 2
    torch_num_threads: int = 2
    max_memory_gb: float = 7.0
    max_disk_gb: float = 14.0

    # xTB constraints
    xtb_timeout_seconds: int = 300
    xtb_max_retries: int = 3
    xtb_convergence_threshold: float = 1e-5

    # Parallelism
    joblib_n_jobs: int = 2

    # Logging
    log_level: str = "INFO"
    log_json: bool = True


@dataclass
class Config:
    """Master configuration class aggregating all settings."""
    paths: PathConfig = field(default_factory=PathConfig)
    hyperparams: HyperParams = field(default_factory=HyperParams)
    resources: ResourceConfig = field(default_factory=ResourceConfig)
    environment_overrides: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env_prefix: str = "MOLECULAR_VAE_") -> "Config":
        """
        Load configuration from environment variables.

        Environment variables are prefixed with MOLECULAR_VAE_ and map to
        config fields using snake_case (e.g., MOLECULAR_VAE_BATCH_SIZE).
        """
        config = cls()

        # Map environment variables to config fields
        env_mappings = {
            # Paths (if overridden)
            "DATA_RAW": "paths.data_raw",
            "DATA_PROCESSED": "paths.data_processed",
            "MODELS_DIR": "paths.models",
            "FIGURES_DIR": "paths.figures",
            "LOGS_DIR": "paths.logs",

            # Hyperparameters
            "LATENT_DIM": "hyperparams.latent_dim",
            "HIDDEN_DIM": "hyperparams.hidden_dim",
            "NUM_LAYERS": "hyperparams.num_layers",
            "BATCH_SIZE": "hyperparams.batch_size",
            "LEARNING_RATE": "hyperparams.learning_rate",
            "NUM_EPOCHS": "hyperparams.num_epochs",
            "KL_WEIGHT": "hyperparams.kl_weight",
            "MAX_SMILES_LENGTH": "hyperparams.max_smiles_length",
            "NUM_CONFORMERS": "hyperparams.num_conformers",

            # Resources
            "NUM_WORKERS": "resources.num_workers",
            "TORCH_NUM_THREADS": "resources.torch_num_threads",
            "MAX_MEMORY_GB": "resources.max_memory_gb",
            "XTB_TIMEOUT_SECONDS": "resources.xtb_timeout_seconds",
            "XTB_MAX_RETRIES": "resources.xtb_max_retries",
            "JOBLIB_N_JOBS": "resources.joblib_n_jobs",
            "LOG_LEVEL": "resources.log_level",
        }

        for env_var, config_path in env_mappings.items():
            full_env_var = f"{env_prefix}{env_var}"
            value = os.getenv(full_env_var)
            if value is not None:
                config.environment_overrides[full_env_var] = value
                # Parse and set value
                cls._set_nested_value(config, config_path, value)
                logger.info(f"Loaded config from env: {full_env_var}={value}")

        # Initialize seed from environment
        set_seed_from_environment("MOLECULAR_VAE_SEED")

        return config

    @staticmethod
    def _set_nested_value(obj: Any, path: str, value: str) -> None:
        """Set a nested attribute value using dot-notation path."""
        parts = path.split(".")
        current = obj
        for part in parts[:-1]:
            current = getattr(current, part)
        final_attr = parts[-1]

        # Type conversion
        field_type = type(getattr(current, final_attr))
        try:
            if field_type == int:
                converted = int(value)
            elif field_type == float:
                converted = float(value)
            elif field_type == bool:
                converted = value.lower() in ("true", "1", "yes")
            else:
                converted = value
            setattr(current, final_attr, converted)
        except ValueError as e:
            logger.warning(f"Failed to convert {path}={value} to {field_type}: {e}")

    def save_to_json(self, filepath: Optional[Path] = None) -> Path:
        """Save configuration to a JSON file."""
        if filepath is None:
            filepath = self.paths.data_processed / "config.json"

        # Convert Path objects to strings for JSON serialization
        data = asdict(self)
        for key, value in data["paths"].items():
            if isinstance(value, Path):
                data["paths"][key] = str(value)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Configuration saved to {filepath}")
        return filepath

    @classmethod
    def load_from_json(cls, filepath: Path) -> "Config":
        """Load configuration from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        # Reconstruct Path objects
        data["paths"] = PathConfig(
            root=Path(data["paths"]["root"])
        )
        # Manually set derived paths to avoid __post_init__ conflicts
        for attr in ["data_raw", "data_processed", "data_calculations",
                    "data_metadata", "models", "figures", "logs", "contracts"]:
            setattr(data["paths"], attr, Path(data["paths"][attr]))

        config = cls(
            paths=data["paths"],
            hyperparams=HyperParams(**data["hyperparams"]),
            resources=ResourceConfig(**data["resources"])
        )
        logger.info(f"Configuration loaded from {filepath}")
        return config

    def __str__(self) -> str:
        """Return a human-readable summary of the configuration."""
        summary = [
            "=== Configuration Summary ===",
            f"Root: {self.paths.root}",
            f"Latent Dim: {self.hyperparams.latent_dim}",
            f"Batch Size: {self.hyperparams.batch_size}",
            f"Learning Rate: {self.hyperparams.learning_rate}",
            f"Num Workers: {self.resources.num_workers}",
            f"Torch Threads: {self.resources.torch_num_threads}",
            f"Max Memory (GB): {self.resources.max_memory_gb}",
            f"XTB Timeout (s): {self.resources.xtb_timeout_seconds}",
            f"Log Level: {self.resources.log_level}",
        ]
        return "\n".join(summary)


# Global configuration instance
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance, initializing if necessary."""
    global _global_config
    if _global_config is None:
        _global_config = Config.from_env()
        logger.info("Global configuration initialized from environment")
    return _global_config


def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _global_config
    _global_config = None
    logger.info("Global configuration reset")


# Convenience accessors
def get_paths() -> PathConfig:
    """Get path configuration."""
    return get_config().paths


def get_hyperparams() -> HyperParams:
    """Get hyperparameter configuration."""
    return get_config().hyperparams


def get_resources() -> ResourceConfig:
    """Get resource configuration."""
    return get_config().resources