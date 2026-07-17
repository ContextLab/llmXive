import os
import random
from pathlib import Path
from typing import Optional
import numpy as np
import torch

class Config:
    """Centralized configuration management for reproducibility and environment setup.
    
    This class handles:
    - Random seed initialization (numpy, python random, torch)
    - Project path resolution
    - CPU thread limits
    - Device configuration (CPU-only enforced)
    """
    
    def __init__(
        self,
        seed: int = 42,
        project_root: Optional[Path] = None,
        cpu_limit: Optional[int] = None
    ):
        self.seed = seed
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.cpu_limit = cpu_limit
        
        self._setup_seed()
        self._setup_cpu_limits()
        self._setup_paths()
        self._setup_torch()
        
    def _setup_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
            
    def _setup_cpu_limits(self):
        """Set CPU thread limits to prevent resource exhaustion."""
        if self.cpu_limit is not None:
            os.environ['OMP_NUM_THREADS'] = str(self.cpu_limit)
            os.environ['MKL_NUM_THREADS'] = str(self.cpu_limit)
            torch.set_num_threads(self.cpu_limit)
            
    def _setup_paths(self):
        """Initialize project paths and ensure directories exist."""
        self.code_dir = self.project_root / 'code'
        self.data_dir = self.project_root / 'data'
        self.tests_dir = self.project_root / 'tests'
        self.specs_dir = self.project_root / 'specs'
        self.figures_dir = self.project_root / 'figures'
        
        # Ensure directories exist
        for d in [
            self.data_dir, 
            self.data_dir / 'raw',
            self.data_dir / 'processed', 
            self.data_dir / 'results', 
            self.tests_dir,
            self.figures_dir
        ]:
            d.mkdir(parents=True, exist_ok=True)
            
    def _setup_torch(self):
        """Configure PyTorch for CPU-only execution."""
        # Force CPU usage as per project constraints
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        torch.set_default_device('cpu')
        
    @property
    def device(self):
        """Return the computation device (always CPU for this project)."""
        return torch.device('cpu')
        
    def get_path(self, relative_path: str) -> Path:
        """Get an absolute path relative to the project root.
        
        Args:
            relative_path: Path relative to project root
            
        Returns:
            Absolute Path object
        """
        return self.project_root / relative_path
        
    def __repr__(self) -> str:
        return (
            f"Config(seed={self.seed}, "
            f"project_root={self.project_root}, "
            f"cpu_limit={self.cpu_limit}, "
            f"device={self.device})"
        )
