"""
Metrics module for statistical analysis of chess game data.
Implements Benjamini-Hochberg FDR correction and other statistical metrics.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_wald_z_statistic(coefficient: float, standard_error: float) -> float:
    """
    Calculate Wald Z-statistic for a coefficient.
    
    Args:
        coefficient: The estimated coefficient value.
        standard_error: The standard error of the coefficient.
        
    Returns:
        The Wald Z-statistic.
        
    Raises:
        ValueError: If standard_error is zero or negative.
    """
    if standard_error <= 0:
        raise ValueError("Standard error must be positive")
    return coefficient / standard_error

def calculate_p_value_z_test(z_statistic: float, two_tailed: bool = True) -> float:
    """
    Calculate p-value from a Z-statistic using the standard normal distribution.
    
    Args:
        z_statistic: The Z-statistic value.
        two_tailed: If True, calculate two-tailed p-value; otherwise one-tailed.
        
    Returns:
        The p-value.
    """
    if two_tailed:
        return 2 * (1 - stats.norm.cdf(abs(z_statistic)))
    else:
        return 1 - stats.norm.cdf(z_statistic)

def calculate_f_statistic(model_ss: float, model_df: int, residual_ss: float, residual_df: int) -> float:
    """
    Calculate F-statistic for model significance.
    
    Args:
        model_ss: Model sum of squares.
        model_df: Model degrees of freedom.
        residual_ss: Residual sum of squares.
        residual_df: Residual degrees of freedom.
        
    Returns:
        The F-statistic.
    """
    if model_df == 0 or residual_df == 0:
        raise ValueError("Degrees of freedom must be positive")
    model_ms = model_ss / model_df
    residual_ms = residual_ss / residual_df
    return model_ms / residual_ms

def calculate_f_statistic_from_sums(r_squared: float, n: int, p: int) -> float:
    """
    Calculate F-statistic from R-squared value.
    
    Args:
        r_squared: The R-squared value of the model.
        n: Number of observations.
        p: Number of predictors (excluding intercept).
        
    Returns:
        The F-statistic.
    """
    if p == 0 or n - p - 1 == 0:
        raise ValueError("Invalid degrees of freedom")
    numerator = r_squared / p
    denominator = (1 - r_squared) / (n - p - 1)
    return numerator / denominator

def apply_benjamini_hochberg_fdr(p_values: pd.Series) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    
    This function implements the Benjamini-Hochberg procedure to control
    the False Discovery Rate when performing multiple hypothesis tests.
    
    Args:
        p_values: A pandas Series of p-values to correct.
        
    Returns:
        A pandas DataFrame with columns:
            - 'original_p_value': The original p-values
            - 'corrected_p_value': The FDR-corrected p-values
            
    Raises:
        ValueError: If input is not a pandas Series or contains invalid values.
        TypeError: If input contains non-numeric values.
    """
    if not isinstance(p_values, pd.Series):
        raise ValueError("Input must be a pandas Series")
    
    if p_values.isna().any():
        logger.warning("Input contains NaN values. They will be excluded from correction.")
        valid_mask = ~p_values.isna()
        p_values_valid = p_values[valid_mask]
    else:
        p_values_valid = p_values
        valid_mask = pd.Series([True] * len(p_values), index=p_values.index)
    
    if len(p_values_valid) == 0:
        raise ValueError("No valid p-values to correct")
    
    if not pd.api.types.is_numeric_dtype(p_values_valid):
        raise TypeError("Input must contain numeric values")
    
    # Create a DataFrame to track original indices
    df = pd.DataFrame({
        'original_p_value': p_values_valid.values,
        'original_index': np.arange(len(p_values_valid))
    })
    
    # Sort by p-value
    df_sorted = df.sort_values('original_p_value').reset_index(drop=True)
    
    n = len(df_sorted)
    
    # Calculate BH critical values
    df_sorted['rank'] = np.arange(1, n + 1)
    df_sorted['critical_value'] = (df_sorted['rank'] / n) * df_sorted['original_p_value'].max()
    
    # Apply BH procedure: find the largest k such that p_(k) <= (k/m) * alpha
    # Then all p-values <= p_(k) are significant
    # For corrected p-values: q_(i) = min(1, min_{j>=i} (m/j * p_(j)))
    
    # Calculate corrected p-values
    corrected_values = np.zeros(n)
    
    # Start from the largest p-value and work backwards
    # q_(n) = p_(n)
    # q_(i) = min(q_(i+1), m/i * p_(i))
    # But we need to ensure monotonicity: q_(i) <= q_(i+1)
    
    for i in range(n - 1, -1, -1):
        if i == n - 1:
            corrected_values[i] = df_sorted['original_p_value'].iloc[i]
        else:
            # Calculate the BH-adjusted value
            adjusted = df_sorted['original_p_value'].iloc[i] * n / (i + 1)
            # Take the minimum of the adjusted value and the next corrected value
            corrected_values[i] = min(adjusted, corrected_values[i + 1])
    
    # Ensure monotonicity from the start (cumulative minimum from the right)
    corrected_values = np.minimum.accumulate(corrected_values[::-1])[::-1]
    
    # Cap at 1.0
    corrected_values = np.minimum(corrected_values, 1.0)
    
    df_sorted['corrected_p_value'] = corrected_values
    
    # Sort back to original order
    df_result = df_sorted.sort_values('original_index').reset_index(drop=True)
    
    # Return only the p-value columns, preserving original index
    result = pd.DataFrame({
        'original_p_value': df_result['original_p_value'].values,
        'corrected_p_value': df_result['corrected_p_value'].values
    }, index=p_values_valid.index)
    
    # Re-insert NaN values if they existed
    if not valid_mask.all():
        full_result = pd.DataFrame({
            'original_p_value': p_values.values,
            'corrected_p_value': np.nan
        }, index=p_values.index)
        full_result.loc[valid_mask, 'original_p_value'] = result['original_p_value'].values
        full_result.loc[valid_mask, 'corrected_p_value'] = result['corrected_p_value'].values
        return full_result
    
    return result

def calculate_metric_summary(
    coefficients: Dict[str, float],
    p_values: Dict[str, float],
    standard_errors: Dict[str, float]
) -> pd.DataFrame:
    """
    Calculate a summary DataFrame of metrics for all predictors.
    
    Args:
        coefficients: Dictionary of predictor names to coefficient values.
        p_values: Dictionary of predictor names to p-values.
        standard_errors: Dictionary of predictor names to standard errors.
        
    Returns:
        A DataFrame with columns: predictor, coefficient, std_error, z_statistic, p_value.
    """
    predictors = list(coefficients.keys())
    
    data = {
        'predictor': predictors,
        'coefficient': [coefficients[p] for p in predictors],
        'std_error': [standard_errors[p] for p in predictors],
        'p_value': [p_values[p] for p in predictors]
    }
    
    df = pd.DataFrame(data)
    df['z_statistic'] = df['coefficient'] / df['std_error']
    
    return df

def main():
    """
    Main function to demonstrate FDR correction.
    """
    # Example usage with sample p-values
    sample_p_values = pd.Series([0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.3, 0.4])
    sample_p_values.name = 'p_values'
    
    logger.info("Sample p-values:")
    print(sample_p_values)
    
    corrected_df = apply_benjamini_hochberg_fdr(sample_p_values)
    
    logger.info("\nFDR-corrected p-values:")
    print(corrected_df)
    
    # Save to a sample file for demonstration
    output_path = 'data/results/fdr_correction_sample.csv'
    corrected_df.to_csv(output_path, index=False)
    logger.info(f"\nSample FDR correction results saved to {output_path}")

if __name__ == "__main__":
    main()