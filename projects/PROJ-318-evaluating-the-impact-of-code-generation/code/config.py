import os
import logging
import random
import numpy as np
from typing import Optional, Dict, Any
import torch
import yaml
from pathlib import Path

# Set up logging for this module
logger = logging.getLogger(__name__)

class ConfigException(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Centralized environment configuration management.
    Defines model paths, rate limits, and other runtime settings.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from a YAML file or environment variables.
        
        Args:
            config_path: Path to the YAML configuration file. If None, 
                         attempts to load from environment variables or defaults.
        """
        self._config: Dict[str, Any] = {}
        self._load_from_yaml(config_path)
        self._load_from_env()
        self._set_defaults()
        self._validate()

    def _load_from_yaml(self, config_path: Optional[str]) -> None:
        """Load configuration from a YAML file if provided."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                raise ConfigException(f"Failed to load config from {config_path}: {e}")
        else:
            logger.info("No YAML config provided, using environment/defaults.")

    def _load_from_env(self) -> None:
        """Override configuration with environment variables if present."""
        env_mapping = {
            'CODEGEN_MODEL_PATH': 'model_path',
            'CODEGEN_MAX_RETRIES': 'rate_limit_retries',
            'CODEGEN_TIMEOUT': 'api_timeout',
            'CODEGEN_LOG_LEVEL': 'log_level',
            'HF_TOKEN': 'huggingface_token',
            'DATA_DIR': 'data_dir',
            'STATE_DIR': 'state_dir',
            'LOGS_DIR': 'logs_dir',
        }

        for env_key, config_key in env_mapping.items():
            value = os.getenv(env_key)
            if value is not None:
                # Attempt to parse as int/float if the existing value is numeric
                if config_key in self._config and isinstance(self._config[config_key], (int, float)):
                    try:
                        self._config[config_key] = type(self._config[config_key])(value)
                    except ValueError:
                        self._config[config_key] = value
                else:
                    self._config[config_key] = value
                logger.debug(f"Overrode {config_key} from environment variable {env_key}")

    def _set_defaults(self) -> None:
        """Set default values for any missing configuration keys."""
        defaults = {
            'model_path': 'Salesforce/codegen-350M-mono',
            'rate_limit_retries': 5,
            'api_timeout': 30,
            'log_level': 'INFO',
            'huggingface_token': None,
            'data_dir': 'data',
            'state_dir': 'state',
            'logs_dir': 'logs',
            'seed': 42,
            'max_memory_mb': 7000,  # 7GB limit for RAM monitoring
            'quantization_bits': 4,
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
                logger.debug(f"Set default for {key}: {value}")

    def _validate(self) -> None:
        """Validate the configuration values."""
        if not isinstance(self._config['rate_limit_retries'], int) or self._config['rate_limit_retries'] < 1:
            raise ConfigException("rate_limit_retries must be a positive integer")
        
        if not isinstance(self._config['api_timeout'], (int, float)) or self._config['api_timeout'] <= 0:
            raise ConfigException("api_timeout must be a positive number")
        
        if self._config['max_memory_mb'] <= 0:
            raise ConfigException("max_memory_mb must be a positive integer")

    @property
    def model_path(self) -> str:
        return str(self._config['model_path'])

    @property
    def rate_limit_retries(self) -> int:
        return int(self._config['rate_limit_retries'])

    @property
    def api_timeout(self) -> int:
        return int(self._config['api_timeout'])

    @property
    def log_level(self) -> str:
        return str(self._config['log_level'])

    @property
    def huggingface_token(self) -> Optional[str]:
        return self._config.get('huggingface_token')

    @property
    def data_dir(self) -> Path:
        return Path(self._config['data_dir'])

    @property
    def state_dir(self) -> Path:
        return Path(self._config['state_dir'])

    @property
    def logs_dir(self) -> Path:
        return Path(self._config['logs_dir'])

    @property
    def seed(self) -> int:
        return int(self._config['seed'])

    @property
    def max_memory_mb(self) -> int:
        return int(self._config['max_memory_mb'])

    @property
    def quantization_bits(self) -> int:
        return int(self._config['quantization_bits'])

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def __repr__(self) -> str:
        # Hide sensitive keys in representation
        safe_config = {k: v for k, v in self._config.items() if k != 'huggingface_token'}
        return f"Config({safe_config})"

# Global config instance
_config_instance: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get or create the global configuration instance.
    
    Args:
        config_path: Optional path to a YAML config file.
                    
    Returns:
        The global Config instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility (Constitution Principle I).
    
    Args:
        seed: The seed value. If None, uses the seed from the global config.
    """
    cfg = get_config()
    effective_seed = seed if seed is not None else cfg.seed
    
    random.seed(effective_seed)
    np.random.seed(effective_seed)
    torch.manual_seed(effective_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(effective_seed)
    
    # For transformers
    os.environ['PYTHONHASHSEED'] = str(effective_seed)
    
    logger.info(f"Global random seeds set to {effective_seed}")

def configure_logging() -> None:
    """
    Configure the root logger based on the current config.
    """
    cfg = get_config()
    level = getattr(logging, cfg.log_level.upper(), logging.INFO)
    
    # Ensure logs directory exists
    cfg.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = cfg.logs_dir / 'pipeline.log'
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger.info(f"Logging configured: level={cfg.log_level}, file={log_file}")

def get_device_and_dtype() -> Tuple[str, torch.dtype]:
    """
    Determine the device and dtype based on availability and config.
    Returns:
        Tuple of (device_name, torch_dtype)
    """
    if torch.cuda.is_available():
        return "cuda", torch.float16
    elif torch.backends.mps.is_available():
        return "mps", torch.float16
    else:
        return "cpu", torch.float32

# Helper to load quantization config
def get_quantization_config(bits: int = 4) -> Optional['BitsAndBytesConfig']:
    """
    Create a BitsAndBytesConfig for quantization.
    
    Args:
        bits: Number of bits for quantization (4 or 8).
        
    Returns:
        BitsAndBytesConfig instance or None if quantization is not applicable.
    """
    try:
        from transformers import BitsAndBytesConfig
        
        if bits not in [4, 8]:
            raise ConfigException(f"Unsupported quantization bits: {bits}. Must be 4 or 8.")
        
        return BitsAndBytesConfig(
            load_in_4bit=(bits == 4),
            load_in_8bit=(bits == 8),
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
    except ImportError:
        logger.warning("bitsandbytes not installed, quantization config unavailable")
        return None

def get_rate_limit_config() -> Dict[str, int]:
    """
    Get rate limiting configuration.
    
    Returns:
        Dictionary with retry and timeout settings.
    """
    cfg = get_config()
    return {
        'max_retries': cfg.rate_limit_retries,
        'timeout': cfg.api_timeout,
    }

def get_max_memory_mb() -> int:
    """
    Get the maximum allowed memory in MB.
    
    Returns:
        Maximum memory in MB.
    """
    return get_config().max_memory_mb

# Verify imports work as expected
if __name__ == "__main__":
    # Basic verification script
    cfg = get_config()
    print(f"Config loaded successfully:")
    print(f"  Model Path: {cfg.model_path}")
    print(f"  Rate Limit Retries: {cfg.rate_limit_retries}")
    print(f"  Seed: {cfg.seed}")
    print(f"  Max Memory MB: {cfg.max_memory_mb}")
    
    set_global_seed()
    configure_logging()
    logger.info("Configuration verification complete.")