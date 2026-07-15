"""
Central configuration for the self-improving LLM recursive architecture project.
Defines hyperparameters, safety constraints, and file paths.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
import random
import numpy as np
import torch

# ============================================================================
# Hyperparameters
# ============================================================================
@dataclass
class Hyperparameters:
    """Training hyperparameters."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    num_epochs: int = 1
    max_seq_length: int = 512
    weight_decay: float = 0.01
    warmup_steps: int = 100
    gradient_clip_val: float = 1.0
    
    def set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

# ============================================================================
# Constraints
# ============================================================================
@dataclass
class SafetyConstraints:
    """Safety and resource constraints for the self-improvement loop."""
    max_param_increase_ratio: float = 1.30  # ≤30% parameter increase
    max_ram_gb: float = 7.0
    max_training_time_seconds: int = 7200  # 2 hours per cycle
    max_total_time_seconds: int = 21600  # 6 hours total
    early_stop_degradation_threshold: float = 0.05  # 5% degradation triggers early stop
    max_retries: int = 2

# ============================================================================
# Path Definitions
# ============================================================================
@dataclass
class PathConfig:
    """File system paths."""
    # Base project root (assumed to be relative to where this script is run)
    project_root: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Data directories
    data_raw: str = os.path.join(project_root, "data", "raw")
    data_processed: str = os.path.join(project_root, "data", "processed")
    
    # Results and artifacts
    results_dir: str = os.path.join(project_root, "results")
    figures_dir: str = os.path.join(project_root, "figures")
    
    # Checkpoints
    checkpoints_dir: str = os.path.join(project_root, "checkpoints")
    
    # Logs
    logs_dir: str = os.path.join(project_root, "logs")
    
    # Specific output files
    trajectory_file: str = os.path.join(results_dir, "trajectory.json")
    trade_off_file: str = os.path.join(results_dir, "trade_off_analysis.json")
    bootstrap_results_file: str = os.path.join(results_dir, "bootstrap_results.json")
    decay_fit_file: str = os.path.join(results_dir, "decay_fit.json")
    
    # Ensure directories exist
    def ensure_dirs(self):
        """Create all required directories if they don't exist."""
        for path in [
            self.data_raw, self.data_processed, self.results_dir,
            self.figures_dir, self.checkpoints_dir, self.logs_dir
        ]:
            os.makedirs(path, exist_ok=True)

# ============================================================================
# Global Configuration Instance
# ============================================================================
config = Hyperparameters()
constraints = SafetyConstraints()
paths = PathConfig()

# ============================================================================
# Utility Functions
# ============================================================================
def get_config_summary() -> dict:
    """Return a dictionary summary of current configuration."""
    return {
        "hyperparameters": {
            "learning_rate": config.learning_rate,
            "batch_size": config.batch_size,
            "seed": config.seed,
            "max_seq_length": config.max_seq_length,
        },
        "constraints": {
            "max_param_increase_ratio": constraints.max_param_increase_ratio,
            "max_ram_gb": constraints.max_ram_gb,
            "max_training_time_seconds": constraints.max_training_time_seconds,
            "early_stop_degradation_threshold": constraints.early_stop_degradation_threshold,
        },
        "paths": {
            "data_raw": paths.data_raw,
            "results_dir": paths.results_dir,
            "trajectory_file": paths.trajectory_file,
        }
    }