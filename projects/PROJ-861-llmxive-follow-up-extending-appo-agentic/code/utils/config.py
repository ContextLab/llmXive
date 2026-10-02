import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np

# Default configuration values
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes per task
DEFAULT_MAX_EXCLUSION_RATE = 0.10  # 10% exclusion threshold

class Config:
    """Configuration manager for the llmXive project."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
        
        # Set defaults
        self._config.setdefault('seed', 42)
        self._config.setdefault('device', 'cpu')
        self._config.setdefault('model_path', 'microsoft/phi-2')
        self._config.setdefault('epsilon', 1e-9)
        self._config.setdefault('task_timeout_seconds', DEFAULT_TIMEOUT_SECONDS)
        self._config.setdefault('max_exclusion_rate', DEFAULT_MAX_EXCLUSION_RATE)
        self._config.setdefault('static_input_path', 'data/processed/sampled_tasks.json')
        self._config.setdefault('static_output_path', 'data/processed/static_scores.json')
        self._config.setdefault('dynamic_input_path', 'data/processed/sampled_tasks.json')
        self._config.setdefault('dynamic_output_path', 'data/processed/dynamic_scores.json')
        self._config.setdefault('correlation_output_path', 'data/results/correlation_results.csv')
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
    def _apply_env_overrides(self):
        """Override config with environment variables if present."""
        env_mappings = {
            'LLMXIVE_SEED': 'seed',
            'LLMXIVE_DEVICE': 'device',
            'LLMXIVE_MODEL_PATH': 'model_path',
            'LLMXIVE_EPSILON': 'epsilon',
            'LLMXIVE_TIMEOUT_SECONDS': 'task_timeout_seconds',
            'LLMXIVE_MAX_EXCLUSION_RATE': 'max_exclusion_rate',
            'LLMXIVE_STATIC_INPUT': 'static_input_path',
            'LLMXIVE_STATIC_OUTPUT': 'static_output_path',
            'LLMXIVE_DYNAMIC_INPUT': 'dynamic_input_path',
            'LLMXIVE_DYNAMIC_OUTPUT': 'dynamic_output_path',
            'LLMXIVE_CORRELATION_OUTPUT': 'correlation_output_path',
        }
        
        for env_var, config_key in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                # Try to convert to appropriate type
                if config_key in ['seed', 'task_timeout_seconds']:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                elif config_key == 'max_exclusion_rate':
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                elif config_key == 'epsilon':
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                self._config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        self._config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()
    
    def validate(self) -> Tuple[bool, str]:
        """Validate the configuration."""
        # Check device
        if self._config['device'] not in ['cpu', 'cuda']:
            return False, f"Invalid device: {self._config['device']}. Must be 'cpu' or 'cuda'."
        
        # Check timeout
        if self._config['task_timeout_seconds'] <= 0:
            return False, "task_timeout_seconds must be positive."
        
        # Check exclusion rate
        if not (0 <= self._config['max_exclusion_rate'] <= 1):
            return False, "max_exclusion_rate must be between 0 and 1."
        
        return True, "Configuration is valid."

_global_config: Optional[Config] = None

def get_config(config_dict: Optional[Dict[str, Any]] = None) -> Config:
    """Get or create the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_dict)
    elif config_dict is not None:
        # Update existing config with new values
        for key, value in config_dict.items():
            _global_config.set(key, value)
    return _global_config

def reset_config():
    """Reset the global configuration."""
    global _global_config
    _global_config = None

def main():
    """Main entry point for configuration testing."""
    config = get_config()
    valid, message = config.validate()
    
    print(f"Configuration validation: {'PASSED' if valid else 'FAILED'}")
    print(f"Message: {message}")
    print("\nCurrent configuration:")
    for key, value in sorted(config.to_dict().items()):
        print(f"  {key}: {value}")
    
    return 0 if valid else 1

if __name__ == '__main__':
    sys.exit(main())