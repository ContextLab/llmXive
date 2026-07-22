import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from logging_config import get_project_logger

logger = get_project_logger(__name__)

CONFIG_FILE = "config.yaml"

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        # Look for config in project root
        config_path = Path(CONFIG_FILE)
        if not config_path.exists():
            # Try relative to code directory
            config_path = Path(__file__).parent.parent / CONFIG_FILE
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config or {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def get_osf_urls(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Extract OSF URLs from configuration."""
    if config is None:
        config = load_config()
    return config.get('osf_urls', [])

def get_project_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """Extract project paths from configuration."""
    if config is None:
        config = load_config()
    
    paths_config = config.get('paths', {})
    base_path = Path(paths_config.get('base', '.'))
    
    return {
        'raw': base_path / paths_config.get('raw', 'data/raw'),
        'processed': base_path / paths_config.get('processed', 'data/processed'),
        'code': base_path / paths_config.get('code', 'code'),
        'tests': base_path / paths_config.get('tests', 'tests'),
        'state': base_path / paths_config.get('state', 'state')
    }

def get_analysis_settings(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract analysis settings from configuration."""
    if config is None:
        config = load_config()
    return config.get('analysis', {})

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate that configuration has required fields."""
    required = ['osf_urls']
    for field in required:
        if field not in config:
            logger.error(f"Missing required config field: {field}")
            return False
    return True

def create_default_config_file(output_path: Optional[str] = None) -> str:
    """Create a default configuration file."""
    if output_path is None:
        output_path = CONFIG_FILE
    
    default_config = {
        'osf_urls': [
            # Add initial OSF URLs here
        ],
        'paths': {
            'base': '.',
            'raw': 'data/raw',
            'processed': 'data/processed',
            'code': 'code',
            'tests': 'tests',
            'state': 'state'
        },
        'analysis': {
            'min_valid_datasets': 3,
            'random_seed': 42
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    
    logger.info(f"Created default config at {output_path}")
    return output_path

def get_config() -> Dict[str, Any]:
    """Get configuration, creating default if necessary."""
    config = load_config()
    if not config:
        config = create_default_config_file()
        config = load_config()
    return config
