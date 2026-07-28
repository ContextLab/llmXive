"""
Analysis module for sensitivity analysis and bias metrics.
Implements FR-005 (Sensitivity Analysis) and FR-004 (Multiplicity Correction).
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Import from project modules
from imputation_pipeline import (
    run_single_imputation_pipeline,
    run_mice_chains,
    pool_imputations,
    perform_complete_case_analysis,
    perform_single_mean_imputation
)
from config import SeedManager
from metrics.bias import calculate_percentage_bias

logger = logging.getLogger(__name__)

def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: str) -> None:
    """Save a dictionary to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def run_sensitivity_sweep(
    dataset_path: str,
    metadata_path: Optional[str],
    m_values: List[int],
    true_variance: Optional[float] = None,
    is_synthetic: bool = False
) -> List[Dict[str, Any]]:
    """
    Run a sensitivity analysis sweep over the number of imputations (m).
    
    Args:
        dataset_path: Path to the input dataset (CSV or Parquet).
        metadata_path: Path to the metadata JSON (for synthetic data).
        m_values: List of m values to test (e.g., [5, 10, 20]).
        true_variance: True variance for synthetic data (if available).
        is_synthetic: Whether the dataset is synthetic.
        
    Returns:
        List of results for each m value.
    """
    logger.info(f"Starting sensitivity sweep on {dataset_path} with m values: {m_values}")
    
    # Load data
    if dataset_path.endswith('.parquet'):
        df = pd.read_parquet(dataset_path)
    else:
        df = pd.read_csv(dataset_path)
        
    # Identify target variable (assume first numeric column with missingness)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    target_var = None
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            target_var = col
            break
            
    if target_var is None:
        logger.warning("No target variable with missingness found. Using first numeric column.")
        target_var = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]
        
    results = []
    
    # We need design variables for variance estimation if available
    has_design = all(col in df.columns for col in ['weight', 'psu', 'strata'])
    
    for m in m_values:
        logger.info(f"Running sweep for m={m}")
        
        # 1. Complete Case Analysis (Baseline)
        try:
            cc_result = perform_complete_case_analysis(df, target_var, has_design=has_design)
            cc_variance = cc_result.get('variance', 0.0)
        except Exception as e:
            logger.warning(f"CC analysis failed for m={m}: {e}")
            cc_variance = 0.0
            
        # 2. Single Mean Imputation
        try:
            single_result = perform_single_mean_imputation(df, target_var, has_design=has_design)
            single_variance = single_result.get('variance', 0.0)
        except Exception as e:
            logger.warning(f"Single imputation failed for m={m}: {e}")
            single_variance = 0.0
            
        # 3. MICE Imputation (m imputations)
        mice_variance = 0.0
        try:
            # Generate seeds for this m
            base_seed = 42
            seeds = [base_seed + i for i in range(m)]
            
            # Run MICE chains
            imputed_datasets = run_mice_chains(
                df,
                target_var,
                m=m,
                max_iter=1000,
                seeds=seeds
            )
            
            # Pool results
            pooled_result = pool_imputations(imputed_datasets, target_var, m=m)
            mice_variance = pooled_result.get('variance', 0.0)
            
        except Exception as e:
            logger.warning(f"MICE analysis failed for m={m}: {e}")
            mice_variance = 0.0
            
        # Calculate bias rates (if true_variance is known, e.g., synthetic)
        bias_rate = 0.0
        if true_variance and true_variance > 0:
            if cc_variance > 0:
                bias_rate = abs((cc_variance - true_variance) / true_variance)
            # Or we could use MICE variance for bias rate
            # bias_rate = abs((mice_variance - true_variance) / true_variance)
        
        result_entry = {
            "m_value": m,
            "cc_variance": cc_variance,
            "single_variance": single_variance,
            "mice_variance": mice_variance,
            "bias_rate": bias_rate,
            "std_dev": 0.0  # Will be calculated later
        }
        results.append(result_entry)
        
    # Calculate std_dev of bias rates across the sweep
    if true_variance:
        bias_rates = [r["bias_rate"] for r in results]
        if len(bias_rates) > 1:
            std_dev = float(np.std(bias_rates))
            for r in results:
                r["std_dev"] = std_dev
                
    return results

def run_sensitivity_sweep_real_data(
    dataset_path: str,
    m_values: List[int],
    output_path: str
) -> None:
    """
    Run sensitivity sweep on real data and save results.
    For real data, we focus on variance stability rather than bias rate.
    """
    logger.info(f"Running sensitivity sweep on real data: {dataset_path}")
    
    # Load data
    if dataset_path.endswith('.parquet'):
        df = pd.read_parquet(dataset_path)
    else:
        df = pd.read_csv(dataset_path)
        
    # Identify target variable
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    target_var = None
    for col in numeric_cols:
        if df[col].isnull().sum() > 0:
            target_var = col
            break
            
    if target_var is None:
        logger.warning("No target variable with missingness found.")
        return
        
    has_design = all(col in df.columns for col in ['weight', 'psu', 'strata'])
    
    results = []
    mice_variances = []
    
    for m in m_values:
        logger.info(f"Running sweep for m={m} on real data")
        
        # MICE Imputation
        mice_variance = 0.0
        try:
            base_seed = 42
            seeds = [base_seed + i for i in range(m)]
            
            imputed_datasets = run_mice_chains(
                df,
                target_var,
                m=m,
                max_iter=1000,
                seeds=seeds
            )
            
            pooled_result = pool_imputations(imputed_datasets, target_var, m=m)
            mice_variance = pooled_result.get('variance', 0.0)
            mice_variances.append(mice_variance)
            
        except Exception as e:
            logger.warning(f"MICE analysis failed for m={m}: {e}")
            mice_variances.append(0.0)
            
        result_entry = {
            "m_value": m,
            "mice_variance": mice_variance,
            "bias_rate": 0.0,  # Cannot calculate without true variance
            "std_dev": 0.0
        }
        results.append(result_entry)
        
    # Calculate std_dev of variances across the sweep
    if len(mice_variances) > 1:
        std_dev = float(np.std(mice_variances))
        for r in results:
            r["std_dev"] = std_dev
            
    # Save results
    save_json(results, output_path)
    logger.info(f"Sensitivity sweep results saved to {output_path}")

def run_sensitivity_sweep_synthetic(
    dataset_path: str,
    metadata_path: str,
    m_values: List[int],
    output_path: str
) -> None:
    """
    Run sensitivity sweep on synthetic data and save results.
    Can calculate bias rate since true variance is known.
    """
    logger.info(f"Running sensitivity sweep on synthetic data: {dataset_path}")
    
    # Load metadata to get true variance
    try:
        metadata = load_json(metadata_path)
        true_variance = metadata.get('true_variance')
        if true_variance is None:
            logger.warning("true_variance not found in metadata.")
            true_variance = None
    except Exception as e:
        logger.warning(f"Could not load metadata: {e}")
        true_variance = None
        
    results = run_sensitivity_sweep(
        dataset_path,
        metadata_path,
        m_values,
        true_variance=true_variance,
        is_synthetic=True
    )
    
    save_json(results, output_path)
    logger.info(f"Sensitivity sweep results saved to {output_path}")

def calculate_stability_score(results: List[Dict[str, Any]]) -> float:
    """
    Calculate the stability score (std dev of bias rates) from sweep results.
    """
    if not results:
        return 0.0
        
    bias_rates = [r.get("bias_rate", 0.0) for r in results]
    if len(bias_rates) > 1:
        return float(np.std(bias_rates))
    return 0.0

def main():
    """Main entry point for sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity analysis sweep")
    parser.add_argument("--dataset", type=str, required=True, help="Path to input dataset")
    parser.add_argument("--metadata", type=str, default=None, help="Path to metadata JSON (for synthetic data)")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    parser.add_argument("--m-values", type=str, default="5,10,20", help="Comma-separated list of m values")
    parser.add_argument("--synthetic", action="store_true", help="Flag if dataset is synthetic")
    
    args = parser.parse_args()
    
    # Parse m values
    m_values = [int(x.strip()) for x in args.m_values.split(',')]
    
    if args.synthetic and args.metadata:
        run_sensitivity_sweep_synthetic(
            args.dataset,
            args.metadata,
            m_values,
            args.output
        )
    else:
        run_sensitivity_sweep_real_data(
            args.dataset,
            m_values,
            args.output
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()