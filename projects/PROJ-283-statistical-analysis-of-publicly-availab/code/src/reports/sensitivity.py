"""
Sensitivity analysis module for threshold sweep and Jaccard index calculation.

Implements FR-010: Perform threshold sweep analysis over a range of small thresholds
and report Jaccard index of significant predictors.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
import logging

from src.config import get_data_path
from src.validation.validate_contracts import validate_model_output, assert_model_output_valid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_jaccard_index(set_a: set, set_b: set) -> float:
    """
    Calculate the Jaccard index between two sets.
    
    Jaccard Index = |A ∩ B| / |A ∪ B|
    
    Args:
        set_a: First set of elements
        set_b: Second set of elements
        
    Returns:
        Jaccard index value between 0 and 1
    """
    if not set_a and not set_b:
        return 1.0  # Both empty sets are identical
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 1.0
    
    return intersection / union


def get_significant_predictors(metrics_df: pd.DataFrame, 
                               p_value_col: str = 'p_values',
                               threshold: float = 0.05) -> set:
    """
    Extract the set of significant predictors based on a p-value threshold.
    
    Args:
        metrics_df: DataFrame containing model metrics including p-values
        p_value_col: Name of the column containing p-values
        threshold: P-value threshold for significance
        
    Returns:
        Set of predictor names that are significant
    """
    if p_value_col not in metrics_df.columns:
        raise ValueError(f"Column '{p_value_col}' not found in metrics DataFrame")
    
    significant = metrics_df[metrics_df[p_value_col] < threshold]
    if 'feature' in significant.columns:
        return set(significant['feature'].tolist())
    elif 'predictor' in significant.columns:
        return set(significant['predictor'].tolist())
    else:
        # Assume index contains feature names
        return set(significant.index.tolist())


def perform_threshold_sweep(metrics_df: pd.DataFrame,
                            threshold_range: Optional[List[float]] = None,
                            p_value_col: str = 'p_values') -> pd.DataFrame:
    """
    Perform a threshold sweep analysis over a range of p-value thresholds.
    
    For each threshold, identifies significant predictors and calculates
    the Jaccard index relative to the previous threshold.
    
    Args:
        metrics_df: DataFrame containing model metrics with p-values
        threshold_range: List of thresholds to sweep. Defaults to [0.01, 0.02, ..., 0.10]
        p_value_col: Name of the column containing p-values
        
    Returns:
        DataFrame with columns: threshold, n_significant, jaccard_index
    """
    if threshold_range is None:
        threshold_range = [i * 0.01 for i in range(1, 11)]  # 0.01 to 0.10
    
    results = []
    previous_significant = None
    
    for threshold in sorted(threshold_range):
        current_significant = get_significant_predictors(
            metrics_df, p_value_col=p_value_col, threshold=threshold
        )
        
        if previous_significant is not None:
            jaccard = calculate_jaccard_index(previous_significant, current_significant)
        else:
            # First threshold has no previous to compare
            jaccard = 1.0 
        
        results.append({
            'threshold': threshold,
            'n_significant': len(current_significant),
            'significant_predictors': sorted(list(current_significant)),
            'jaccard_index': jaccard
        })
        
        previous_significant = current_significant
    
    return pd.DataFrame(results)


def run_sensitivity_analysis(input_path: Optional[str] = None,
                             output_path: Optional[str] = None) -> Dict:
    """
    Main function to run sensitivity analysis on model output data.
    
    Args:
        input_path: Path to input model metrics JSON. If None, uses default path.
        output_path: Path to save results JSON. If None, uses default path.
        
    Returns:
        Dictionary containing analysis results
    """
    # Default paths
    data_dir = get_data_path('results')
    if input_path is None:
        input_path = str(data_dir / 'model_metrics.json')
    if output_path is None:
        output_path = str(data_dir / 'sensitivity_analysis.json')
    
    logger.info(f"Loading model metrics from {input_path}")
    
    # Load data
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    with open(input_path, 'r') as f:
        model_data = json.load(f)
    
    # Validate structure (basic check)
    if 'models' not in model_data:
        raise ValueError("Input JSON must contain 'models' key")
    
    results = {
        'analysis_type': 'threshold_sweep',
        'threshold_range': [i * 0.01 for i in range(1, 11)],
        'models': {}
    }
    
    for model_name, model_metrics in model_data['models'].items():
        logger.info(f"Processing model: {model_name}")
        
        # Convert metrics to DataFrame
        if isinstance(model_metrics, dict) and 'coefficients' in model_metrics:
            # Handle structured model output
            df_data = []
            coeffs = model_metrics['coefficients']
            p_vals = model_metrics.get('p_values', [])
            
            # Ensure lists are same length
            n_features = len(coeffs) if isinstance(coeffs, list) else 0
            if isinstance(coeffs, dict):
                feature_names = list(coeffs.keys())
                n_features = len(feature_names)
            
            for i, (feature, coef) in enumerate(coeffs.items() if isinstance(coeffs, dict) else enumerate(coeffs)):
                p_val = p_vals[i] if i < len(p_vals) else 1.0
                df_data.append({
                    'feature': feature if isinstance(coeffs, dict) else f'feature_{i}',
                    'coefficient': coef,
                    'p_values': p_val
                })
            
            metrics_df = pd.DataFrame(df_data)
        elif isinstance(model_metrics, list):
            # Handle list of metrics
            metrics_df = pd.DataFrame(model_metrics)
            if 'p_values' not in metrics_df.columns and 'p_value' in metrics_df.columns:
                metrics_df['p_values'] = metrics_df['p_value']
        else:
            logger.warning(f"Skipping model {model_name} due to unexpected format")
            continue
        
        # Ensure p_values column exists
        if 'p_values' not in metrics_df.columns:
            logger.warning(f"Model {model_name} missing p_values column, skipping")
            continue
        
        # Perform threshold sweep
        sweep_results = perform_threshold_sweep(metrics_df)
        
        results['models'][model_name] = {
            'threshold_sweep': sweep_results.to_dict(orient='records'),
            'summary': {
                'total_predictors': len(metrics_df),
                'significant_at_005': int(sweep_results[sweep_results['threshold'] == 0.05]['n_significant'].values[0]) if len(sweep_results) > 0 else 0,
                'jaccard_at_005': float(sweep_results[sweep_results['threshold'] == 0.05]['jaccard_index'].values[0]) if len(sweep_results) > 0 else 0.0
            }
        }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    
    return results


if __name__ == '__main__':
    run_sensitivity_analysis()
