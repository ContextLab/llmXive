import os
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Any
from utils import setup_logging, init_random_seed, get_logger

logger = logging.getLogger(__name__)

def save_model_artifact(model, path: str):
    """Save model artifact."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def save_split_indices(splits: List[Dict], output_dir: str):
    """Save split indices."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for i, split in enumerate(splits):
        with open(f"{output_dir}/split_fold_{i}.pkl", 'wb') as f:
            pickle.dump(split, f)
    logger.info(f"Saved {len(splits)} splits to {output_dir}")

def main():
    init_random_seed(42)
    setup_logging()
    # Called by other scripts
    pass

if __name__ == "__main__":
    main()