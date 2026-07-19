"""Global configuration and seeding management."""
import os
import random
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import numpy as np
import torch

class Config:
    """
    Global configuration holder.
    
    Provides paths, seeding, and other project-wide settings.
    Designed to be tolerant of missing attributes to prevent crashes
    in partially initialized states.
    """
    def __init__(self):
        # Define default paths
        self.root_dir = Path(os.getenv("PROJECT_ROOT", "."))
        self.data_raw = self.root_dir / "data" / "raw"
        self.data_processed = self.root_dir / "data" / "processed"
        self.data_results = self.root_dir / "data" / "results"
        self.code_dir = self.root_dir / "code"
        
        # Specific paths for bias check
        self.exclusion_log_path = self.data_processed / "exclusion_log.json"
        self.bias_report_path = self.data_results / "bias_report.json"
        
        # Configuration for filtering
        self.min_family_size = 5
        
        # Paths dictionary for flexible access
        self.paths = {
            "data_raw": self.data_raw,
            "data_processed": self.data_processed,
            "data_results": self.data_results,
            "exclusion_log": self.exclusion_log_path,
            "bias_report": self.bias_report_path
        }

        # Seeding defaults
        self.seed = 42
        self.cpu_limit = None

    def set_seed(self, seed: int = 42) -> None:
        """Set global random seeds for reproducibility."""
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def get_available_memory(self) -> float:
        """Get available memory in GB (placeholder for actual implementation)."""
        # In a real implementation, this would query the OS
        return 16.0

    # Tolerant attribute access for paths
    def __getattr__(self, name: str) -> Any:
        # If a specific attribute is requested that doesn't exist,
        # check if it's a path key in the paths dict
        if name in self.paths:
            return self.paths[name]
        # Fallback to default behavior (raises AttributeError)
        raise AttributeError(f"'Config' object has no attribute '{name}'")

_GLOBAL_CONFIG: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = Config()
    return _GLOBAL_CONFIG

def set_global_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = config