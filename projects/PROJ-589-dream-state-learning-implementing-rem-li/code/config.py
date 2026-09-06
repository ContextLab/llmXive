import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import torch

class Config:
    """
    Centralized configuration for the Dream-State Learning pipeline.
    Handles hyperparameters, paths, seed management, and device enforcement.
    """
    
    def __init__(
        self,
        seed: int = 42,
        max_memory_gb: float = 6.0,
        max_batch_size: int = 32,
        max_grad_norm: float = 1.0,
        dtype: torch.dtype = torch.float32,
        device: Optional[str] = None,
        # Paths
        base_path: Optional[Path] = None,
        data_path: Optional[Path] = None,
        log_path: Optional[Path] = None,
        checkpoint_path: Optional[Path] = None,
        result_path: Optional[Path] = None,
        # Training parameters
        num_epochs: int = 3,
        learning_rate: float = 5e-5,
        warmup_steps: int = 10,
        dream_ratio: float = 0.25,
        entropy_threshold: float = 0.5,
        max_entropy_retries: int = 3,
        # Data parameters
        max_length: int = 512,
        mask_rate: float = 0.15,
        # Resource limits
        max_wall_clock_hours: float = 5.0,
        # Sensitivity analysis
        temperature_sweep_values: List[float] = None
    ):
        self.seed = seed
        self.max_memory_gb = max_memory_gb
        self.max_batch_size = max_batch_size
        self.max_grad_norm = max_grad_norm
        self.dtype = dtype
        
        # Device enforcement: CPU-only for CI compatibility
        if device is None:
            self.device = "cpu"
        else:
            self.device = device
        
        # Paths
        self.base_path = base_path or Path(__file__).parent.parent
        self.data_path = data_path or self.base_path / "data"
        self.log_path = log_path or self.data_path / "logs"
        self.checkpoint_path = checkpoint_path or self.data_path / "checkpoints"
        self.result_path = result_path or self.data_path / "results"
        
        # Training parameters
        self.num_epochs = num_epochs
        self.learning_rate = learning_rate
        self.warmup_steps = warmup_steps
        self.dream_ratio = dream_ratio
        self.entropy_threshold = entropy_threshold
        self.max_entropy_retries = max_entropy_retries
        
        # Data parameters
        self.max_length = max_length
        self.mask_rate = mask_rate
        
        # Resource limits
        self.max_wall_clock_hours = max_wall_clock_hours
        
        # Temperature sweep values
        self.temperature_sweep_values = temperature_sweep_values or [0.5, 0.7, 0.9]
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Set seeds
        self._set_seeds()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        dirs = [
            self.data_path,
            self.log_path,
            self.checkpoint_path,
            self.result_path,
            self.data_path / "raw",
            self.data_path / "results"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def _set_seeds(self) -> None:
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'seed': self.seed,
            'max_memory_gb': self.max_memory_gb,
            'max_batch_size': self.max_batch_size,
            'max_grad_norm': self.max_grad_norm,
            'dtype': str(self.dtype),
            'device': self.device,
            'base_path': str(self.base_path),
            'data_path': str(self.data_path),
            'log_path': str(self.log_path),
            'checkpoint_path': str(self.checkpoint_path),
            'result_path': str(self.result_path),
            'num_epochs': self.num_epochs,
            'learning_rate': self.learning_rate,
            'warmup_steps': self.warmup_steps,
            'dream_ratio': self.dream_ratio,
            'entropy_threshold': self.entropy_threshold,
            'max_entropy_retries': self.max_entropy_retries,
            'max_length': self.max_length,
            'mask_rate': self.mask_rate,
            'max_wall_clock_hours': self.max_wall_clock_hours,
            'temperature_sweep_values': self.temperature_sweep_values
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create Config from dictionary."""
        return cls(**config_dict)
