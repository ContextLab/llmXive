"""
Multiple-comparison correction utilities for statistical analysis.

Implements Holm-Bonferroni correction (FR-006) for controlling the
Family-Wise Error Rate (FWER) when performing multiple hypothesis tests.

This module provides functions to adjust p-values from multiple tests
using the Holm-Bonferroni method, which is more powerful than the
standard Bonferroni correction while still controlling FWER.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union
import json
from pathlib import Path
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def holm_bonferroni_correction(p_values: List[float], 
                                alpha: float = 0.05) -> Dict[str, Union[List[float], List[bool]]]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    The Holm-Bonferroni method (Holm, 1979) is a step-down procedure that
    controls the Family-Wise Error Rate (FWER) while being more powerful
    than the standard Bonferroni correction.
    
    Algorithm:
    1. Sort p-values in ascending order: p(1) <= p(2) <= ... <= p(m)
    2. For each p(i), compute adjusted p-value: p_adj(i) = max((m - i + 1) * p(i), p_adj(i-1))
       (with p_adj(0) = 0)
    3. Reject null hypothesis if p_adj(i) < alpha
    
    Args:
        p_values: List of raw p-values from hypothesis tests
        alpha: Significance level (default: 0.05)
        
    Returns:
        Dictionary containing:
        - 'adjusted_p_values': List of adjusted p-values (same order as input)
        - 'rejections': List of booleans indicating whether each hypothesis is rejected
        - 'original_p_values': List of original p-values (for reference)
        - 'sorted_indices': Indices that would sort the p-values
    """
    if not p_values:
        logger.warning("Empty p-values list provided to Holm-Bonferroni correction")
        return {
            'adjusted_p_values': [],
            'rejections': [],
            'original_p_values': [],
            'sorted_indices': []
        }
    
    n_tests = len(p_values)
    logger.info(f"Applying Holm-Bonferroni correction to {n_tests} tests with alpha={alpha}")
    
    # Store original indices to restore order later
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Compute adjusted p-values using Holm-Bonferroni method
    adjusted_p_values_sorted = []
    max_adjusted = 0.0
    
    for i, p in enumerate(sorted_p_values):
        # Holm-Bonferroni adjustment: (n - i) * p
        adjusted = (n_tests - i) * p
        # Ensure monotonicity: adjusted p-values must be non-decreasing
        adjusted = max(adjusted, max_adjusted)
        # Cap at 1.0
        adjusted = min(adjusted, 1.0)
        adjusted_p_values_sorted.append(adjusted)
        max_adjusted = adjusted
    
    # Restore original order
    adjusted_p_values = [0.0] * n_tests
    for sorted_idx, adjusted in zip(sorted_indices, adjusted_p_values_sorted):
        adjusted_p_values[sorted_idx] = adjusted
    
    # Determine rejections
    rejections = [p_adj < alpha for p_adj in adjusted_p_values]
    
    logger.debug(f"Adjusted p-values: {adjusted_p_values}")
    logger.debug(f"Rejections: {rejections}")
    logger.info(f"Holm-Bonferroni correction complete: {sum(rejections)} of {n_tests} hypotheses rejected at alpha={alpha}")
    
    return {
        'adjusted_p_values': adjusted_p_values,
        'rejections': rejections,
        'original_p_values': p_values,
        'sorted_indices': sorted_indices.tolist()
    }


def apply_correction_to_dataframe(df: pd.DataFrame, 
                                   p_value_column: str, 
                                   alpha: float = 0.05,
                                   comparison_column: Optional[str] = None) -> pd.DataFrame:
    """
    Apply Holm-Bonferroni correction to a pandas DataFrame containing p-values.
    
    Args:
        df: DataFrame containing p-values
        p_value_column: Name of the column containing p-values
        alpha: Significance level (default: 0.05)
        comparison_column: Optional column name to group comparisons (e.g., 'metric_type')
        
    Returns:
        DataFrame with additional columns for adjusted p-values and rejections
    """
    if p_value_column not in df.columns:
        raise ValueError(f"Column '{p_value_column}' not found in DataFrame")
    
    logger.info(f"Applying Holm-Bonferroni correction to DataFrame with {len(df)} rows")
    
    result = df.copy()
    
    if comparison_column and comparison_column in df.columns:
        # Apply correction within each group
        logger.info(f"Applying correction within groups defined by '{comparison_column}'")
        groups = df[comparison_column].unique()
        
        for group in groups:
            group_mask = df[comparison_column] == group
            group_p_values = df.loc[group_mask, p_value_column].tolist()
            
            if len(group_p_values) == 0:
                continue
            
            correction_result = holm_bonferroni_correction(group_p_values, alpha)
            
            # Update results for this group
            result.loc[group_mask, f'{p_value_column}_adjusted'] = correction_result['adjusted_p_values']
            result.loc[group_mask, f'{p_value_column}_rejected'] = correction_result['rejections']
    else:
        # Apply correction to all p-values
        p_values = df[p_value_column].tolist()
        correction_result = holm_bonferroni_correction(p_values, alpha)
        
        result[f'{p_value_column}_adjusted'] = correction_result['adjusted_p_values']
        result[f'{p_value_column}_rejected'] = correction_result['rejections']
    
    logger.info(f"DataFrame correction complete: {result[f'{p_value_column}_rejected'].sum()} rejections")
    return result


def save_correction_results(results: Dict, output_path: Union[str, Path]) -> None:
    """
    Save correction results to a JSON file.
    
    Args:
        results: Dictionary containing correction results
        output_path: Path to save the JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python native types for JSON serialization
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, list):
            serializable_results[key] = [float(v) if isinstance(v, (np.floating, float)) else bool(v) if isinstance(v, (np.bool_, bool)) else v for v in value]
        else:
            serializable_results[key] = value
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Correction results saved to {output_path}")


def load_correction_results(input_path: Union[str, Path]) -> Dict:
    """
    Load correction results from a JSON file.
    
    Args:
        input_path: Path to the JSON file
        
    Returns:
        Dictionary containing correction results
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Correction results file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        results = json.load(f)
    
    logger.info(f"Correction results loaded from {input_path}")
    return results


def main():
    """
    Command-line interface for testing Holm-Bonferroni correction.
    
    This function demonstrates the correction with sample p-values
    and saves the results to the analysis_results directory.
    """
    from utils.config_manager import get_config
    
    config = get_config()
    output_dir = Path(config.get('analysis_results_dir', 'data/analysis_results'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample p-values for demonstration (simulating multiple hypothesis tests)
    # These represent p-values from McNemar's tests and LME model comparisons
    sample_p_values = [0.001, 0.032, 0.045, 0.123, 0.067, 0.890, 0.021, 0.156]
    sample_comparisons = [
        "Baseline vs LLM (Accuracy)",
        "Baseline vs Rule (Accuracy)",
        "LLM vs Rule (Accuracy)",
        "Baseline vs LLM (Speed)",
        "Baseline vs Rule (Speed)",
        "LLM vs Rule (Speed)",
        "Baseline vs LLM (Top-5)",
        "Baseline vs Rule (Top-5)"
    ]
    
    logger.info("Running Holm-Bonferroni correction demonstration")
    logger.info(f"Sample p-values: {sample_p_values}")
    
    # Apply correction
    results = holm_bonferroni_correction(sample_p_values, alpha=0.05)
    
    # Create a summary DataFrame
    summary_df = pd.DataFrame({
        'comparison': sample_comparisons,
        'raw_p_value': sample_p_values,
        'adjusted_p_value': results['adjusted_p_values'],
        'rejected': results['rejections']
    })
    
    # Save results
    json_output_path = output_dir / 'holm_bonferroni_results.json'
    save_correction_results(results, json_output_path)
    
    csv_output_path = output_dir / 'holm_bonferroni_summary.csv'
    summary_df.to_csv(csv_output_path, index=False)
    
    logger.info(f"Results saved to {json_output_path} and {csv_output_path}")
    logger.info(f"Summary:\n{summary_df.to_string(index=False)}")
    
    return results


if __name__ == "__main__":
    main()