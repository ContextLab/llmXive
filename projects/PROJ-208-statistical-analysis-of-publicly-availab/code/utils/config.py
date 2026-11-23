import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import yaml

class Config:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "random_seed": 42,
            "paths": {
                "raw_data": "data/raw/github_issues_raw_api.parquet",
                "cleaned_data": "data/processed/cleaned_issues.csv",
                "repo_metadata": "data/processed/repo_metadata.json",
                "outlier_report": "data/processed/outlier_report.json",
                "distribution_metrics": "data/processed/distribution_metrics.json",
                "hypothesis_results": "data/processed/hypothesis_results.json",
                "mixed_effects_results": "data/processed/mixed_effects_results.json",
                "collinearity_results": "data/processed/collinearity_results.json",
                "sensitivity_results": "data/processed/sensitivity_analysis.json",
                "figures_dir": "data/figures",
                "logs_dir": "data/logs"
            },
            "thresholds": {
                "completeness": 0.95,
                "vif_collinearity": 5,
                "outlier_iqr_multiplier": 1.5,
                "label_frequency_threshold": 0.01
            },
            "api": {
                "rate_limit_wait": 60,
                "max_retries": 5,
                "timeout": 30
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

_global_config: Optional[Config] = None

def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_path(name: str) -> Path:
    """Get a path from the configuration."""
    path_str = get_config().get(f"paths.{name}")
    if not path_str:
        raise ValueError(f"Path '{name}' not found in config")
    return Path(path_str)

def get_threshold(name: str) -> float:
    """Get a threshold value from the configuration."""
    val = get_config().get(f"thresholds.{name}")
    if val is None:
        raise ValueError(f"Threshold '{name}' not found in config")
    return float(val)

def get_api_config() -> Dict[str, Any]:
    """Get API configuration."""
    return get_config().get("api", {})

def save_config(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save configuration to file."""
    save_path = path or Path("config.yaml")
    with open(save_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)
