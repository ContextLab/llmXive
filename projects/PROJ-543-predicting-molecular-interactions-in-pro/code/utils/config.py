"""
Environment configuration management for molecular interaction prediction.

Handles random seeds, hyperparameters, and environment variables to ensure
reproducibility and centralized configuration management.
"""

import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import torch

# Default hyperparameters aligned with project requirements
DEFAULT_SEED = 42
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# GNN Hyperparameters
DEFAULT_HIDDEN_DIM = 256
DEFAULT_NUM_LAYERS = 3
DEFAULT_DROPOUT = 0.1
DEFAULT_LEARNING_RATE = 1e-3
DEFAULT_WEIGHT_DECAY = 1e-5

# Training Hyperparameters
DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_EPOCHS = 100
DEFAULT_EARLY_STOPPING_PATIENCE = 10
DEFAULT_MAX_TRAINING_TIME_HOURS = 4

# Data Hyperparameters
DEFAULT_RESOLUTION_THRESHOLD = 2.5  # Angstroms
DEFAULT_DISTANCE_CUTOFF = 5.0  # Angstroms for edges
DEFAULT_WATER_DISTANCE_CUTOFF = 3.5  # Angstroms for water detection

# Clustering Hyperparameters
DEFAULT_DBSCAN_EPS = 0.5
DEFAULT_DBSCAN_MIN_SAMPLES = 5

# Statistical Validation Hyperparameters
DEFAULT_FDR_ALPHA = 0.05
DEFAULT_PERMUTATION_ITERATIONS = 1000

@dataclass
class Hyperparameters:
    """Centralized hyperparameter container."""
    
    # Reproducibility
    seed: int = DEFAULT_SEED
    
    # Device
    device: str = DEFAULT_DEVICE
    
    # GNN Architecture
    hidden_dim: int = DEFAULT_HIDDEN_DIM
    num_layers: int = DEFAULT_NUM_LAYERS
    dropout: float = DEFAULT_DROPOUT
    
    # Optimization
    learning_rate: float = DEFAULT_LEARNING_RATE
    weight_decay: float = DEFAULT_WEIGHT_DECAY
    batch_size: int = DEFAULT_BATCH_SIZE
    
    # Training Control
    max_epochs: int = DEFAULT_MAX_EPOCHS
    early_stopping_patience: int = DEFAULT_EARLY_STOPPING_PATIENCE
    max_training_time_hours: float = DEFAULT_MAX_TRAINING_TIME_HOURS
    
    # Data Processing
    resolution_threshold: float = DEFAULT_RESOLUTION_THRESHOLD
    distance_cutoff: float = DEFAULT_DISTANCE_CUTOFF
    water_distance_cutoff: float = DEFAULT_WATER_DISTANCE_CUTOFF
    
    # Clustering
    dbscan_eps: float = DEFAULT_DBSCAN_EPS
    dbscan_min_samples: int = DEFAULT_DBSCAN_MIN_SAMPLES
    
    # Statistical Validation
    fdr_alpha: float = DEFAULT_FDR_ALPHA
    permutation_iterations: int = DEFAULT_PERMUTATION_ITERATIONS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert hyperparameters to dictionary."""
        return {
            "seed": self.seed,
            "device": self.device,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "batch_size": self.batch_size,
            "max_epochs": self.max_epochs,
            "early_stopping_patience": self.early_stopping_patience,
            "max_training_time_hours": self.max_training_time_hours,
            "resolution_threshold": self.resolution_threshold,
            "distance_cutoff": self.distance_cutoff,
            "water_distance_cutoff": self.water_distance_cutoff,
            "dbscan_eps": self.dbscan_eps,
            "dbscan_min_samples": self.dbscan_min_samples,
            "fdr_alpha": self.fdr_alpha,
            "permutation_iterations": self.permutation_iterations,
        }

@dataclass
class EnvironmentConfig:
    """Environment and path configuration."""
    
    # Project paths
    project_root: str = field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    data_raw_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "data", "raw"))
    data_processed_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "data", "processed"))
    data_results_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "data", "results"))
    data_reference_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "data", "reference"))
    code_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "code"))
    tests_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "tests"))
    specs_dir: str = field(default_factory=lambda: os.path.join(os.environ.get("PROJECT_ROOT", ""), "specs"))
    
    # Paths with defaults if env vars not set
    def __post_init__(self):
        root = os.environ.get("PROJECT_ROOT", self.project_root)
        self.data_raw_dir = os.path.join(root, "data", "raw")
        self.data_processed_dir = os.path.join(root, "data", "processed")
        self.data_results_dir = os.path.join(root, "data", "results")
        self.data_reference_dir = os.path.join(root, "data", "reference")
        self.code_dir = os.path.join(root, "code")
        self.tests_dir = os.path.join(root, "tests")
        self.specs_dir = os.path.join(root, "specs")
        
        # Ensure directories exist
        for dir_path in [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_results_dir,
            self.data_reference_dir,
        ]:
            os.makedirs(dir_path, exist_ok=True)

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_config() -> tuple:
    """Get default configuration objects.
    
    Returns:
        Tuple of (Hyperparameters, EnvironmentConfig)
    """
    hyperparams = Hyperparameters()
    env_config = EnvironmentConfig()
    return hyperparams, env_config

def load_config_from_env() -> tuple:
    """Load configuration from environment variables.
    
    Environment variables take precedence over defaults.
    
    Returns:
        Tuple of (Hyperparameters, EnvironmentConfig)
    """
    # Get defaults
    hyperparams, env_config = get_config()
    
    # Override with environment variables if set
    if "SEED" in os.environ:
        hyperparams.seed = int(os.environ["SEED"])
    if "DEVICE" in os.environ:
        hyperparams.device = os.environ["DEVICE"]
    if "HIDDEN_DIM" in os.environ:
        hyperparams.hidden_dim = int(os.environ["HIDDEN_DIM"])
    if "NUM_LAYERS" in os.environ:
        hyperparams.num_layers = int(os.environ["NUM_LAYERS"])
    if "DROPOUT" in os.environ:
        hyperparams.dropout = float(os.environ["DROPOUT"])
    if "LEARNING_RATE" in os.environ:
        hyperparams.learning_rate = float(os.environ["LEARNING_RATE"])
    if "BATCH_SIZE" in os.environ:
        hyperparams.batch_size = int(os.environ["BATCH_SIZE"])
    if "MAX_EPOCHS" in os.environ:
        hyperparams.max_epochs = int(os.environ["MAX_EPOCHS"])
    if "EARLY_STOPPING_PATIENCE" in os.environ:
        hyperparams.early_stopping_patience = int(os.environ["EARLY_STOPPING_PATIENCE"])
    if "RESOLUTION_THRESHOLD" in os.environ:
        hyperparams.resolution_threshold = float(os.environ["RESOLUTION_THRESHOLD"])
    if "DISTANCE_CUTOFF" in os.environ:
        hyperparams.distance_cutoff = float(os.environ["DISTANCE_CUTOFF"])
    
    return hyperparams, env_config

def initialize_environment(seed: Optional[int] = None) -> Hyperparameters:
    """Initialize the environment with seed and return hyperparameters.
    
    Args:
        seed: Optional seed override. If None, uses config or default.
    
    Returns:
        Hyperparameters object with applied settings.
    """
    hyperparams, _ = load_config_from_env()
    
    if seed is not None:
        hyperparams.seed = seed
    
    set_seed(hyperparams.seed)
    return hyperparams
