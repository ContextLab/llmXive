"""
Configuration management for llmXive research pipeline.

Handles seeds, paths, and threshold configurations.
"""
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class Config:
    """Centralized configuration holder."""

    def __init__(self, config_path: Optional[Path] = None):
        self.root_dir = Path(__file__).parent.parent
        self.code_dir = self.root_dir / "code"
        self.data_dir = self.root_dir / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.held_out_dir = self.data_dir / "held_out"
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.held_out_dir.mkdir(parents=True, exist_ok=True)

        # Default paths for specific data
        self.traces_dir = self.raw_dir
        self.features_path = self.processed_dir / "feature_matrix.csv"
        self.scores_path = self.processed_dir / "per_trace_scores.csv"
        self.rules_dir = self.processed_dir / "rules"

        # Random seed for reproducibility
        self.seed = 42
        os.environ["PYTHONHASHSEED"] = str(self.seed)

        # Thresholds
        self.fidelity_threshold = 0.90  # 90% fidelity required for compression
        self.max_tree_depth = 5         # CPU-tractable limit for rule induction

        # Load optional YAML config if provided
        if config_path and config_path.exists():
            self._load_yaml(config_path)

    def _load_yaml(self, path: Path) -> None:
        """Load overrides from a YAML configuration file."""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
        except Exception as e:
            print(f"Warning: Could not load config from {path}: {e}")

# Singleton instance for convenience
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
