import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

class Config:
    """Configuration class for the llmXive project."""
    
    def __init__(self):
        # Base paths
        self.project_root = Path(__file__).parent.parent
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.models_dir = self.project_root / "models"
        self.analysis_dir = self.project_root / "analysis"
        self.tests_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"
        self.logs_dir = self.project_root / "logs"
        
        # Data paths
        self.raw_data_path = self.data_dir / "raw"
        self.processed_data_path = self.data_dir / "processed"
        self.analysis_data_path = self.data_dir / "analysis"
        
        # Target cities for filtering (Chinese cities from TransitLM)
        self.target_cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
        
        # Model configuration
        self.max_sequence_length = 128
        self.batch_size = 32
        self.learning_rate = 1e-4
        self.num_epochs = 10
        
        # Random seed for reproducibility
        self.random_seed = 42
        
        # Vocabulary settings
        self.top_n_vocabulary = 5000
        self.unknown_token = "<UNKNOWN>"
        
        # Stratification thresholds
        self.short_route_threshold = 15
        self.medium_route_threshold = 30
        
        # Graph validation
        self.min_jaccard_index = 0.95
        
        # Performance thresholds
        self.validity_drop_threshold = 0.15  # 15% absolute drop
        self.significance_level = 0.05
        
        # Resource constraints
        self.memory_limit_gb = 14
        self.time_limit_seconds = 300

def get_env_config() -> Config:
    """Get configuration from environment or defaults."""
    config = Config()
    
    # Override with environment variables if present
    if os.getenv("TARGET_CITIES"):
        config.target_cities = os.getenv("TARGET_CITIES").split(",")
    
    if os.getenv("RANDOM_SEED"):
        config.random_seed = int(os.getenv("RANDOM_SEED"))
    
    if os.getenv("TOP_N_VOCABULARY"):
        config.top_n_vocabulary = int(os.getenv("TOP_N_VOCABULARY"))
    
    return config

def set_global_seed(seed: Optional[int] = None) -> None:
    """Set global random seeds for reproducibility."""
    if seed is None:
        config = get_env_config()
        seed = config.random_seed
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
