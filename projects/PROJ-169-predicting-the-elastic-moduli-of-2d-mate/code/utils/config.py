import os
import random
from pathlib import Path
from typing import Optional
import numpy as np

class Config:
    """Centralized configuration management."""
    
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
        self._setup_paths()
        
    def _setup_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        if 'CUDA_VISIBLE_DEVICES' not in os.environ:
            os.environ['CUDA_VISIBLE_DEVICES'] = ''
            
    def _setup_paths(self):
        """Initialize project paths."""
        self.code_dir = self.project_root / 'code'
        self.data_dir = self.project_root / 'data'
        self.tests_dir = self.project_root / 'tests'
        self.specs_dir = self.project_root / 'specs'
        
        # Ensure directories exist
        for d in [self.data_dir, self.data_dir / 'processed', 
                  self.data_dir / 'results', self.tests_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
    @property
    def device(self):
        return 'cpu'
