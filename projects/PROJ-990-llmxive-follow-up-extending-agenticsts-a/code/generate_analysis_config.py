import os
import json
import logging
import random
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.generate_analysis_config')

PROCESSED_DIR = Path('data/processed')
OUTPUT_FILE = PROCESSED_DIR / 'analysis_config.json'

def load_split_metadata():
    """Load split metadata."""
    return {
        'train_ratio': 0.5,
        'ablation_train_ratio': 0.2,
        'validation_ratio': 0.15,
        'test_ratio': 0.15
    }

def load_ablation_config():
    """Load ablation config."""
    return {
        'seed': 42,
        'strategy': 'layer_removal'
    }

def generate_analysis_config():
    """Generate the analysis config file."""
    config = {
        'splits': load_split_metadata(),
        'ablation': load_ablation_config(),
        'seeds': {
            'random': 42,
            'numpy': 42
        },
        'timestamp': str(random.random()) # Just to make it unique per run if needed
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved analysis config to {OUTPUT_FILE}")

def main():
    generate_analysis_config()

if __name__ == '__main__':
    main()
