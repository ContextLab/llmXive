"""
Configuration management for the feature importance drift analysis pipeline.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration container for the pipeline."""
    data_dir: Path = field(default_factory=lambda: Path("data"))
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    log_level: str = "INFO"
    window_size_days: int = 30
    model_params: Dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42
    })
    min_r_squared: float = 0.8
    n_permutation_resamples: int = 1000
    block_size: int = 5

_config: Optional[Config] = None


def get_config() -> Config:
    """Get the singleton configuration instance."""
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config


def reset_config() -> None:
    """Reset the configuration to defaults (useful for testing)."""
    global _config
    _config = None


def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
    log_level = os.getenv("LOG_LEVEL", "INFO")
    window_size = int(os.getenv("WINDOW_SIZE_DAYS", "30"))
    min_r2 = float(os.getenv("MIN_R_SQUARED", "0.8"))
    n_resamples = int(os.getenv("N_PERMUTATION_RESAMPLES", "1000"))
    block_sz = int(os.getenv("BLOCK_SIZE", "5"))

    return Config(
        data_dir=data_dir,
        output_dir=output_dir,
        log_level=log_level,
        window_size_days=window_size,
        min_r_squared=min_r2,
        n_permutation_resamples=n_resamples,
        block_size=block_sz
    )


def main() -> None:
    """Main entry point for configuration module (testing)."""
    config = get_config()
    print(f"Configuration loaded:")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  Output Dir: {config.output_dir}")
    print(f"  Log Level: {config.log_level}")
    print(f"  Window Size: {config.window_size_days} days")
    print(f"  Min R²: {config.min_r_squared}")
