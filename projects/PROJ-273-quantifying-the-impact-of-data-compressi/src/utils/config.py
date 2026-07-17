"""
Configuration management for the llmXive gravitational wave compression pipeline.

Provides:
- Random seed pinning for reproducibility
- Centralized path management for project directories
- Environment variable overrides for CI/CD flexibility
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# Project Root Detection
# Assumes the project root is the parent of the 'src' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if not (_PROJECT_ROOT / "src").exists():
    # Fallback for testing environments where the script might be run from a different context
    _PROJECT_ROOT = Path.cwd()

# Default Configuration Values
DEFAULT_SEED = 42
DEFAULT_MAX_ATTEMPTS = 20
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_TARGET_EVENTS = 15
DEFAULT_MIN_VALID_EVENTS = 12

# Directory Structure Constants (relative to project root)
DIR_DATA_RAW = "data/raw"
DIR_DATA_INTERIM = "data/interim"
DIR_DATA_PROCESSED = "data/processed"
DIR_DATA_EXTERNAL = "data/external"
DIR_CODE_PROVENANCE = "code/provenance"
DIR_REPORTS = "reports"
DIR_FIGURES = "figures"

class Config:
    """
    Central configuration holder.
    Singleton pattern to ensure consistent state across the pipeline.
    """
    _instance: Optional['Config'] = None

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # 1. Random Seed Management
        self.seed = int(os.getenv("GW_COMP_SEED", DEFAULT_SEED))
        self._set_seed(self.seed)
        
        # 2. Pipeline Control Parameters
        self.max_attempts = int(os.getenv("GW_COMP_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS))
        self.timeout_seconds = int(os.getenv("GW_COMP_TIMEOUT", DEFAULT_TIMEOUT_SECONDS))
        self.target_events = int(os.getenv("GW_COMP_TARGET_EVENTS", DEFAULT_TARGET_EVENTS))
        self.min_valid_events = int(os.getenv("GW_COMP_MIN_VALID", DEFAULT_MIN_VALID_EVENTS))
        
        # 3. Path Management
        self.root = _PROJECT_ROOT
        self.paths: Dict[str, Path] = {}
        self._resolve_paths()
        
        self._initialized = True

    def _set_seed(self, seed: int) -> None:
        """Pin random seeds for numpy, random, and torch (if available)."""
        random.seed(seed)
        np.random.seed(seed)
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass  # PyTorch not installed, skip

    def _resolve_paths(self) -> None:
        """Resolve all project directories relative to the root."""
        self.paths["root"] = self.root
        self.paths["data_raw"] = self.root / DIR_DATA_RAW
        self.paths["data_interim"] = self.root / DIR_DATA_INTERIM
        self.paths["data_processed"] = self.root / DIR_DATA_PROCESSED
        self.paths["data_external"] = self.root / DIR_DATA_EXTERNAL
        self.paths["provenance"] = self.root / DIR_CODE_PROVENANCE
        self.paths["reports"] = self.root / DIR_REPORTS
        self.paths["figures"] = self.root / DIR_FIGURES
        
        # Ensure directories exist
        for p in self.paths.values():
            if p != self.root:
                p.mkdir(parents=True, exist_ok=True)

    @property
    def data_raw(self) -> Path:
        return self.paths["data_raw"]

    @property
    def data_interim(self) -> Path:
        return self.paths["data_interim"]

    @property
    def data_processed(self) -> Path:
        return self.paths["data_processed"]

    @property
    def data_external(self) -> Path:
        return self.paths["data_external"]

    @property
    def provenance(self) -> Path:
        return self.paths["provenance"]

    @property
    def reports(self) -> Path:
        return self.paths["reports"]

    @property
    def figures(self) -> Path:
        return self.paths["figures"]

    def get_path(self, key: str) -> Path:
        """Safely retrieve a path by key."""
        if key not in self.paths:
            raise KeyError(f"Unknown path key: {key}. Valid keys: {list(self.paths.keys())}")
        return self.paths[key]

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to a dictionary (excluding paths for JSON serialization if needed)."""
        return {
            "seed": self.seed,
            "max_attempts": self.max_attempts,
            "timeout_seconds": self.timeout_seconds,
            "target_events": self.target_events,
            "min_valid_events": self.min_valid_events,
            "paths": {k: str(v) for k, v in self.paths.items()}
        }

# Global instance for easy access
config = Config()

def get_config() -> Config:
    """Return the global configuration instance."""
    return config

def set_seed(seed: int) -> None:
    """Update the global seed and re-seed all libraries."""
    config.seed = seed
    config._set_seed(seed)

def ensure_directories() -> None:
    """Ensure all project directories exist (idempotent)."""
    config._resolve_paths()

if __name__ == "__main__":
    # Simple self-test to verify paths and seed
    cfg = get_config()
    print(f"Project Root: {cfg.root}")
    print(f"Seed: {cfg.seed}")
    print(f"Data Raw: {cfg.data_raw}")
    print(f"Data External: {cfg.data_external}")
    print("Directories verified.")
