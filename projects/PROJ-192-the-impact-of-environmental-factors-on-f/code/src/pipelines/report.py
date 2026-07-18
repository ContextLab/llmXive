import os
import pandas as pd
import numpy as np
from scipy.stats import fdr_bh
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_permanova_results(file_path: str) -> pd.DataFrame:
    """
    Load PERMANOVA results from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing PERMANOVA results.
        
    Returns:
        DataFrame with PERMANOVA results.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PERMANOVA results file not found: {file_path}")
    
    df = pd.read_csv(path)
    required_cols = ['term', 'R2', 'p-value', 'p-value_adj']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in PERMANOVA results: {missing}")
    
    return df

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    _, p_adj, _, _ = fdr_bh(p_values, alpha=0.05, method='indep')
    return list(p_adj)

def generate_permanova_summary(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a summary CSV of PERMANOVA results with FDR correction.
    
    Args:
        results_df: DataFrame with PERMANOVA results.
        output_path: Path to save the summary CSV.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure FDR is applied if not already
    if 'p-value_adj' not in results_df.columns:
        results_df = results_df.copy()
        results_df['p-value_adj'] = apply_fdr_correction(results_df['p-value'].tolist())
    
    results_df.to_csv(output, index=False)
    logger.info(f"Saved PERMANOVA summary to {output_path}")

def generate_db_rda_variance(results_df: pd.DataFrame, output_path: str) -> None:
    """
    Generate variance partitioning results from db-RDA.
    
    Args:
        results_df: DataFrame with variance partitioning results.
        output_path: Path to save the variance CSV.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Assuming results_df has columns: term, R2, p-value, p-value_adj
    # We output the variance explained (R2) for each term
    results_df.to_csv(output, index=False)
    logger.info(f"Saved db-RDA variance to {output_path}")

def generate_db_rda_biome_results(results_df: pd.DataFrame, biome: str, output_path: str) -> None:
    """
    Generate db-RDA results for a specific biome.
    
    Args:
        results_df: DataFrame with results for the biome.
        biome: Name of the biome.
        output_path: Path to save the results CSV.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output, index=False)
    logger.info(f"Saved db-RDA results for biome '{biome}' to {output_path}")

def determine_top_drivers_stability(results_df: pd.DataFrame, biome_column: str = 'biome') -> Tuple[str, float]:
    """
    Determine the stability of top drivers across biomes.
    
    Args:
        results_df: DataFrame with results including biome and top driver.
        biome_column: Name of the column containing biome information.
        
    Returns:
        Tuple of (top_driver_name, std_dev_of_rank).
    """
    if results_df.empty:
        return "N/A", 0.0
    
    # Group by biome and find the top driver (highest R2 or lowest p-value)
    # Assuming 'R2' is the metric for importance
    top_drivers = results_df.sort_values('R2', ascending=False).groupby(biome_column).first()
    
    if top_drivers.empty:
        return "N/A", 0.0
    
    # Calculate the standard deviation of the rank index of the top driver
    # Here we assume the top driver is the one with the highest R2 in each biome
    # We rank the R2 values across all biomes for the top driver
    top_driver_names = top_drivers['term'].unique()
    
    if len(top_driver_names) == 0:
        return "N/A", 0.0
    
    # For simplicity, we take the most frequent top driver and calculate stability
    # A more robust method would involve rank correlation across biomes
    most_frequent_driver = top_drivers['term'].value_counts().idxmax()
    
    # Calculate a simple stability metric: 1 if all biomes agree, 0 if completely random
    # This is a placeholder for a more complex statistical test
    stability_score = top_drivers['term'].value_counts().max() / len(top_drivers)
    
    return most_frequent_driver, stability_score

def run_threshold_sweep(permanova_results_path: str, output_path: str, 
                        p_value_thresholds: Optional[List[float]] = None,
                        r2_thresholds: Optional[List[float]] = None,
                        use_fdr: bool = True) -> pd.DataFrame:
    """
    Implement threshold sweep logic to iterate p-values and R² cutoffs.
    
    This function:
    1. Loads the PERMANOVA results.
    2. Iterates over specified p-value thresholds (default: [0.01, 0.05, 0.1]).
    3. Iterates over specified R² cutoffs (default: [0.05, 0.1, 0.2]).
    4. For each combination, filters the results and identifies the top driver.
    5. Records the top driver for each threshold set.
    
    Args:
        permanova_results_path: Path to the CSV file with PERMANOVA results.
        output_path: Path to save the sensitivity analysis CSV.
        p_value_thresholds: List of p-value thresholds to test.
        r2_thresholds: List of R² thresholds to test.
        use_fdr: If True, use 'p-value_adj' for filtering; else use 'p-value'.
        
    Returns:
        DataFrame with the sensitivity analysis results.
    """
    # Load data
    df = load_permanova_results(permanova_results_path)
    
    # Defaults
    if p_value_thresholds is None:
        p_value_thresholds = [0.01, 0.05, 0.1]
    if r2_thresholds is None:
        r2_thresholds = [0.05, 0.1, 0.2]
    
    results = []
    
    # Determine which p-value column to use
    p_col = 'p-value_adj' if use_fdr and 'p-value_adj' in df.columns else 'p-value'
    
    logger.info(f"Starting threshold sweep with {len(p_value_thresholds)} p-value thresholds "
                f"and {len(r2_thresholds)} R² thresholds.")
    
    for p_thresh in p_value_thresholds:
        for r2_thresh in r2_thresholds:
            # Filter: p <= p_thresh AND R2 >= r2_thresh
            mask = (df[p_col] <= p_thresh) & (df['R2'] >= r2_thresh)
            subset = df[mask]
            
            top_driver = "None"
            if not subset.empty:
                # Top driver is the one with the highest R2 in the filtered set
                top_driver = subset.loc[subset['R2'].idxmax(), 'term']
            
            results.append({
                'p_value_threshold': p_thresh,
                'r2_threshold': r2_thresh,
                'significant_terms_count': len(subset),
                'top_driver': top_driver,
                'stable': True if top_driver != "None" else False
            })
    
    result_df = pd.DataFrame(results)
    
    # Save to output
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output, index=False)
    
    logger.info(f"Sensitivity analysis saved to {output_path}")
    return result_df

def determine_top_drivers_and_ranking_stability(sensitivity_df: pd.DataFrame) -> Tuple[str, float, bool]:
    """
    Calculate robustness metric from sensitivity analysis.
    
    Args:
        sensitivity_df: DataFrame from run_threshold_sweep.
        
    Returns:
        Tuple of (most_frequent_driver, stability_percentage, is_robust).
    """
    if sensitivity_df.empty or (sensitivity_df['top_driver'] == "None").all():
        return "None", 0.0, False
    
    # Filter out 'None' drivers
    valid_df = sensitivity_df[sensitivity_df['top_driver'] != "None"]
    if valid_df.empty:
        return "None", 0.0, False
    
    # Count frequency of each top driver
    driver_counts = valid_df['top_driver'].value_counts()
    most_frequent_driver = driver_counts.idxmax()
    count_most_frequent = driver_counts.max()
    
    total_rows = len(valid_df)
    stability_percentage = (count_most_frequent / total_rows) * 100
    
    # Pass if >= 80%
    is_robust = stability_percentage >= 80.0
    
    return most_frequent_driver, stability_percentage, is_robust

def run_report_pipeline_with_null_handling(permanova_results_path: str, 
                                           sensitivity_output_path: str,
                                           robustness_output_path: str) -> None:
    """
    Run the full report pipeline including null result handling.
    
    Args:
        permanova_results_path: Path to PERMANOVA results.
        sensitivity_output_path: Path for sensitivity analysis CSV.
        robustness_output_path: Path for robustness summary Markdown.
    """
    # Run threshold sweep
    sensitivity_df = run_threshold_sweep(permanova_results_path, sensitivity_output_path)
    
    # Calculate robustness
    top_driver, stability_pct, is_robust = determine_top_drivers_and_ranking_stability(sensitivity_df)
    
    # Generate robustness summary
    output = Path(robustness_output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    status = "PASS" if is_robust else "FAIL"
    summary = f"""# Robustness Summary

**Analysis**: Threshold Sensitivity for Top Driver Stability

- **Top Driver**: {top_driver}
- **Stability Percentage**: {stability_pct:.2f}%
- **Threshold**: 80%
- **Status**: {status}

## Details

The analysis swept p-value thresholds (0.01, 0.05, 0.1) and R² cutoffs (0.05, 0.1, 0.2).
The top driver remained **{top_driver}** in {stability_pct:.2f}% of the threshold combinations.
"""
    
    with open(output, 'w') as f:
        f.write(summary)
    
    logger.info(f"Robustness summary saved to {robustness_output_path}")

def generate_sampling_report(sampling_info: Dict, output_path: str) -> None:
    """
    Generate a report documenting subsampling ratios.
    
    Args:
        sampling_info: Dictionary with sampling details (e.g., original_count, subsample_count, ratio).
        output_path: Path to save the report CSV.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame([sampling_info])
    df.to_csv(output, index=False)
    logger.info(f"Sampling report saved to {output_path}")

def check_and_handle_null_results(permanova_results_path: str, output_path: str) -> None:
    """
    Check if PERMANOVA results have any significant drivers and generate a null result report if not.
    
    Args:
        permanova_results_path: Path to PERMANOVA results.
        output_path: Path to save the null result report.
    """
    df = load_permanova_results(permanova_results_path)
    
    # Check if any term has p-value_adj < 0.05
    if 'p-value_adj' in df.columns:
        significant = df[df['p-value_adj'] < 0.05]
    else:
        significant = df[df['p-value'] < 0.05]
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    if significant.empty:
        report = """# Null Result Report

**Analysis**: Environmental Drivers of Fungal Community Structure

**Status**: No Significant Abiotic Drivers Detected

All tested environmental factors had adjusted p-values > 0.05.
No significant association between abiotic factors and fungal community structure was found in this dataset.
"""
        with open(output, 'w') as f:
            f.write(report)
        logger.info(f"Null result report saved to {output_path}")
    else:
        logger.info("Significant drivers found, skipping null result report.")