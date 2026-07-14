import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis

logger = logging.getLogger(__name__)

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return {"baseline": {"datasets": []}}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(filepath: str) -> pd.DataFrame:
    """Load a dataset from the processed directory."""
    return pd.read_csv(filepath)

def generate_null_dataset(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Generate a null dataset by shuffling the outcome variable."""
    pin_random_seed(seed)
    df_null = df.copy()
    
    # Assume 'value' is the outcome variable
    if 'value' in df_null.columns:
        df_null['value'] = np.random.permutation(df_null['value'].values)
    
    # If 'dependent_var' exists, shuffle that
    if 'dependent_var' in df_null.columns:
        df_null['dependent_var'] = np.random.permutation(df_null['dependent_var'].values)
    
    return df_null

def estimate_fpr_for_dataset(df: pd.DataFrame, dataset_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate false positive rate for a single dataset via permutation."""
    results = {
        "dataset": dataset_name,
        "fpr_t_test": 0.0,
        "fpr_regression": 0.0,
        "significance_threshold": 0.05
    }
    
    # Generate multiple null datasets and test
    n_permutations = 100
    sig_threshold = 0.05
    
    t_test_sig_count = 0
    reg_sig_count = 0
    
    for i in range(n_permutations):
        df_null = generate_null_dataset(df, seed=42+i)
        result = run_baseline_analysis(df=df_null, dataset_name=f"{dataset_name}_null_{i}", config=config)
        
        if result and result.get('t_test'):
            if result['t_test'].get('p_value', 1.0) <= sig_threshold:
                t_test_sig_count += 1
        
        if result and result.get('regression'):
            if result['regression'].get('p_values', {}).get('slope', 1.0) <= sig_threshold:
                reg_sig_count += 1
    
    results['fpr_t_test'] = t_test_sig_count / n_permutations
    results['fpr_regression'] = reg_sig_count / n_permutations
    
    return results

def write_output(results: List[Dict[str, Any]], output_file: str):
    """Write FPR results to JSON file."""
    output_data = {"null_fpr_metrics": {"datasets": results}}
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Null FPR metrics written to {output_file}")

def main():
    setup_logging("INFO")
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/raw") # Use raw for source
    output_file = os.path.join(processed_dir.replace("raw", "processed"), "null_fpr_metrics.json")
    
    # Load datasets from raw directory
    datasets = []
    if os.path.exists(processed_dir):
        for f in os.listdir(processed_dir):
            if f.endswith('.csv'):
                datasets.append(os.path.join(processed_dir, f))
    
    if not datasets:
        logger.warning("No datasets found for null FPR estimation.")
        # Write empty result
        write_output([], output_file)
        return 0
    
    all_results = []
    for ds_path in datasets:
        ds_name = os.path.basename(ds_path).replace('.csv', '')
        logger.info(f"Estimating FPR for {ds_name}")
        df = load_dataset_from_processed(ds_path)
        result = estimate_fpr_for_dataset(df, ds_name, config)
        all_results.append(result)
    
    write_output(all_results, output_file)
    return 0

if __name__ == "__main__":
    sys.exit(main())