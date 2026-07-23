import logging
import os
import random
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

def load_environment_variables():
    """Load environment variables from .env file if present."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

def init_random_seed(seed: int = 42):
    """Initialize random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def setup_logging(level: int = logging.INFO):
    """Configure logging for the project."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/processed/pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

def get_logger(name: str):
    """Get a logger instance."""
    return logging.getLogger(name)
