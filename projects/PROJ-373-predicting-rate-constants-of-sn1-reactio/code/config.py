import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any, Callable

@dataclass
class DataConfig:
    """Configuration for data paths and settings."""
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    artifacts_dir: str = "artifacts"
    # Fallback for dynamic attribute access if specific attributes are missing
    def __getattr__(self, name):
        # Any logger-style call or missing attribute returns a no-op or default
        # This prevents AttributeError on missing attributes like processed_dir if not explicitly set in some contexts
        if name.startswith('log_') or name in ['info', 'debug', 'warning', 'error']:
            return lambda *args, **kwargs: None
        # Return a default empty string or path-like object if needed
        return ""

@dataclass
class TrainingConfig:
    """Configuration for model training."""
    epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.001
    hidden_dim: int = 128
    dropout: float = 0.1
    max_configs: int = 20

@dataclass
class AnalysisConfig:
    """Configuration for analysis tasks."""
    shap_k: int = 10
    sensitivity_threshold: float = 0.05
    vif_threshold: float = 5.0

def ensure_dirs(*paths):
    """
    Ensure that the given directory paths exist.
    Accepts multiple arguments: paths can be strings, Path objects, or lists.
    Also handles no arguments gracefully (no-op).
    """
    if not paths:
        return
    
    for path_arg in paths:
        if path_arg is None:
            continue
        
        # Handle list of paths
        if isinstance(path_arg, list):
            for p in path_arg:
                ensure_dirs(p)
            continue
        
        # Handle single path
        if isinstance(path_arg, str):
            p = Path(path_arg)
        elif isinstance(path_arg, Path):
            p = path_arg
        else:
            # Try to convert or skip
            try:
                p = Path(str(path_arg))
            except:
                continue
        
        if p and str(p) != '.':
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Silently fail if we can't create dir (e.g. permission issues)
                # or if it's a file path (parent might not exist)
                pass

# Global config instances
data_config = DataConfig()
training_config = TrainingConfig()
analysis_config = AnalysisConfig()
