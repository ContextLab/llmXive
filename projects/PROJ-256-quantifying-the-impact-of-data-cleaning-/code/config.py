import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    """Configuration management class."""

    def __init__(self):
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", ""),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "PERMUTATION_ITERATIONS": int(os.getenv("PERMUTATION_ITERATIONS", "100")),
            "BASELINE_METRICS_PATH": os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"),
            "CLEANED_METRICS_PATH": os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"),
            "NULL_FPR_METRICS_PATH": os.getenv("NULL_FPR_METRICS_PATH", "data/processed/null_fpr_metrics.json"),
            "outcome_col": os.getenv("outcome_col", "outcome"),
            "group_col": os.getenv("group_col", "group"),
        }

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value

    # Logger-style no-op methods for compatibility with various call sites
    def info(self, *args, **kwargs):
        pass
    def debug(self, *args, **kwargs):
        pass
    def warning(self, *args, **kwargs):
        pass
    def error(self, *args, **kwargs):
        pass
    def critical(self, *args, **kwargs):
        pass

def get_config() -> Config:
    return Config()

def reload_config():
    load_dotenv(override=True)
    return get_config()

def main():
    pass

if __name__ == "__main__":
    pass
