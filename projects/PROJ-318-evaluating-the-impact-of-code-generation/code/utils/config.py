import os
import torch
from typing import Optional, Tuple, Dict, Any
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "model_paths": {
        "codegen_mono": "Salesforce/codegen-350M-mono",
        "sentence_transformer": "sentence-transformers/all-MiniLM-L6-v2"
    },
    "rate_limits": {
        "max_retries": 3,
        "retry_delay_seconds": 2,
        "timeout_seconds": 30
    },
    "hardware": {
        "preferred_device": "cuda",
        "fallback_device": "cpu",
        "use_4bit_quantization": True,
        "max_memory_mb": 7000
    }
}

class ConfigException(Exception):
    """Custom exception for configuration errors."""
    pass

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.
    
    Args:
        config_path: Path to the config YAML file. If None, uses defaults.
        
    Returns:
        Dictionary containing configuration parameters.
        
    Raises:
        ConfigException: If the config file cannot be parsed or is invalid.
    """
    if config_path is None:
        logger.info("No config file provided, using defaults")
        return DEFAULT_CONFIG.copy()
    
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file {config_path} not found, using defaults")
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ConfigException("Config file must contain a YAML dictionary")
        
        # Merge with defaults to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        
        # Recursive merge for nested dicts
        for key, value in config.items():
            if key in DEFAULT_CONFIG and isinstance(value, dict) and isinstance(DEFAULT_CONFIG[key], dict):
                merged_config[key].update(value)
        
        logger.info(f"Loaded configuration from {config_path}")
        return merged_config
        
    except yaml.YAMLError as e:
        raise ConfigException(f"Failed to parse config file {config_path}: {e}")
    except Exception as e:
        raise ConfigException(f"Error loading config from {config_path}: {e}")

def get_device_and_dtype(config: Optional[Dict[str, Any]] = None) -> Tuple[torch.device, torch.dtype]:
    """
    Determine the device and dtype to use based on configuration and hardware availability.
    
    Args:
        config: Configuration dictionary. If None, loads defaults.
        
    Returns:
        Tuple of (device, dtype)
        
    Raises:
        ConfigException: If device configuration is invalid.
    """
    if config is None:
        config = load_config()
    
    hardware_cfg = config.get("hardware", DEFAULT_CONFIG["hardware"])
    preferred_device = hardware_cfg.get("preferred_device", "cuda")
    fallback_device = hardware_cfg.get("fallback_device", "cpu")
    use_4bit = hardware_cfg.get("use_4bit_quantization", True)
    
    # Determine device
    if preferred_device == "cuda":
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using CUDA device: {device}")
        else:
            device = torch.device(fallback_device)
            logger.warning(f"CUDA not available, falling back to {fallback_device}")
    elif preferred_device == "cpu":
        device = torch.device("cpu")
        logger.info("Using CPU device")
    else:
        raise ConfigException(f"Invalid preferred_device: {preferred_device}")
    
    # Determine dtype
    # 4-bit quantization typically uses float16 or bfloat16 if available
    if use_4bit:
        if device.type == "cuda" and torch.cuda.is_bf16_supported():
            dtype = torch.bfloat16
        elif device.type == "cuda":
            dtype = torch.float16
        else:
            # CPU usually uses float32 for stability with 4-bit quantization
            dtype = torch.float32
    else:
        dtype = torch.float32
    
    logger.info(f"Using device: {device}, dtype: {dtype}")
    return device, dtype

def validate_model_path(model_name: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Validate and resolve a model path.
    
    Args:
        model_name: The model identifier (e.g., "Salesforce/codegen-350M-mono" or a key from config).
        config: Configuration dictionary. If None, loads defaults.
        
    Returns:
        The resolved model path string.
        
    Raises:
        ConfigException: If the model path is invalid or not found in config.
    """
    if config is None:
        config = load_config()
    
    model_paths = config.get("model_paths", DEFAULT_CONFIG["model_paths"])
    
    # Check if model_name is a key in the config
    if model_name in model_paths:
        resolved_path = model_paths[model_name]
        logger.debug(f"Resolved model key '{model_name}' to '{resolved_path}'")
        return resolved_path
    
    # If it looks like a full path, validate it's not empty
    if model_name and isinstance(model_name, str) and model_name.strip():
        logger.debug(f"Using provided model path: {model_name}")
        return model_name
    
    raise ConfigException(f"Invalid or unknown model path: {model_name}")

def get_quantization_config(use_4bit: bool = True) -> Optional[Any]:
    """
    Create a HuggingFace BitsAndBytesConfig for 4-bit quantization.
    
    Args:
        use_4bit: Whether to enable 4-bit quantization.
        
    Returns:
        BitsAndBytesConfig instance if enabled, None otherwise.
    """
    if not use_4bit:
        return None
    
    try:
        from transformers import BitsAndBytesConfig
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16, # Default, might be overridden by get_device_and_dtype
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
    except ImportError:
        logger.warning("bitsandbytes not installed, 4-bit quantization disabled")
        return None

def get_rate_limit_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    Get rate limiting configuration parameters.
    
    Args:
        config: Configuration dictionary. If None, loads defaults.
        
    Returns:
        Dictionary with max_retries, retry_delay_seconds, timeout_seconds.
    """
    if config is None:
        config = load_config()
    
    return config.get("rate_limits", DEFAULT_CONFIG["rate_limits"])

def get_max_memory_mb(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the maximum memory limit in MB from configuration.
    
    Args:
        config: Configuration dictionary. If None, loads defaults.
        
    Returns:
        Maximum memory in MB.
    """
    if config is None:
        config = load_config()
    
    return config.get("hardware", DEFAULT_CONFIG["hardware"]).get("max_memory_mb", 7000)

# Example usage / entry point for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = load_config()
    device, dtype = get_device_and_dtype(cfg)
    print(f"Device: {device}, Dtype: {dtype}")
    print(f"Model Path (codegen_mono): {validate_model_path('codegen_mono', cfg)}")
    print(f"Rate Limits: {get_rate_limit_config(cfg)}")
    print(f"Max Memory: {get_max_memory_mb(cfg)} MB")