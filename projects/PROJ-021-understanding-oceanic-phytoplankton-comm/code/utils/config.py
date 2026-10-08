import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class Config:
    """Configuration manager for the project."""
    project_root: Path = field(default_factory=lambda: Path(os.getcwd()))
    data_root: Path = field(default_factory=lambda: Path("data"))
    code_root: Path = field(default_factory=lambda: Path("code"))
    specs_root: Path = field(default_factory=lambda: Path("specs"))
    state_root: Path = field(default_factory=lambda: Path("state"))
    
    # Hyperparameters and limits
    memory_limit_gb: float = 7.0
    runtime_limit_hours: float = 6.0
    random_seed: int = 42
    
    # Dataset specific
    min_temporal_overlap_years: int = 10
    missing_value_threshold_pct: float = 5.0
    
    # Model specific
    rf_max_trees: int = 500
    vlm_patience: int = 3
    vlm_fallback_threshold: float = 0.05 # R2 difference threshold for fallback logic

    def get_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the project root."""
        return self.project_root / relative_path

_config: Optional[Config] = None

def get_config() -> Config:
    global _config
    if _config is None:
        # Try to load from environment or defaults
        _config = Config()
        if "MEMORY_LIMIT_GB" in os.environ:
            _config.memory_limit_gb = float(os.environ["MEMORY_LIMIT_GB"])
        if "RUNTIME_LIMIT_HOURS" in os.environ:
            _config.runtime_limit_hours = float(os.environ["RUNTIME_LIMIT_HOURS"])
        if "RANDOM_SEED" in os.environ:
            _config.random_seed = int(os.environ["RANDOM_SEED"])
    return _config

def reset_config():
    global _config
    _config = None

def get_available_ram_gb() -> float:
    """Estimate available RAM (simple fallback if psutil not available)."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed, using default memory limit.")
        return get_config().memory_limit_gb

def main():
    """Test configuration loading."""
    cfg = get_config()
    logger.info(f"Config loaded: {asdict(cfg)}")

if __name__ == "__main__":
    main()