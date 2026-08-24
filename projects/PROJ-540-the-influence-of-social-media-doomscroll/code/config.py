import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import yaml
import numpy as np

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path("config.yaml")
    
    if not config_path.exists():
        # Default config if file missing
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            'random_seed': 42,
            'paths': {
                'raw_data': Path('data/raw/ingested_data.csv'),
                'processed_data': Path('data/processed/analysis_data.csv'),
                'correlation_results': Path('outputs/correlation_results.json'),
                'regression_results': Path('outputs/regression_results.json'),
                'robustness_results': Path('outputs/robustness_results.json'),
                'plot': Path('outputs/plot.png'),
                'final_report': Path('outputs/final_report.md')
            },
            'dataset_url': 'https://raw.githubusercontent.com/plotly/datasets/master/tips.csv' # Placeholder, overridden by env or specific task
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure paths are Path objects
    if 'paths' in config:
        for k, v in config['paths'].items():
            if isinstance(v, str):
                config['paths'][k] = Path(v)
    
    return config

def set_seed(seed: Optional[int]) -> None:
    """Set the random seed for reproducibility."""
    if seed is None:
        logger.warning("Random seed not set. Results may not be reproducible.")
        return
    
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed set to: {seed}")

def verify_and_apply_seed(config: Dict[str, Any]) -> int:
    """Verify seed is set and apply it. Returns the seed used."""
    seed = config.get('random_seed')
    if seed is None:
        logger.warning("No random seed configured in config. Setting to default 42.")
        seed = 42
    
    set_seed(seed)
    log_seed_status(seed)
    return seed

def log_seed_status(seed: int) -> None:
    """Log the seed status."""
    logger.info(f"Reproducibility Seed Applied: {seed}")

def get_dataset_url(config: Dict[str, Any]) -> str:
    """Get the dataset URL from config or environment."""
    url = os.getenv('DATASET_URL')
    if url:
        return url
    
    url = config.get('dataset_url')
    if url:
        return url
    
    # Fallback to a known public dataset if none configured
    # Using a realistic placeholder that returns JSON/CSV
    return "https://raw.githubusercontent.com/plotly/datasets/master/tips.csv"

def ensure_directories(*paths: Path) -> None:
    """Ensure all directories for the given paths exist."""
    for p in paths:
        parent = p.parent if p.is_file() else p
        parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {parent}")