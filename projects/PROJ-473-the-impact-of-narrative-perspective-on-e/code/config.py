import os
import numpy as np
import logging

# Constants for paths
GOLD_STANDARD_ANNOTATIONS_PATH = "data/raw/gold_standard_annotations.csv"
PRIMARY_MATCHING_THRESHOLD = 0.30

def get_config():
    """
    Return configuration dictionary for paths, seeds, and hyperparameters.
    Initializes directories and logging.
    """
    config = {
        'primary_matching_threshold': PRIMARY_MATCHING_THRESHOLD,
        'gold_standard_annotations_path': GOLD_STANDARD_ANNOTATIONS_PATH,
        'random_seed': 42,
        'log_dir': 'data/logs',
        'processed_dir': 'data/processed',
        'raw_dir': 'data/raw',
        'artifacts_dir': 'data/artifacts',
        'figures_dir': 'data/artifacts',
        'extraction_log': 'data/logs/extraction.log',
        'matching_log': 'data/logs/matching.log'
    }
    
    # Set random seed for reproducibility
    np.random.seed(config['random_seed'])
    
    # Setup logging directory if it doesn't exist
    os.makedirs(config['log_dir'], exist_ok=True)
    os.makedirs(config['processed_dir'], exist_ok=True)
    os.makedirs(config['raw_dir'], exist_ok=True)
    os.makedirs(config['artifacts_dir'], exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(config['log_dir'], 'pipeline.log')),
            logging.StreamHandler()
        ]
    )
    
    return config