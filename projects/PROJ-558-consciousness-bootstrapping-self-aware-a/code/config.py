import os
from typing import Optional, Dict, Any
import torch

class ConfigurationError(Exception):
    pass

class Config:
    def __init__(self, **kwargs):
        self.seed = kwargs.get('seed', 42)
        self.batch_size = kwargs.get('batch_size', 8)
        self.recursion_depth = kwargs.get('recursion_depth', 2)
        self.learning_rate = kwargs.get('learning_rate', 1e-4)
        self.token_limit = kwargs.get('token_limit', 100000)
        self.max_length = kwargs.get('max_length', 512)
        self.epochs = kwargs.get('epochs', 1)
        self.use_recursive = kwargs.get('use_recursive', True)
        self.device = kwargs.get('device', 'cpu')
        self.data_path = kwargs.get('data_path', 'data/raw/pile_arxiv_truncated.json')
        
        # Enforce CPU-only
        if self.device != 'cpu':
            self.device = 'cpu'
            if not torch.cuda.is_available():
                self.device = 'cpu'
            else:
                # If user requested GPU but we enforce CPU
                self.device = 'cpu'

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __repr__(self):
        return f"Config(seed={self.seed}, batch_size={self.batch_size}, recursion_depth={self.recursion_depth}, ...)"

_global_config = None

def get_config():
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_config(**kwargs):
    global _global_config
    _global_config = Config(**kwargs)
    return _global_config

def validate_config(config: Config):
    if config.recursion_depth > 2:
        raise ConfigurationError(f"Recursion depth {config.recursion_depth} exceeds maximum allowed (2).")
    if config.batch_size < 1:
        raise ConfigurationError("Batch size must be at least 1.")
    if config.token_limit < 1:
        raise ConfigurationError("Token limit must be at least 1.")
    return True

def main():
    # Example usage
    cfg = get_config()
    print(cfg)
    validate_config(cfg)

if __name__ == "__main__":
    main()