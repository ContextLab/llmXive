from __future__ import annotations

import logging
import os
import random
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    """Global configuration container."""
    seed: int = 42
    log_level: int = logging.INFO
    data_dir: str = "data"
    code_dir: str = "code"
    output_dir: str = "data/model"
    figures_dir: str = "figures"
    cache_dir: str = "data/cache"
    project_name: str = "statistical-analysis-of-code-complexity"

    def __post_init__(self):
        # Ensure directories exist
        for d in [self.data_dir, self.code_dir, self.output_dir, self.figures_dir, self.cache_dir]:
            os.makedirs(d, exist_ok=True)

_config: Optional[Config] = None

def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def set_random_seed(seed: int | None = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_config().seed
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: numpy and torch seeds are set in their respective modules if needed

def get_seed() -> int:
    """Get the current random seed."""
    return get_config().seed

def get_log_level() -> int:
    """Get the current logging level."""
    return get_config().log_level
