"""
Collinearity check between prompt token count and structural element count.

This module implements FR-013: diagnose collinearity between token count and
structural element count to ensure they are not perfectly correlated, which
would invalidate separate analysis of these metrics.

Output: Writes correlation coefficient and p-value to data/results/analysis_summary.csv
"""
import os
import csv
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from scipy import stats

from config import Paths
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_collinearity(
    variants_df: pd.DataFrame,
    token_col: str = 'token_count',
    structural_col: str = 'structural_element_count'
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between token count and structural element count.
    
    Args:
        variants_df: DataFrame containing prompt variant data
        token_col: Column name for token counts
        structural_col: Column name for structural element counts
        
    Returns:
        Dictionary with correlation coefficient, p-value, and sample size
    """
    if token_col not in variants_df.columns:
        raise ValueError(f"Column '{token_col}' not found in DataFrame")
    if structural_col not in variants_df.columns:
        raise ValueError(f"Column '{structural_col}' not found in DataFrame")
    
    # Drop rows with missing values
    valid_data = variants_df[[token_col, structural_col]].dropna()
    
    if len(valid_data) < 2:
        raise ValueError("Insufficient data points for correlation analysis")
    
    x = valid_data[token_col]
    y = valid_data[structural_col]
    
    # Calculate Pearson correlation
    correlation, p_value = stats.pearsonr(x, y)
    
    return {
        'correlation_coefficient': correlation,
        'p_value': p_value,
        'sample_size': len(valid_data),
        'token_column': token_col,
        'structural_column': structural_col
    }

def write_summary_to_csv(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write collinearity check results to analysis_summary.csv.
    
    Args:
        results: Dictionary containing correlation results
        output_path: Optional custom output path (defaults to data/results/analysis_summary.csv)
        
    Returns:
        Path to the written CSV file
    """
    if output_path is None:
        output_path = Paths.RESULTS_DIR / 'analysis_summary.csv'
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare row data
    row_data = {
        'analysis_type': 'collinearity_check',
        'metric_1': results['token_column'],
        'metric_2': results['structural_column'],
        'correlation_coefficient': results['correlation_coefficient'],
        'p_value': results['p_value'],
        'sample_size': results['sample_size'],
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Check if file exists to determine if header is needed
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)
    
    logger.info(f"Wrote collinearity check results to {output_path}")
    return output_path

def main() -> None:
    """
    Main entry point for collinearity check.
    
    Loads prompt variants from data/processed/prompt_variants.parquet,
    calculates correlation between token_count and structural_element_count,
    and writes results to data/results/analysis_summary.csv.
    """
    # Load prompt variants
    variants_path = Paths.PROCESSED_DIR / 'prompt_variants.parquet'
    
    if not variants_path.exists():
        raise FileNotFoundError(
            f"Prompt variants file not found at {variants_path}. "
            "Run T018 (storage) first to generate this file."
        )
    
    logger.info(f"Loading prompt variants from {variants_path}")
    variants_df = pd.read_parquet(variants_path)
    
    logger.info(f"Loaded {len(variants_df)} prompt variants")
    
    # Calculate collinearity
    logger.info("Calculating correlation between token count and structural element count")
    results = calculate_collinearity(variants_df)
    
    # Log results
    logger.info(f"Correlation coefficient: {results['correlation_coefficient']:.4f}")
    logger.info(f"P-value: {results['p_value']:.4e}")
    logger.info(f"Sample size: {results['sample_size']}")
    
    # Interpret results
    abs_corr = abs(results['correlation_coefficient'])
    if abs_corr > 0.9:
        logger.warning("HIGH COLLINEARITY DETECTED: Token count and structural element count "
                     "are highly correlated (r > 0.9). Consider using only one metric in analysis.")
    elif abs_corr > 0.7:
        logger.warning("MODERATE COLLINEARITY: Metrics are moderately correlated (0.7 < r < 0.9).")
    else:
        logger.info("LOW COLLINEARITY: Metrics are sufficiently independent for separate analysis.")
    
    # Write to CSV
    output_path = write_summary_to_csv(results)
    logger.info(f"Collinearity check complete. Results written to {output_path}")

if __name__ == '__main__':
    main()