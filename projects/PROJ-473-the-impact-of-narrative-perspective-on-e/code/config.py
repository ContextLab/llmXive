import os
import numpy as np

def get_config():
    """
    Get project configuration: paths, seeds, hyperparameters.
    """
    config = {
        'random_seed': 42,
        'paths': {
            'data_raw': 'data/raw',
            'data_processed': 'data/processed',
            'data_artifacts': 'data/artifacts',
            'logs': 'data/logs'
        },
        'hyperparameters': {
            'min_words': 50,
            'similarity_threshold': 0.3,
            'k_matches': 3
        }
    }
    
    # Set seed
    np.random.seed(config['random_seed'])
    
    # Ensure directories exist
    for path in config['paths'].values():
        os.makedirs(path, exist_ok=True)
    
    return config
