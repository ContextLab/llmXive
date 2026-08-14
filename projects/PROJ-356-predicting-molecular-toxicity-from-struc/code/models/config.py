from typing import Dict, Any

class ModelConfig:
    """Configuration container for model hyperparameters."""
    def __init__(self, config_dict: Dict[str, Any] = None):
        self.config = config_dict or {}
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
