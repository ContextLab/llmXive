import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from logger import get_logger, info, warning, error

@dataclass
class Config:
    """Configuration container for the project."""
    seed: int = 42
    data_path: str = "data"
    output_path: str = "data/derived"
    raw_data_path: str = "data/raw"
    derived_data_path: str = "data/derived"
    figures_path: str = "figures"
    log_level: str = "INFO"

    def __post_init__(self):
        # Ensure paths are Path objects
        self.data_path = Path(self.data_path)
        self.output_path = Path(self.output_path)
        self.raw_data_path = Path(self.raw_data_path)
        self.derived_data_path = Path(self.derived_data_path)
        self.figures_path = Path(self.figures_path)

_config_instance: Optional[Config] = None

def load_config_from_env() -> Config:
    """Load configuration from environment variables with defaults."""
    global _config_instance
    if _config_instance is not None:
        return _config_instance

    seed = int(os.getenv("PROJECT_SEED", "42"))
    data_path = os.getenv("PROJECT_DATA_PATH", "data")
    output_path = os.getenv("PROJECT_OUTPUT_PATH", "data/derived")
    raw_data_path = os.getenv("PROJECT_RAW_DATA_PATH", "data/raw")
    derived_data_path = os.getenv("PROJECT_DERIVED_DATA_PATH", "data/derived")
    figures_path = os.getenv("PROJECT_FIGURES_PATH", "figures")
    log_level = os.getenv("PROJECT_LOG_LEVEL", "INFO")

    config = Config(
        seed=seed,
        data_path=data_path,
        output_path=output_path,
        raw_data_path=raw_data_path,
        derived_data_path=derived_data_path,
        figures_path=figures_path,
        log_level=log_level,
    )
    _config_instance = config
    return config

def save_config_to_json(config: Config, path: Path) -> None:
    """Save configuration to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "seed": config.seed,
        "data_path": str(config.data_path),
        "output_path": str(config.output_path),
        "raw_data_path": str(config.raw_data_path),
        "derived_data_path": str(config.derived_data_path),
        "figures_path": str(config.figures_path),
        "log_level": config.log_level,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    info(f"Configuration saved to {path}")

def load_config_from_json(path: Path) -> Config:
    """Load configuration from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        data = json.load(f)
    config = Config(
        seed=data.get("seed", 42),
        data_path=data.get("data_path", "data"),
        output_path=data.get("output_path", "data/derived"),
        raw_data_path=data.get("raw_data_path", "data/raw"),
        derived_data_path=data.get("derived_data_path", "data/derived"),
        figures_path=data.get("figures_path", "figures"),
        log_level=data.get("log_level", "INFO"),
    )
    global _config_instance
    _config_instance = config
    return config

def get_config() -> Config:
    """Get the current configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config_from_env()
    return _config_instance

def set_config(config: Config) -> None:
    """Set the configuration instance explicitly."""
    global _config_instance
    _config_instance = config

def set_random_seed(seed: Optional[int] = None) -> None:
    """Set the random seed for reproducibility."""
    if seed is None:
        config = get_config()
        seed = config.seed
    import numpy as np
    import random
    random.seed(seed)
    np.random.seed(seed)
    info(f"Random seed set to {seed}")

def main() -> None:
    """Main entry point for configuration testing."""
    logger = get_logger(__name__)
    logger.info("Testing configuration loading...")
    config = get_config()
    logger.info(f"Loaded config: seed={config.seed}, data_path={config.data_path}")
    set_random_seed(config.seed)
    logger.info("Configuration test completed successfully.")

if __name__ == "__main__":
    main()