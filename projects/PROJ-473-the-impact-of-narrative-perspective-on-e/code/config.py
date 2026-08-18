import os
import numpy as np
import logging

def get_config():
    """
    Return configuration dictionary for paths, seeds, and hyperparameters.
    """
    config = {
        'primary_matching_threshold': 0.30,
        'gold_standard_annotations_path': 'data/raw/gold_standard_annotations.csv',
        'random_seed': 42,
        'log_dir': 'data/logs',
        'processed_dir': 'data/processed',
        'raw_dir': 'data/raw',
        'artifacts_dir': 'data/artifacts'
    }
    
    # Set random seed
    np.random.seed(config['random_seed'])
    
    # Setup logging
    os.makedirs(config['log_dir'], exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(config['log_dir'], 'pipeline.log')),
            logging.StreamHandler()
        ]
    )
    
    return config