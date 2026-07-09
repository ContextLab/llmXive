import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from utils.logging import get_logger

logger = get_logger(__name__)

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "code/config.yaml"
        self.config = self._load_config()
        
        # Default values if not in config
        self._defaults = {
            "data_root": "data",
            "random_seed": 42,
            "event_window_days": 7,
            "control_window_days": 30,
            "anomaly_window_days": 30, # Added for T014
            "usgs_base_url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
            "min_magnitude": 4.0,
            "max_depth_km": 70,
            "test_event_count": 12,
            "test_region": "Alaska",
            "deviations_path": "docs/deviations.md"
        }

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, self._defaults.get(key, default))

# Global config instance
_config = Config()

def get_data_path() -> Path:
    return Path(_config.get("data_root", "data"))

def get_processed_path() -> Path:
    return get_data_path() / "processed"

def get_event_window_days() -> int:
    return _config.get("event_window_days", 7)

def get_control_window_days() -> int:
    return _config.get("control_window_days", 30)

def get_random_seed() -> int:
    return _config.get("random_seed", 42)

def get_usgs_base_url() -> str:
    return _config.get("usgs_base_url", "https://earthquake.usgs.gov/fdsnws/event/1/query")

def get_min_magnitude() -> float:
    return _config.get("min_magnitude", 4.0)

def get_max_depth_km() -> int:
    return _config.get("max_depth_km", 70)

def get_test_event_count() -> int:
    return _config.get("test_event_count", 12)

def get_test_region() -> str:
    return _config.get("test_region", "Alaska")

def get_deviations_path() -> str:
    return _config.get("deviations_path", "docs/deviations.md")

def get_anomaly_window_days() -> int:
    """
    Returns the window size for calculating pressure anomalies.
    Defaults to 30 days as per spec's 'sufficient duration' requirement.
    """
    return _config.get("anomaly_window_days", 30)

# Helper to set random seed
def set_random_seed(seed: Optional[int] = None):
    s = seed if seed is not None else get_random_seed()
    random.seed(s)
    np.random.seed(s)
    logger.info(f"Random seed set to {s}")

if __name__ == "__main__":
    # Basic test
    print(f"Data Path: {get_data_path()}")
    print(f"Event Window: {get_event_window_days()} days")
    print(f"Anomaly Window: {get_anomaly_window_days()} days")
    print(f"Config loaded from: {_config.config_path}")
