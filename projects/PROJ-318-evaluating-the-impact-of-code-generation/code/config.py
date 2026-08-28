"""
Environment configuration management for the llmXive pipeline.

This module provides a centralized Config class to manage model paths,
rate-limit retries, and other environment-specific settings.
It reads from environment variables and provides validation logic.
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ConfigException(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Centralized configuration management.

    Loads settings from environment variables with sensible defaults.
    Validates critical paths and settings on initialization.
    """

    # Environment variable keys
    MODEL_PATH_ENV = "CODEGEN_MODEL_PATH"
    QUANTIZATION_BIT_ENV = "QUANTIZATION_BITS"
    RATE_LIMIT_RETRIES_ENV = "RATE_LIMIT_RETRIES"
    RATE_LIMIT_BACKOFF_ENV = "RATE_LIMIT_BACKOFF_SECONDS"
    MAX_MEMORY_MB_ENV = "MAX_MEMORY_MB"
    DEVICE_ENV = "DEVICE"

    # Default values
    DEFAULT_MODEL_PATH = "Salesforce/codegen-350M-mono"
    DEFAULT_QUANTIZATION_BITS = 4
    DEFAULT_RATE_LIMIT_RETRIES = 3
    DEFAULT_RATE_LIMIT_BACKOFF = 5.0
    DEFAULT_MAX_MEMORY_MB = 7000  # 7 GB limit as per task requirements
    DEFAULT_DEVICE = "cpu"

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.model_path: str = self._get_env(
            self.MODEL_PATH_ENV, self.DEFAULT_MODEL_PATH
        )
        self.quantization_bits: int = self._get_env_int(
            self.QUANTIZATION_BIT_ENV, self.DEFAULT_QUANTIZATION_BITS
        )
        self.rate_limit_retries: int = self._get_env_int(
            self.RATE_LIMIT_RETRIES_ENV, self.DEFAULT_RATE_LIMIT_RETRIES
        )
        self.rate_limit_backoff: float = self._get_env_float(
            self.RATE_LIMIT_BACKOFF_ENV, self.DEFAULT_RATE_LIMIT_BACKOFF
        )
        self.max_memory_mb: int = self._get_env_int(
            self.MAX_MEMORY_MB_ENV, self.DEFAULT_MAX_MEMORY_MB
        )
        self.device: str = self._get_env(
            self.DEVICE_ENV, self.DEFAULT_DEVICE
        )

        self._validate()
        logger.info(
            "Configuration loaded: model=%s, quant=%db, retries=%d, max_mem=%dMB",
            self.model_path,
            self.quantization_bits,
            self.rate_limit_retries,
            self.max_memory_mb,
        )

    def _get_env(self, key: str, default: str) -> str:
        """Get string environment variable or default."""
        val = os.getenv(key, default)
        if not isinstance(val, str):
            raise ConfigException(f"Invalid type for env var {key}: expected str, got {type(val)}")
        return val

    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer environment variable or default."""
        val_str = os.getenv(key, str(default))
        try:
            return int(val_str)
        except ValueError:
            raise ConfigException(f"Invalid integer for env var {key}: {val_str}")

    def _get_env_float(self, key: str, default: float) -> float:
        """Get float environment variable or default."""
        val_str = os.getenv(key, str(default))
        try:
            return float(val_str)
        except ValueError:
            raise ConfigException(f"Invalid float for env var {key}: {val_str}")

    def _validate(self) -> None:
        """Validate configuration settings."""
        if self.quantization_bits not in [4, 8, 16, 32]:
            raise ConfigException(
                f"Quantization bits must be 4, 8, 16, or 32. Got: {self.quantization_bits}"
            )

        if self.rate_limit_retries < 0:
            raise ConfigException(
                f"Rate limit retries must be non-negative. Got: {self.rate_limit_retries}"
            )

        if self.rate_limit_backoff <= 0:
            raise ConfigException(
                f"Rate limit backoff must be positive. Got: {self.rate_limit_backoff}"
            )

        if self.max_memory_mb <= 0:
            raise ConfigException(
                f"Max memory must be positive. Got: {self.max_memory_mb}"
            )

        # Validate device
        if self.device not in ["cpu", "cuda", "mps"]:
            raise ConfigException(
                f"Invalid device: {self.device}. Must be 'cpu', 'cuda', or 'mps'."
            )

    def get_model_path(self) -> str:
        """Get the configured model path."""
        return self.model_path

    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration."""
        return {
            "retries": self.rate_limit_retries,
            "backoff_seconds": self.rate_limit_backoff,
        }

    def get_max_memory_mb(self) -> int:
        """Get the maximum memory limit in MB."""
        return self.max_memory_mb

    def get_device(self) -> str:
        """Get the configured device."""
        return self.device

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to a dictionary."""
        return {
            "model_path": self.model_path,
            "quantization_bits": self.quantization_bits,
            "rate_limit_retries": self.rate_limit_retries,
            "rate_limit_backoff": self.rate_limit_backoff,
            "max_memory_mb": self.max_memory_mb,
            "device": self.device,
        }

# Singleton instance for easy access
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration singleton."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# Verify import works by instantiating (will raise if env vars are invalid)
if __name__ == "__main__":
    cfg = get_config()
    print(f"Config initialized successfully: {cfg.to_dict()}")