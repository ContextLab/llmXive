import os
import numpy as np
import logging

# Configure basic logging for the config module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Hyperparameters ---
# Threshold for primary matching logic (used in T025)
PRIMARY_MATCHING_THRESHOLD = 0.30

# Other algorithmic parameters
MIN_WORDS = 50
SIMILARITY_THRESHOLD = 0.3
K_MATCHES = 3
PRONOUN_LIST_1ST = ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours']
PRONOUN_LIST_3RD = ['he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their', 'theirs']
TFIDF_STOP_WORDS = 'english'
SENSITIVITY_THRESHOLDS = [0.25, 0.30, 0.35, 0.40]

def get_config():
    """
    Get project configuration: paths, seeds, and hyperparameters.
    
    This function initializes the global random seed, ensures all required
    directories exist, and returns a dictionary containing all project
    configuration values used by the pipeline.
    
    Returns:
        dict: Configuration dictionary with keys:
            - random_seed (int): Seed for reproducibility
            - paths (dict): Paths to data directories
            - hyperparameters (dict): Algorithmic parameters
            - PRIMARY_MATCHING_THRESHOLD (float): Threshold for matching (T025)
    """
    config = {
        'random_seed': 42,
        'paths': {
            'data_raw': 'data/raw',
            'data_processed': 'data/processed',
            'data_artifacts': 'data/artifacts',
            'logs': 'data/logs',
            'figures': 'data/artifacts'  # For plots like regression_plot.png
        },
        'hyperparameters': {
            'min_words': MIN_WORDS,
            'similarity_threshold': SIMILARITY_THRESHOLD,
            'k_matches': K_MATCHES,
            'pronoun_list_1st': PRONOUN_LIST_1ST,
            'pronoun_list_3rd': PRONOUN_LIST_3RD,
            'tfidf_stop_words': TFIDF_STOP_WORDS,
            'sensitivity_thresholds': SENSITIVITY_THRESHOLDS
        }
    }
    
    # Set random seed for reproducibility
    np.random.seed(config['random_seed'])
    logger.info(f"Random seed set to {config['random_seed']}")
    
    # Ensure all required directories exist
    for path_name, path_value in config['paths'].items():
        os.makedirs(path_value, exist_ok=True)
        logger.debug(f"Ensured directory exists: {path_value}")
    
    logger.info("Configuration loaded successfully")
    return config