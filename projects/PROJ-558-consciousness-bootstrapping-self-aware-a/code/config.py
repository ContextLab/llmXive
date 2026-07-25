import os
from typing import Optional, Dict, Any
import torch

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass

class Config:
    """
    Configuration management for the Consciousness Bootstrapping project.
    Handles hyperparameters and enforces execution constraints.
    """

    def __init__(
        self,
        seed: int = 42,
        batch_size: int = 8,
        recursion_depth: int = 2,
        learning_rate: float = 1e-4,
        token_limit: int = 100000,
        max_steps: int = 1000,
        device: Optional[str] = None,
        log_level: str = "INFO",
        data_dir: str = "data/raw",
        output_dir: str = "artifacts/results",
    ):
        self.seed = seed
        self.batch_size = batch_size
        self.recursion_depth = recursion_depth
        self.learning_rate = learning_rate
        self.token_limit = token_limit
        self.max_steps = max_steps
        self.log_level = log_level
        self.data_dir = data_dir
        self.output_dir = output_dir

        # Enforce CPU-only execution constraint
        self._enforce_cpu_only(device)

    def _enforce_cpu_only(self, provided_device: Optional[str]) -> None:
        """
        Enforces that execution is restricted to CPU.
        Raises ConfigurationError if GPU is detected or requested.
        """
        if provided_device is not None:
            if "cuda" in provided_device.lower():
                raise ConfigurationError(
                    "GPU execution is explicitly forbidden by project constraints. "
                    "Use 'cpu' or None."
                )
            self.device = provided_device
        else:
            # Default to CPU
            self.device = "cpu"

        # Double-check at runtime if torch is available
        if torch.cuda.is_available():
            # We allow the system to have CUDA, but we force the config to use CPU
            # to prevent accidental usage.
            if "cuda" in self.device:
                raise ConfigurationError(
                    "GPU execution is forbidden. Even if CUDA is available, "
                    "this project must run on CPU."
                )

    def to_dict(self) -> Dict[str, Any]:
        """Returns the configuration as a dictionary."""
        return {
            "seed": self.seed,
            "batch_size": self.batch_size,
            "recursion_depth": self.recursion_depth,
            "learning_rate": self.learning_rate,
            "token_limit": self.token_limit,
            "max_steps": self.max_steps,
            "device": self.device,
            "log_level": self.log_level,
            "data_dir": self.data_dir,
            "output_dir": self.output_dir,
        }

    @classmethod
    def from_env(cls) -> "Config":
        """
        Loads configuration from environment variables with sensible defaults.
        Useful for CI/CD pipelines.
        """
        seed = int(os.getenv("CONFIG_SEED", 42))
        batch_size = int(os.getenv("CONFIG_BATCH_SIZE", 8))
        recursion_depth = int(os.getenv("CONFIG_RECURSION_DEPTH", 2))
        learning_rate = float(os.getenv("CONFIG_LEARNING_RATE", 1e-4))
        token_limit = int(os.getenv("CONFIG_TOKEN_LIMIT", 100000))
        max_steps = int(os.getenv("CONFIG_MAX_STEPS", 1000))
        log_level = os.getenv("CONFIG_LOG_LEVEL", "INFO")
        data_dir = os.getenv("CONFIG_DATA_DIR", "data/raw")
        output_dir = os.getenv("CONFIG_OUTPUT_DIR", "artifacts/results")
        device = os.getenv("CONFIG_DEVICE", None)

        return cls(
            seed=seed,
            batch_size=batch_size,
            recursion_depth=recursion_depth,
            learning_rate=learning_rate,
            token_limit=token_limit,
            max_steps=max_steps,
            device=device,
            log_level=log_level,
            data_dir=data_dir,
            output_dir=output_dir,
        )

# Global configuration instance (singleton pattern)
_global_config: Optional[Config] = None

def get_config() -> Config:
    """Returns the global configuration instance, creating one if necessary."""
    global _global_config
    if _global_config is None:
        _global_config = Config.from_env()
    return _global_config

def set_config(config: Config) -> None:
    """Sets the global configuration instance."""
    global _global_config
    _global_config = config

def validate_config(config: Config) -> bool:
    """
    Validates the configuration object for logical consistency.
    Returns True if valid, raises ConfigurationError otherwise.
    """
    if config.recursion_depth < 1:
        raise ConfigurationError("Recursion depth must be at least 1.")
    if config.recursion_depth > 2:
        raise ConfigurationError(
            "Recursion depth is strictly capped at 2 by project constraints."
        )
    if config.batch_size < 1:
        raise ConfigurationError("Batch size must be at least 1.")
    if config.learning_rate <= 0:
        raise ConfigurationError("Learning rate must be positive.")
    if config.token_limit <= 0:
        raise ConfigurationError("Token limit must be positive.")
    if config.seed < 0:
        raise ConfigurationError("Seed must be non-negative.")

    # Re-verify CPU constraint
    if "cuda" in config.device:
        raise ConfigurationError(
            "Configuration validation failed: GPU device specified."
        )

    return True