"""
Benjamini-Hochberg (FDR) Correction for Multiple Comparisons.

This module implements the Benjamini-Hochberg procedure to control the False
Discovery Rate (FDR) for a set of p-values, specifically targeting interaction
terms and secondary personality traits as defined in FR-007.

Main effects (Gamification, Conscientiousness) are reported uncorrected unless
explicitly included in the multiple comparison set.
"""
import os
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from code.utils.logging import pipeline_logger

logger = pipeline_logger


def benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform the Benjamini-Hochberg FDR correction on a list of p-values.

    Parameters
    ----------
    p_values : np.ndarray
        Array of raw p-values.
    alpha : float
        Target FDR level (default 0.05).

    Returns
    -------
    rejected : np.ndarray
        Boolean array indicating which hypotheses are rejected (True = significant).
    adj_p_values : np.ndarray
        Array of adjusted p-values.
    critical_values : np.ndarray
        Array of critical values used in the comparison.
    """
    if len(p_values) == 0:
        return np.array([]), np.array([]), np.array([])

    # Sort p-values and keep track of original indices
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate critical values: (i / n) * alpha
    # i ranges from 1 to n
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Find the largest k such that p_(k) <= critical_(k)
    # We iterate from the largest p-value downwards
    reject_mask = sorted_p_values <= critical_values
    if not np.any(reject_mask):
        # No rejections
        rejected_sorted = np.zeros(n, dtype=bool)
    else:
        # Find the largest index where rejection holds
        k = np.where(reject_mask)[0][-1]
        rejected_sorted = np.zeros(n, dtype=bool)
        rejected_sorted[:k+1] = True

    # Map back to original order
    rejected = np.zeros(n, dtype=bool)
    rejected[sorted_indices] = rejected_sorted

    # Calculate adjusted p-values
    # adj_p[i] = min( (n / rank) * p, 1 ) with monotonicity enforcement
    adjusted_sorted = np.zeros(n)
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj_val = min(sorted_p_values[i] * n / rank, 1.0)
        adjusted_sorted[i] = adj_val

    # Enforce monotonicity: adj_p[i] <= adj_p[i+1]
    # We iterate backwards to ensure the cumulative minimum is respected
    for i in range(n - 2, -1, -1):
        adjusted_sorted[i] = min(adjusted_sorted[i], adjusted_sorted[i+1])

    adj_p_values = np.zeros(n)
    adj_p_values[sorted_indices] = adjusted_sorted

    return rejected, adj_p_values, critical_values


def apply_fdr_to_model_results(
    model_results: pd.DataFrame,
    interaction_columns: List[str],
    secondary_columns: List[str],
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Apply FDR correction to specific columns in a model results DataFrame.

    This function extracts p-values from the specified columns (interaction terms
    and secondary traits), applies the Benjamini-Hochberg correction, and
    appends the adjusted p-values and significance flags to the DataFrame.

    Parameters
    ----------
    model_results : pd.DataFrame
        DataFrame containing model summary statistics (must include 'pvalue' or similar).
        Expected columns: 'term', 'coef', 'std err', 't', 'P>|t|' (statsmodels style).
    interaction_columns : List[str]
        List of term names representing interaction effects to correct.
    secondary_columns : List[str]
        List of term names representing secondary personality traits to correct.
    alpha : float
        Target FDR level.

    Returns
    -------
    pd.DataFrame
        The input DataFrame with added columns:
        - 'pval_adj': Adjusted p-value
        - 'fdr_significant': Boolean flag indicating significance after FDR correction
    """
    # Identify the target terms
    target_terms = list(set(interaction_columns + secondary_columns))
    
    if not target_terms:
        logger.info("No interaction or secondary columns specified for FDR correction.")
        model_results['pval_adj'] = model_results.get('P>|t|', model_results.get('pvalue', np.nan))
        model_results['fdr_significant'] = False
        return model_results

    # Filter rows corresponding to target terms
    # Assuming the 'term' column exists in statsmodels summary output
    if 'term' not in model_results.columns:
        raise ValueError("Model results DataFrame must contain a 'term' column.")
    
    target_mask = model_results['term'].isin(target_terms)
    target_pvalues = model_results.loc[target_mask, 'P>|t|'].values

    if len(target_pvalues) == 0:
        logger.warning("No p-values found for the specified target terms.")
        model_results['pval_adj'] = model_results.get('P>|t|', model_results.get('pvalue', np.nan))
        model_results['fdr_significant'] = False
        return model_results

    # Apply BH correction
    rejected, adj_p, _ = benjamini_hochberg(target_pvalues, alpha)

    # Create a mapping from term to adjusted p-value and significance
    # We need to map back to the original dataframe rows
    # Since the mask might not be contiguous, we create a series
    adj_p_series = pd.Series(np.nan, index=model_results.index)
    sig_series = pd.Series(False, index=model_results.index)

    # We need to know which index in target_pvalues corresponds to which row in model_results
    # Iterate through the filtered dataframe
    filtered_indices = model_results.index[target_mask]
    for idx, adj_val, is_sig in zip(filtered_indices, adj_p, rejected):
        adj_p_series[idx] = adj_val
        sig_series[idx] = is_sig

    # Assign to dataframe
    model_results['pval_adj'] = adj_p_series
    model_results['fdr_significant'] = sig_series

    # Log the results
    significant_count = sig_series.sum()
    logger.info(f"FDR Correction applied to {len(target_terms)} terms. "
                f"Significant at alpha={alpha}: {significant_count}/{len(target_terms)}")
    
    # Log specific significant findings
    if significant_count > 0:
        sig_terms = model_results.loc[sig_series, 'term'].tolist()
        logger.info(f"Significant terms after FDR: {sig_terms}")

    return model_results


def main():
    """
    Main entry point for FDR correction testing/demo.
    
    This function loads processed data, fits a model (if not already done),
    and demonstrates the FDR correction on interaction terms.
    In a real pipeline, this would be called by the reporting module.
    """
    logger.info("Starting FDR Correction Module.")
    
    # Check if processed data exists
    data_path = "data/processed/merged_data.csv"
    if not os.path.exists(data_path):
        logger.warning(f"Processed data not found at {data_path}. "
                       "Skipping FDR correction execution. "
                       "Ensure T017 (Merge) and T020 (Modeling) are complete.")
        return

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")

    # Example: Simulate a model results dataframe for demonstration
    # In the actual pipeline, this would be populated by fit_mixed_effects_model
    # We create a dummy dataframe to show the function works
    dummy_terms = [
        "Intercept", 
        "Gamified", 
        "Conscientiousness", 
        "Gamified:Conscientiousness", 
        "Need_for_Achievement", 
        "Gamified:Need_for_Achievement"
    ]
    dummy_pvalues = [0.001, 0.003, 0.04, 0.012, 0.08, 0.009]
    
    results_df = pd.DataFrame({
        "term": dummy_terms,
        "coef": [1.0, 0.5, 0.2, 0.15, 0.1, 0.12],
        "std err": [0.1, 0.1, 0.05, 0.06, 0.05, 0.06],
        "t": [10.0, 5.0, 4.0, 2.5, 2.0, 2.0],
        "P>|t|": dummy_pvalues
    })

    # Define the sets for correction
    interaction_terms = ["Gamified:Conscientiousness", "Gamified:Need_for_Achievement"]
    secondary_terms = ["Need_for_Achievement"] # As per FR-007, secondary traits are included

    # Apply correction
    corrected_df = apply_fdr_to_model_results(
        results_df, 
        interaction_columns=interaction_terms, 
        secondary_columns=secondary_terms, 
        alpha=0.05
    )

    # Display results
    logger.info("Original vs Corrected P-values:")
    logger.info(corrected_df[['term', 'P>|t|', 'pval_adj', 'fdr_significant']].to_string())

    # Save the corrected results to a CSV for the report
    output_path = "data/processed/fdr_corrected_results.csv"
    corrected_df.to_csv(output_path, index=False)
    logger.info(f"FDR corrected results saved to {output_path}")


if __name__ == "__main__":
    main()