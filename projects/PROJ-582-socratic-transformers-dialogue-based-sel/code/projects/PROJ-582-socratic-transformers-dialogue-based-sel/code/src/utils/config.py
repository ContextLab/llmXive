import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

@dataclass
class SocraticConfig:
    """
    Configuration for the Socratic Transformers project.
    
    This dataclass holds all project-wide settings including model paths,
    random seeds, and hyperparameters.
    """
    
    # Project paths
    project_root: str = field(
        default_factory=lambda: str(Path(__file__).parent.parent.parent.parent.parent)
    )
    data_root: str = field(default="data")
    
    # Model paths
    base_model_path: str = "meta-llama/Meta-Llama-3-8B"
    critic_model_path: str = "meta-llama/Meta-Llama-3-8B"
    
    # Random seeds
    seed: int = 42
    
    # Training parameters
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    max_seq_length: int = 512
    
    # Quantization settings
    use_4bit_quantization: bool = True
    use_double_quant: bool = True
    quant_type: str = "nf4"
    
    # Evaluation parameters
    eval_batch_size: int = 4
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Data parameters
    train_split: float = 0.8
    validation_split: float = 0.1
    test_split: float = 0.1
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    # Timeout settings (in seconds)
    training_timeout: int = 3600  # 1 hour
    generation_timeout: int = 600  # 10 minutes
    
    def __post_init__(self):
        """Validate and set up the configuration."""
        # Ensure paths are absolute
        self.project_root = str(Path(self.project_root).resolve())
        self.data_root = str(Path(self.project_root) / self.data_root)
        self.log_dir = str(Path(self.project_root) / self.log_dir)
    
    def set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        if torch.cuda.is_available():
            torch.manual_seed(self.seed)
            torch.cuda.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)
        os.environ['PYTHONHASHSEED'] = str(self.seed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_') and not callable(v)
        }

# Global config instance
_global_config: Optional[SocraticConfig] = None

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        SocraticConfig: Configuration object with values from environment.
    """
    config = SocraticConfig()
    
    # Override with environment variables if set
    if os.getenv('BASE_MODEL_PATH'):
        config.base_model_path = os.getenv('BASE_MODEL_PATH')
    if os.getenv('CRITIC_MODEL_PATH'):
        config.critic_model_path = os.getenv('CRITIC_MODEL_PATH')
    if os.getenv('RANDOM_SEED'):
        config.seed = int(os.getenv('RANDOM_SEED'))
    if os.getenv('BATCH_SIZE'):
        config.batch_size = int(os.getenv('BATCH_SIZE'))
    if os.getenv('NUM_EPOCHS'):
        config.num_epochs = int(os.getenv('NUM_EPOCHS'))
    
    return config

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    
    Returns:
        SocraticConfig: The global configuration.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config

def set_global_config(config: SocraticConfig):
    """
    Set the global configuration instance.
    
    Args:
        config: The configuration to set as global.
    """
    global _global_config
    _global_config = config

def ensure_directories():
    """Create necessary directories for the project."""
    config = get_config()
    
    directories = [
        config.data_root,
        os.path.join(config.data_root, 'raw'),
        os.path.join(config.data_root, 'processed'),
        os.path.join(config.data_root, 'results'),
        config.log_dir
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def init_project():
    """Initialize the project with configuration and directories."""
    config = get_config()
    config.set_seed()
    ensure_directories()

# Import torch here to avoid circular imports
import torch