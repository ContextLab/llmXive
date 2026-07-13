"""
Configuration management for the llmXive weather analysis pipeline.

Loads hyperparameters, paths, seeds, and enforces the 6-hour compute limit.
Supports environment variable overrides and YAML configuration files.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import random
import numpy as np
import time

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

@dataclass
class Config:
    """
    Central configuration holder for the pipeline.
    """
    # Paths
    data_raw_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "raw")
    data_processed_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "processed")
    outputs_plots_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "outputs" / "plots")
    outputs_metrics_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "outputs" / "metrics")
    state_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "state")
    logs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    
    # Hyperparameters
    seed: int = 42
    max_missing_ratio: float = 0.15  # 15%
    max_gap_days: int = 30
    percentile_threshold: float = 0.90  # Default for POT
    
    # Compute Limits
    wall_clock_budget_seconds: int = 6 * 3600  # 6 hours default
    time_check_interval_seconds: int = 60
    fallback_time_threshold_seconds: int = 2 * 3600  # 2 hours before subsampling
    
    # Model Specifics
    gpd_fitting_method: str = "mle"  # 'mle', 'pwm', 'mm'
    spatial_model_type: str = "gaussian_copula"
    cross_validation_strategy: str = "loso"  # Leave-One-Station-Out
    
    # Environment overrides
    def __post_init__(self):
        self._apply_env_overrides()
    
    def _apply_env_overrides(self):
        """Override config values with environment variables if present."""
        env_mappings = {
            "WALL_CLOCK_BUDGET_SECONDS": "wall_clock_budget_seconds",
            "SEED": "seed",
            "MAX_MISSING_RATIO": "max_missing_ratio",
            "PERCENTILE_THRESHOLD": "percentile_threshold",
            "DATA_RAW_DIR": "data_raw_dir",
            "DATA_PROCESSED_DIR": "data_processed_dir",
        }
        
        for env_key, attr_name in env_mappings.items():
            if env_key in os.environ:
                val = os.environ[env_key]
                if attr_name in ["wall_clock_budget_seconds", "seed"]:
                    setattr(self, attr_name, int(val))
                elif attr_name in ["max_missing_ratio", "percentile_threshold"]:
                    setattr(self, attr_name, float(val))
                elif "DIR" in attr_name:
                    setattr(self, attr_name, Path(val))
        
        # Ensure directories exist
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create directories if they don't exist."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.outputs_plots_dir,
            self.outputs_metrics_dir,
            self.state_dir,
            self.logs_dir
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)

    def check_time_budget(self, start_time: float) -> bool:
        """
        Check if the wall-clock time budget has been exceeded.
        
        Args:
            start_time: The time the process started (from time.time())
        
        Returns:
            True if within budget, False if exceeded.
        """
        elapsed = time.time() - start_time
        return elapsed < self.wall_clock_budget_seconds

    def should_trigger_fallback(self, start_time: float) -> bool:
        """
        Check if the process should trigger fallback logic (e.g., subsampling).
        
        Returns:
            True if estimated time suggests we will hit the hard limit.
        """
        elapsed = time.time() - start_time
        return elapsed > self.fallback_time_threshold_seconds

    def load_from_yaml(self, config_path: Optional[Path] = None) -> None:
        """
        Load configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML file. Defaults to PROJECT_ROOT/config.yaml
        """
        path = config_path or CONFIG_PATH
        if not path.exists():
            return
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        if data:
            for key, value in data.items():
                if hasattr(self, key):
                    # Handle path conversion
                    if isinstance(getattr(self, key), Path) and isinstance(value, str):
                        value = Path(value)
                    setattr(self, key, value)

# Global instance
config = Config()

# Load YAML if it exists
if CONFIG_PATH.exists():
    config.load_from_yaml()

def get_config() -> Config:
    """Return the global configuration instance."""
    return config

if __name__ == "__main__":
    # Basic validation script
    cfg = get_config()
    print(f"Configuration loaded successfully.")
    print(f"Data Raw Dir: {cfg.data_raw_dir}")
    print(f"Wall Clock Budget: {cfg.wall_clock_budget_seconds} seconds ({cfg.wall_clock_budget_seconds/3600:.1f} hours)")
    print(f"Seed: {cfg.seed}")
    print(f"Max Missing Ratio: {cfg.max_missing_ratio}")
    
    # Verify time check
    start = time.time() - 100  # Fake start time
    assert cfg.check_time_budget(start), "Time budget check failed on valid time"
    print("Time budget checks passed.")