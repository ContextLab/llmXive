import os
from typing import Optional, Dict, Any
import torch

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass

class Config:
    """
    Configuration container for the Consciousness Bootstrapping project.
    Enforces CPU-only execution and defines hyperparameters.
    """
    
    def __init__(
        self,
        seed: int = 42,
        batch_size: int = 8,
        recursion_depth: int = 2,
        learning_rate: float = 1e-4,
        token_limit: int = 100000,
        device: Optional[str] = None,
        max_epochs: int = 3,
        log_interval: int = 10,
        save_interval: int = 100
    ):
        self.seed = seed
        self.batch_size = batch_size
        self.recursion_depth = recursion_depth
        self.learning_rate = learning_rate
        self.token_limit = token_limit
        self.max_epochs = max_epochs
        self.log_interval = log_interval
        self.save_interval = save_interval
        
        # Enforce CPU-only execution constraint
        if device is not None:
            if device != "cpu":
                raise ConfigurationError(
                    f"GPU execution is not supported. Got device='{device}', "
                    "but only 'cpu' is allowed per project constraints."
                )
            self.device = device
        else:
            # Default to CPU and verify
            if torch.cuda.is_available():
                # Explicitly force CPU even if CUDA is available
                self.device = "cpu"
            else:
                self.device = "cpu"
        
        self._validate()

    def _validate(self) -> None:
        """Validate configuration parameters."""
        if self.seed < 0:
            raise ConfigurationError(f"Seed must be non-negative, got {self.seed}")
        
        if self.batch_size < 1:
            raise ConfigurationError(f"Batch size must be >= 1, got {self.batch_size}")
        
        if self.recursion_depth < 1:
            raise ConfigurationError(f"Recursion depth must be >= 1, got {self.recursion_depth}")
        
        if self.learning_rate <= 0:
            raise ConfigurationError(f"Learning rate must be > 0, got {self.learning_rate}")
        
        if self.token_limit < 1:
            raise ConfigurationError(f"Token limit must be >= 1, got {self.token_limit}")
        
        if self.max_epochs < 1:
            raise ConfigurationError(f"Max epochs must be >= 1, got {self.max_epochs}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "seed": self.seed,
            "batch_size": self.batch_size,
            "recursion_depth": self.recursion_depth,
            "learning_rate": self.learning_rate,
            "token_limit": self.token_limit,
            "device": self.device,
            "max_epochs": self.max_epochs,
            "log_interval": self.log_interval,
            "save_interval": self.save_interval,
        }

    def __repr__(self) -> str:
        return f"Config(seed={self.seed}, batch_size={self.batch_size}, recursion_depth={self.recursion_depth}, device={self.device})"

_global_config: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration instance.
    If not set, returns a default Config with CPU enforcement.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _global_config
    _global_config = config

def validate_config(config: Dict[str, Any]) -> Config:
    """
    Validate a dictionary of configuration parameters and return a Config instance.
    Raises ConfigurationError if validation fails.
    """
    try:
        return Config(
            seed=config.get("seed", 42),
            batch_size=config.get("batch_size", 8),
            recursion_depth=config.get("recursion_depth", 2),
            learning_rate=config.get("learning_rate", 1e-4),
            token_limit=config.get("token_limit", 100000),
            device=config.get("device", None),
            max_epochs=config.get("max_epochs", 3),
            log_interval=config.get("log_interval", 10),
            save_interval=config.get("save_interval", 100)
        )
    except ConfigurationError as e:
        raise e
    except Exception as e:
        raise ConfigurationError(f"Failed to parse configuration: {e}")

# Ensure CPU-only at module import time as a safety net
if torch.cuda.is_available():
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    torch.set_num_threads(1)
