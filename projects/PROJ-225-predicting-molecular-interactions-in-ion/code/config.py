import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Custom Exceptions
class DataIngestionError(Exception):
    pass

class ModelTrainingError(Exception):
    pass

class AnalysisError(Exception):
    pass

# Configuration Defaults
SEED = 42
MAX_TRIALS = 60
TRIAL_TIMEOUT = 300
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

DATA_PATHS = {
    'raw': 'data/raw',
    'processed': 'data/processed',
    'validation': 'data/validation',
    'models': 'models'
}

HYPERPARAM_BOUNDS = {
    'n_estimators': (50, 500),
    'max_depth': (3, 10),
    'learning_rate': (0.01, 0.3)
}

def load_config() -> Dict[str, Any]:
    """Load configuration from environment or defaults."""
    config = {
        'SEED': int(os.getenv('SEED', SEED)),
        'MAX_TRIALS': int(os.getenv('MAX_TRIALS', MAX_TRIALS)),
        'TRIAL_TIMEOUT': int(os.getenv('TRIAL_TIMEOUT', TRIAL_TIMEOUT)),
        'DATA_PATHS': DATA_PATHS
    }
    
    # Validate required env keys if needed
    required_keys = ['SPICE_URL'] # Example
    for key in required_keys:
        if not os.getenv(key):
            logger.warning(f"Environment variable {key} is not set.")
            
    return config

if __name__ == "__main__":
    print(f"Config loaded: {load_config()}")
