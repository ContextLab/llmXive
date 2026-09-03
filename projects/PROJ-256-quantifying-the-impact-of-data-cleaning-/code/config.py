import os
from typing import Any, Dict, Optional

class Config:
    """
    Configuration manager acting as a single source of truth for paths and parameters.
    Implements __getattr__ to tolerate arbitrary attribute access (logger-style calls).
    """
    def __init__(self):
        self._config: Dict[str, Any] = {
            "DATASET_URLS": {
                "uci_har": "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip",
                "uci_shopper": "https://archive.ics.uci.edu/ml/machine-learning-databases/00395/uci-shopper-data.zip"
            },
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "output"),
            "FIGURES_PATH": os.getenv("FIGURES_PATH", "output/figures"),
            "REPORTS_PATH": os.getenv("REPORTS_PATH", "output/reports"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "OUTLIER_K": float(os.getenv("OUTLIER_K", "1.5")),
            "SIGNIFICANCE_THRESHOLD": float(os.getenv("SIGNIFICANCE_THRESHOLD", "0.05")),
            "MISSINGNESS_BINS": [0.0, 0.05, 0.10, 1.0],
            "SIZE_BINS": [(0, 50), (50, 200), (200, float('inf'))]
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        # Tolerate logger-style calls (e.g., config.info(), config.debug())
        if name.startswith('_'):
            raise AttributeError(name)
        
        # Check if it's a direct config key
        if name in self._config:
            return self._config[name]
        
        # Return a no-op callable for any other attribute access
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

# Global instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    global _config_instance
    _config_instance = Config()
    return _config_instance
