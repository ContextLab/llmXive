import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from utils.logging import get_module_logger

logger = get_module_logger(__name__)

def calculate_jaccard_index(set_a: Set[Any], set_b: Set[Any]) -> float:
    """
    Calculate the Jaccard index between two sets.
    
    Args:
        set_a: First set of items.
        set_b: Second set of items.
        
    Returns:
        Jaccard index (intersection size / union size). Returns 0.0 if both sets are empty.
    """
    if not set_a and not set_b:
        return 1.0
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
        
    return intersection / union

def calculate_jaccard_stability_matrix(feature_sets: List[Set[Any]]) -> pd.DataFrame:
    """
    Calculate the pairwise Jaccard index matrix for a list of feature sets.
    
    Args:
        feature_sets: List of sets, each representing a set of selected features.
        
    Returns:
        DataFrame with Jaccard indices between all pairs of feature sets.
    """
    n = len(feature_sets)
    if n == 0:
        return pd.DataFrame()
        
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
            
    return pd.DataFrame(
        matrix,
        index=[f"Run_{i}" for i in range(n)],
        columns=[f"Run_{j}" for j in range(n)]
    )

def calculate_mean_jaccard_stability(matrix: pd.DataFrame) -> float:
    """
    Calculate the mean Jaccard stability score from a pairwise matrix.
    Excludes the diagonal (self-comparison).
    
    Args:
        matrix: Pairwise Jaccard index matrix.
        
    Returns:
        Mean stability score.
    """
    if matrix.empty:
        return 0.0
        
    n = matrix.shape[0]
    if n <= 1:
        return 1.0
        
    # Exclude diagonal
    diag_mask = np.eye(n, dtype=bool)
    off_diag_values = matrix.values[~diag_mask]
    
    if len(off_diag_values) == 0:
        return 0.0
        
    return float(np.mean(off_diag_values))

def save_jaccard_stability_report(
    matrix: pd.DataFrame,
    mean_stability: float,
    output_path: Union[str, Path]
) -> None:
    """
    Save the Jaccard stability analysis report to a CSV file.
    
    Args:
        matrix: Pairwise Jaccard index matrix.
        mean_stability: Calculated mean stability score.
        output_path: Path to save the report.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(f"# Jaccard Stability Report\n")
        f.write(f"# Mean Stability Score: {mean_stability:.4f}\n")
        f.write(f"#\n")
        matrix.to_csv(f)
        
    logger.info(f"Jaccard stability report saved to {output_path}")

def benjamini_hochberg_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).
    
    This function takes a list of p-values (typically from predictor significance tests)
    and adjusts them to account for multiple comparisons. It returns a dictionary
    containing the adjusted p-values, a boolean mask indicating which hypotheses
    are rejected (significant), and the critical values used in the calculation.
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level for FDR control (default 0.05).
        
    Returns:
        A dictionary with keys:
            - 'adjusted_p_values': List of BH-adjusted p-values.
            - 'is_significant': List of booleans indicating significance after correction.
            - 'rank': List of ranks assigned to original p-values.
            - 'critical_values': List of critical values for the BH procedure.
            - 'num_rejected': Integer count of rejected null hypotheses.
    """
    if not p_values:
        return {
            'adjusted_p_values': [],
            'is_significant': [],
            'rank': [],
            'critical_values': [],
            'num_rejected': 0
        }
        
    n = len(p_values)
    
    # Create a DataFrame to track original indices and values
    df = pd.DataFrame({
        'original_index': range(n),
        'p_value': p_values
    })
    
    # Sort by p-value
    df = df.sort_values('p_value').reset_index(drop=True)
    
    # Calculate ranks (1 to n)
    df['rank'] = np.arange(1, n + 1)
    
    # Calculate critical values: (i/n) * alpha
    df['critical_value'] = (df['rank'] / n) * alpha
    
    # Calculate adjusted p-values using the BH step-up procedure
    # Start from the largest p-value and work backwards
    # adjusted_p_i = min(1, min_{j>=i} (n/j * p_j))
    
    # Initialize adjusted p-values
    df['adjusted_p_value'] = 1.0
    
    # Work backwards from the largest rank
    min_adjusted = 1.0
    for i in range(n - 1, -1, -1):
        # Calculate the BH adjusted value for this rank
        bh_value = (n / df.iloc[i]['rank']) * df.iloc[i]['p_value']
        # Ensure monotonicity: adjusted p-value at rank i is min(bh_value, adjusted at i+1)
        min_adjusted = min(min_adjusted, bh_value, 1.0)
        df.at[i, 'adjusted_p_value'] = min_adjusted
        
    # Sort back to original order
    df = df.sort_values('original_index').reset_index(drop=True)
    
    # Determine significance
    df['is_significant'] = df['adjusted_p_value'] <= alpha
    
    # Count rejections
    num_rejected = int(df['is_significant'].sum())
    
    logger.info(f"Benjamini-Hochberg correction applied: {num_rejected}/{n} predictors significant at alpha={alpha}")
    
    return {
        'adjusted_p_values': df['adjusted_p_value'].tolist(),
        'is_significant': df['is_significant'].tolist(),
        'rank': df['rank'].tolist(),
        'critical_values': df['critical_value'].tolist(),
        'num_rejected': num_rejected
    }

def apply_bh_correction_to_predictors(
    predictor_data: pd.DataFrame,
    p_value_column: str = 'p_value',
    alpha: float = 0.05,
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to a DataFrame of predictor statistics.
    
    This is a convenience wrapper for the BH correction function, designed to work
    with typical model output DataFrames containing predictor names and p-values.
    
    Args:
        predictor_data: DataFrame with at least a column of p-values.
        p_value_column: Name of the column containing p-values.
        alpha: Significance level for FDR control.
        output_path: Optional path to save the corrected results.
        
    Returns:
        DataFrame with added columns for adjusted p-values and significance status.
    """
    if p_value_column not in predictor_data.columns:
        raise ValueError(f"Column '{p_value_column}' not found in predictor_data")
        
    p_values = predictor_data[p_value_column].tolist()
    
    # Apply BH correction
    bh_results = benjamini_hochberg_correction(p_values, alpha)
    
    # Create a new DataFrame with results
    result_df = predictor_data.copy()
    result_df['adjusted_p_value'] = bh_results['adjusted_p_values']
    result_df['is_significant_bh'] = bh_results['is_significant']
    result_df['bh_rank'] = bh_results['rank']
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        logger.info(f"BH-corrected predictor results saved to {output_path}")
        
    return result_df