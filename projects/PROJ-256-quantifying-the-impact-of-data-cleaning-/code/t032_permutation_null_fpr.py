import argparse
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from analysis import generate_null_dataset, run_null_analysis, run_baseline_analysis
from utils import pin_random_seed, setup_logging
from config import get_config

logger = logging.getLogger(__name__)

def generate_null_fpr_metrics(
    raw_data_dir: str,
    outcome_col: str,
    group_col: str,
    k_thresholds: List[float] = [1.5, 2.0],
    n_permutations: int = 100
) -> Dict[str, Any]:
    """
    Generate null metrics by permuting outcome variable and running analysis.
    Computes FPR for each outlier threshold.
    """
    pin_random_seed(42)
    config = get_config()
    
    # Load datasets from raw_dir
    csv_files = list(Path(raw_data_dir).glob("*.csv"))
    if not csv_files:
        logger.error(f"No CSV files found in {raw_data_dir}")
        return {}
    
    null_metrics = {}
    
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        dataset_name = csv_file.stem
        logger.info(f"Processing null analysis for {dataset_name}")
        
        # Run permutations
        for k in k_thresholds:
            k_key = f"k_{k}"
            if k_key not in null_metrics:
                null_metrics[k_key] = {}
            
            significant_count = 0
            total_count = 0
            
            for i in range(n_permutations):
                seed = 42 + i
                df_null = generate_null_dataset(df, outcome_col, seed=seed)
                
                # Run analysis on null data
                # Note: We assume group_col exists in df_null
                metrics = run_null_analysis(
                    df_null,
                    outcome_col=outcome_col,
                    group_col=group_col,
                    k_threshold=k
                )
                
                if "error" in metrics:
                    continue
                
                p_val = metrics.get('t_test', {}).get('p_value')
                if p_val is not None:
                    total_count += 1
                    if p_val < 0.05:
                        significant_count += 1
            
            if total_count > 0:
                fpr = significant_count / total_count
                null_metrics[k_key][dataset_name] = {
                    "fpr": fpr,
                    "n_permutations": n_permutations,
                    "significant_count": significant_count,
                    "total_count": total_count
                }
            else:
                null_metrics[k_key][dataset_name] = {
                    "fpr": None,
                    "error": "no_valid_tests"
                }
    
    return null_metrics

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Null FPR Metrics")
    parser.add_argument("--raw_dir", type=str, default="data/raw", help="Directory with raw CSVs")
    parser.add_argument("--outcome", type=str, default="outcome", help="Outcome column name")
    parser.add_argument("--group", type=str, default="group", help="Group column name")
    parser.add_argument("--output", type=str, default="data/processed/null_fpr_metrics.json", help="Output file")
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging("INFO")
    
    logger.info("Starting Null FPR Analysis")
    
    null_metrics = generate_null_fpr_metrics(
        raw_data_dir=args.raw_dir,
        outcome_col=args.outcome,
        group_col=args.group,
        k_thresholds=[1.5, 2.0],
        n_permutations=100
    )
    
    save_path = args.output
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, 'w') as f:
        json.dump(null_metrics, f, indent=2, default=str)
    
    logger.info(f"Null FPR metrics written to {save_path}")

if __name__ == "__main__":
    main()
