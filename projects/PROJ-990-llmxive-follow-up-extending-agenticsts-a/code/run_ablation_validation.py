import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

from ablation import load_trajectories, simulate_ablation_engine, generate_ablation_config, run_ablation_study
from config import load_config_from_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('llmXive.run_ablation_validation')

def main():
    """
    T008b: Generate Ground Truth Labels (Validation).
    
    Logic:
    1. Verify 'data/processed/validation_set.csv' exists and is non-empty.
    2. Execute run_ablation_study on the 'validation' dataset split.
    3. Output: 'data/processed/ablation_labels_validation.json'.
    """
    logger.info("Starting T008b: Generate Ground Truth Labels (Validation).")
    
    # 1. Verify Input
    config = load_config_from_file('config.json')
    input_path = Path(config['data']['processed']) / 'validation_set.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Dependency T014a (Splitter) has not produced validation_set.csv.")
        raise FileNotFoundError(f"Required input file missing: {input_path}")
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        raise
    
    if df.empty:
        logger.error(f"Input file {input_path} is empty.")
        raise ValueError(f"Validation set is empty. Cannot generate ablation labels.")
    
    logger.info(f"Input validated: {len(df)} rows in validation_set.csv.")
    
    # 2. Execute Ablation Study
    # The function run_ablation_study is defined in ablation.py and expects the dataset name (without '_set')
    # to construct the path internally or via config.
    # Based on T008 implementation, it calls load_trajectories('ablation_train') which looks for 'ablation_train_set.csv'.
    # Here we need to run on 'validation', so it will look for 'validation_set.csv'.
    
    try:
        run_ablation_study('validation')
        logger.info("Ablation study on validation set completed successfully.")
    except Exception as e:
        logger.error(f"Ablation study failed: {e}")
        raise

if __name__ == '__main__':
    main()