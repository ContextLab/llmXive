import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import local modules
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis, load_datasets_from_raw
from config import get_config

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str) -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load baseline metrics: {e}")
        return None

def load_dataset_from_processed(filepath: str) -> Optional[pd.DataFrame]:
    """Load a dataset from the processed directory."""
    if not os.path.exists(filepath):
        logger.warning(f"Dataset file not found: {filepath}")
        return None
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return None

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable.
    This breaks the relationship between predictors and outcome.
    """
    pin_random_seed(seed)
    df_null = df.copy()
    # Shuffle the outcome column
    df_null[outcome_col] = np.random.permutation(df_null[outcome_col].values)
    return df_null

def estimate_fpr_for_dataset(
    df_null: pd.DataFrame, 
    dataset_name: str, 
    predictor_col: str, 
    outcome_col: str, 
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate for a single null dataset.
    Returns a dictionary with p-values and significance flags.
    """
    # Run analysis on the null dataset
    result = run_baseline_analysis(
        df_null, 
        dataset_name=dataset_name,
        predictor_col=predictor_col,
        outcome_col=outcome_col
    )
    
    fpr_entry = {
        'dataset': dataset_name,
        't_test': {},
        'regression': {},
        'significant_t_test': False,
        'significant_regression': False
    }
    
    if 't_test' in result and result['t_test']:
        p_val_t = result['t_test'].get('p_value')
        if p_val_t is not None:
            fpr_entry['t_test'] = result['t_test']
            fpr_entry['significant_t_test'] = p_val_t <= alpha
        
    if 'regression' in result and result['regression']:
        p_val_r = result['regression'].get('p_value')
        if p_val_r is not None:
            fpr_entry['regression'] = result['regression']
            fpr_entry['significant_regression'] = p_val_r <= alpha
    
    return fpr_entry

def write_output(results: List[Dict[str, Any]], output_path: str):
    """Write the FPR metrics to a JSON file."""
    output_data = {
        'metadata': {
            'type': 'permutation_null_fpr',
            'generated_at': str(datetime.now()),
            'alpha_threshold': 0.05,
            'description': 'False Positive Rate estimation via permutation null datasets'
        },
        'datasets': results
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Null FPR metrics written to {output_path}")

def main():
    """
    Main execution for T032: Permutation Null FPR Estimation.
    
    Strategy:
    1. Load existing raw datasets (or cleaned variants if available).
    2. For each dataset, generate N null datasets (shuffled outcome).
    3. Run analysis on each null dataset.
    4. Calculate proportion of tests with p <= 0.05 (FPR).
    5. Output to data/processed/null_fpr_metrics.json.
    """
    setup_logging()
    config = get_config()
    
    raw_dir = config.get('RAW_DATA_PATH', 'data/raw')
    output_path = os.path.join(config.get('PROCESSED_DATA_PATH', 'data/processed'), 'null_fpr_metrics.json')
    seed = config.get('RANDOM_SEED', 42)
    n_permutations = 10  # Number of permutations per dataset for speed
    
    logger.info(f"Starting T032: Permutation Null FPR Estimation")
    logger.info(f"Raw directory: {raw_dir}")
    logger.info(f"Output path: {output_path}")
    
    # Load datasets from raw directory
    datasets = load_datasets_from_raw(raw_dir)
    
    if not datasets:
        logger.warning("No datasets found in raw directory. Creating empty output.")
        write_output([], output_path)
        return

    all_fpr_results = []
    
    for item in datasets:
        df = item['df']
        dataset_name = item['name']
        
        # Identify columns if not standard 'group'/'outcome'
        # Heuristic: last column is outcome, a binary column is predictor
        cols = df.columns.tolist()
        # Try to find a binary column for predictor
        predictor_col = None
        outcome_col = None
        
        for col in cols:
            if df[col].nunique() == 2:
                predictor_col = col
                break
        
        # Default outcome is last column
        outcome_col = cols[-1]
        
        if predictor_col is None:
            # Fallback: use first column if not outcome
            predictor_col = cols[0] if cols[0] != outcome_col else cols[1]
        
        logger.info(f"Processing dataset: {dataset_name} (Predictor: {predictor_col}, Outcome: {outcome_col})")
        
        for i in range(n_permutations):
            null_seed = seed + i
            df_null = generate_null_dataset(df, outcome_col, null_seed)
            
            result = estimate_fpr_for_dataset(
                df_null, 
                f"{dataset_name}_null_{i}", 
                predictor_col, 
                outcome_col
            )
            all_fpr_results.append(result)
    
    write_output(all_fpr_results, output_path)
    logger.info("T032 completed successfully.")

if __name__ == '__main__':
    main()
