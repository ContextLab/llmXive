"""
Configuration Validator for llmXive Pipeline.
Implements T004.1: Verifies hyperparams.yaml existence and required keys.
Halts execution if validation fails.
"""
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_KEYS: Set[str] = {
    'seed',
    'paths',
    'memory',
    'reward',
    'training',
    'dataset',
    'statistics',
    'time',
    'verify'
}

REQUIRED_MEMORY_KEYS: Set[str] = {'max_ram_gb', 'batch_size', 'gradient_accumulation_steps'}
REQUIRED_REWARD_KEYS: Set[str] = {'epsilon', 'smoothing_type'}
REQUIRED_TRAINING_KEYS: Set[str] = {'learning_rate', 'max_steps'}

CONFIG_PATH = Path("config/hyperparams.yaml")

def load_config() -> Dict[str, Any]:
    """Load the YAML configuration file."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in {CONFIG_PATH}: {e}")
    
    if config is None:
        raise ValueError(f"Configuration file {CONFIG_PATH} is empty.")
    
    return config

def validate_structure(config: Dict[str, Any]) -> bool:
    """Validate top-level keys and nested structures."""
    missing_keys = REQUIRED_KEYS - set(config.keys())
    if missing_keys:
        raise ValueError(f"Missing required top-level keys in config: {missing_keys}")

    # Validate memory section
    memory_keys = REQUIRED_MEMORY_KEYS - set(config.get('memory', {}).keys())
    if memory_keys:
        raise ValueError(f"Missing required keys in 'memory' section: {memory_keys}")

    # Validate reward section
    reward_keys = REQUIRED_REWARD_KEYS - set(config.get('reward', {}).keys())
    if reward_keys:
        raise ValueError(f"Missing required keys in 'reward' section: {reward_keys}")

    # Validate training section
    training_keys = REQUIRED_TRAINING_KEYS - set(config.get('training', {}).keys())
    if training_keys:
        raise ValueError(f"Missing required keys in 'training' section: {training_keys}")

    # Validate epsilon is positive
    epsilon = config.get('reward', {}).get('epsilon')
    if epsilon is None or not isinstance(epsilon, (int, float)) or epsilon <= 0:
        raise ValueError(f"Reward 'epsilon' must be a positive number. Found: {epsilon}")

    # Validate batch_size is 1 (Hard Floor)
    batch_size = config.get('memory', {}).get('batch_size')
    if batch_size != 1:
        raise ValueError(f"Hard floor constraint violated: batch_size must be 1. Found: {batch_size}")

    return True

def validate_paths(config: Dict[str, Any]) -> bool:
    """Ensure required directories exist or can be created."""
    paths_config = config.get('paths', {})
    required_dirs = [
        paths_config.get('data_raw'),
        paths_config.get('data_processed'),
        paths_config.get('data_results'),
        paths_config.get('data_checkpoints'),
        paths_config.get('logs')
    ]

    for dir_path in required_dirs:
        if dir_path:
            full_path = Path(dir_path)
            full_path.mkdir(parents=True, exist_ok=True)
            if not full_path.exists():
                raise RuntimeError(f"Failed to create directory: {full_path}")
    
    return True

def validate_config() -> Dict[str, Any]:
    """Main entry point for validation. Raises on error."""
    logger.info(f"Validating configuration at {CONFIG_PATH}...")
    
    config = load_config()
    validate_structure(config)
    validate_paths(config)
    
    logger.info("Configuration validation successful.")
    return config

def main():
    """CLI entry point for validation."""
    try:
        config = validate_config()
        print(f"Validation passed. Loaded config with seed: {config['seed']}")
        return 0
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logger.error(f"Configuration validation FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())