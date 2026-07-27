import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

from ablation import load_trajectories, simulate_ablation_engine, generate_ablation_config, run_ablation_study

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.ablation_validation')

def main():
    """
    Main entry point for T008b: Generate Ground Truth Labels (Validation).
    
    Logic:
    1. Verify `data/processed/validation_set.csv` exists and is non-empty.
    2. Execute `code/ablation.py` (run_ablation_study) on the 'validation' set.
    3. Output: `data/processed/ablation_labels_validation.json`.
    """
    logger.info("Starting T008b: Generate Ground Truth Labels (Validation).")
    
    # 1. Verify input exists and is non-empty
    config_path = Path('config.json')
    if not config_path.exists():
        # Fallback to default if config missing, though T004 should have created it
        processed_dir = Path('data/processed')
    else:
        from config import load_config_from_file
        config = load_config_from_file('config.json')
        processed_dir = Path(config['data']['processed'])
    
    input_file = processed_dir / 'validation_set.csv'
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"CRITICAL: Input file {input_file} does not exist. "
            "T014a (Splitter) must complete successfully before T008b can run."
        )
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise RuntimeError(f"Failed to read {input_file}: {e}")
    
    if df.empty:
        raise ValueError(
            f"CRITICAL: Input file {input_file} is empty. "
            "The validation set must contain at least 20 trajectories (FR-006)."
        )
    
    logger.info(f"Input validation passed. Found {len(df)} trajectories in {input_file}.")
    
    # 2. Execute ablation study on the 'validation' set
    # The run_ablation_study function expects the dataset_name (without '_set')
    # and constructs the path internally.
    try:
        run_ablation_study('validation')
        logger.info("T008b completed successfully.")
    except Exception as e:
        logger.error(f"Ablation study failed: {e}")
        raise

if __name__ == '__main__':
    main()