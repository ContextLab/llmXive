"""
Configuration management for the molecular reactivity prediction pipeline.

Handles random seed setting, device configuration, and hyperparameters.
Ensures reproducibility and CPU-only execution as per project constraints.
"""
import os
import random
import logging
from typing import Optional, Dict, Any

import numpy as np

# Try to import torch, but allow CPU-only environments where it might not be installed
# or where the user explicitly wants to avoid GPU dependencies for this specific run.
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not found. GPU/CUDA configuration will be skipped.")

# Configure logging for this module
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_SEED = 42
DEFAULT_DEVICE = "cpu"
DEFAULT_MAX_WORKERS = 4
DEFAULT_BATCH_SIZE = 32
DEFAULT_LEARNING_RATE = 1e-3
DEFAULT_NUM_EPOCHS = 100
DEFAULT_EARLY_STOPPING_PATIENCE = 10
DEFAULT_DROPOUT_RATE = 0.1

# Project root directory (assumes code/ is at project root level or one level down)
# We try to detect the root relative to this file
_current_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_current_dir) if os.path.basename(_current_dir) == "code" else _current_dir

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")
LOGS_DIR = os.path.join(ARTIFACTS_DIR, "logs")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RAW_DIR = os.path.join(DATA_DIR, "raw")
ASSETS_DIR = os.path.join(DATA_DIR, "assets")

class Config:
    """
    Central configuration class for the project.
    
    Attributes:
        seed (int): Random seed for reproducibility.
        device (str): Device to run computations on ('cpu' or 'cuda').
        batch_size (int): Batch size for training.
        learning_rate (float): Learning rate for optimizer.
        num_epochs (int): Maximum number of training epochs.
        early_stopping_patience (int): Patience for early stopping.
        dropout_rate (float): Dropout rate for regularization.
        max_workers (int): Maximum number of worker threads/processes.
    """
    
    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        device: str = DEFAULT_DEVICE,
        batch_size: int = DEFAULT_BATCH_SIZE,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        num_epochs: int = DEFAULT_NUM_EPOCHS,
        early_stopping_patience: int = DEFAULT_EARLY_STOPPING_PATIENCE,
        dropout_rate: float = DEFAULT_DROPOUT_RATE,
        max_workers: int = DEFAULT_MAX_WORKERS
    ):
        self.seed = seed
        self.device = device
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.early_stopping_patience = early_stopping_patience
        self.dropout_rate = dropout_rate
        self.max_workers = max_workers
        
        # Validate device
        self._validate_device()
        
        # Set seeds for reproducibility
        self._set_seeds()
        
        # Log configuration
        self._log_config()

    def _validate_device(self) -> None:
        """Validate the device setting."""
        if self.device not in ["cpu", "cuda"]:
            raise ValueError(f"Invalid device: {self.device}. Must be 'cpu' or 'cuda'.")
        
        if self.device == "cuda" and TORCH_AVAILABLE:
            if not torch.cuda.is_available():
                logger.warning("CUDA requested but not available. Falling back to CPU.")
                self.device = "cpu"
        elif self.device == "cuda" and not TORCH_AVAILABLE:
            raise RuntimeError("CUDA requested but PyTorch is not installed.")
        
        # Enforce CPU-only as per project constraints unless explicitly overridden
        if self.device != "cpu":
            logger.warning("Non-CPU device detected. Project constraints may require CPU-only execution.")

    def _set_seeds(self) -> None:
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        if TORCH_AVAILABLE and self.device == "cuda":
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(self.seed)
                torch.cuda.manual_seed_all(self.seed)  # if multi-GPU
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        
        # Ensure deterministic behavior where possible
        os.environ['PYTHONHASHSEED'] = str(self.seed)
        
        logger.info(f"Random seeds set to {self.seed}")

    def _log_config(self) -> None:
        """Log the current configuration."""
        logger.info("Configuration loaded:")
        logger.info(f"  Seed: {self.seed}")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  Batch Size: {self.batch_size}")
        logger.info(f"  Learning Rate: {self.learning_rate}")
        logger.info(f"  Num Epochs: {self.num_epochs}")
        logger.info(f"  Early Stopping Patience: {self.early_stopping_patience}")
        logger.info(f"  Dropout Rate: {self.dropout_rate}")
        logger.info(f"  Max Workers: {self.max_workers}")
        logger.info(f"  Project Root: {PROJECT_ROOT}")
        logger.info(f"  Data Dir: {DATA_DIR}")
        logger.info(f"  Artifacts Dir: {ARTIFACTS_DIR}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "seed": self.seed,
            "device": self.device,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "early_stopping_patience": self.early_stopping_patience,
            "dropout_rate": self.dropout_rate,
            "max_workers": self.max_workers,
            "project_root": PROJECT_ROOT,
            "data_dir": DATA_DIR,
            "artifacts_dir": ARTIFACTS_DIR
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary."""
        return cls(
            seed=config_dict.get("seed", DEFAULT_SEED),
            device=config_dict.get("device", DEFAULT_DEVICE),
            batch_size=config_dict.get("batch_size", DEFAULT_BATCH_SIZE),
            learning_rate=config_dict.get("learning_rate", DEFAULT_LEARNING_RATE),
            num_epochs=config_dict.get("num_epochs", DEFAULT_NUM_EPOCHS),
            early_stopping_patience=config_dict.get("early_stopping_patience", DEFAULT_EARLY_STOPPING_PATIENCE),
            dropout_rate=config_dict.get("dropout_rate", DEFAULT_DROPOUT_RATE),
            max_workers=config_dict.get("max_workers", DEFAULT_MAX_WORKERS)
        )

# Global default configuration instance
# This can be imported and used throughout the project
default_config = Config()

def get_config(seed: Optional[int] = None, device: Optional[str] = None) -> Config:
    """
    Get a configuration instance with optional overrides.
    
    Args:
        seed: Optional seed override.
        device: Optional device override.
        
    Returns:
        Config: New configuration instance.
    """
    kwargs = {}
    if seed is not None:
        kwargs["seed"] = seed
    if device is not None:
        kwargs["device"] = device
    
    return Config(**kwargs)

# Convenience function to ensure directories exist
def ensure_directories() -> None:
    """Create all necessary project directories if they don't exist."""
    dirs = [
        DATA_DIR,
        ARTIFACTS_DIR,
        LOGS_DIR,
        PROCESSED_DIR,
        RAW_DIR,
        ASSETS_DIR
    ]
    
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")

if __name__ == "__main__":
    # Test the configuration when run directly
    logging.basicConfig(level=logging.INFO)
    
    # Ensure directories exist
    ensure_directories()
    
    # Create and display config
    config = get_config(seed=42, device="cpu")
    print(f"Configuration: {config.to_dict()}")
    
    # Verify seeds are set
    print(f"Random seed test: {random.random()}")
    print(f"Numpy seed test: {np.random.random()}")
    
    if TORCH_AVAILABLE:
        print(f"Torch seed test: {torch.rand(1).item()}")