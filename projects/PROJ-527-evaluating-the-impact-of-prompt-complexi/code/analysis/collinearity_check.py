"""
Collinearity check between prompt token count and structural element count.

This module implements FR-013: diagnose collinearity between the two primary
complexity metrics before statistical modeling. High collinearity would
invalidate separate coefficient estimates in the LMM.
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
    token_col: str = "prompt_token_count",
    struct_col: str = "structural_element_count"
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation and p-value between token count and structural count.
    
    Args:
        variants_df: DataFrame containing prompt variants with token and structural counts.
        token_col: Column name for prompt token counts.
        struct_col: Column name for structural element counts.
        
    Returns:
        Dictionary with correlation coefficient, p-value, and sample size.
        
    Raises:
        ValueError: If columns are missing or data is invalid.
    """
    if token_col not in variants_df.columns:
        raise ValueError(f"Column '{token_col}' not found in DataFrame")
    if struct_col not in variants_df.columns:
        raise ValueError(f"Column '{struct_col}' not found in DataFrame")
        
    # Drop rows with missing values
    valid_data = variants_df[[token_col, struct_col]].dropna()
    n = len(valid_data)
    
    if n < 2:
        raise ValueError(f"Insufficient data points for correlation (n={n})")
        
    tokens = valid_data[token_col].values
    structure = valid_data[struct_col].values
    
    # Calculate Pearson correlation
    correlation, p_value = stats.pearsonr(tokens, structure)
    
    logger.info(
        f"Collinearity check: r={correlation:.4f}, p={p_value:.4e}, n={n}"
    )
    
    # Interpret collinearity severity
    if abs(correlation) > 0.8:
        severity = "HIGH"
    elif abs(correlation) > 0.5:
        severity = "MODERATE"
    else:
        severity = "LOW"
        
    return {
        "correlation_coefficient": correlation,
        "p_value": p_value,
        "sample_size": n,
        "severity": severity,
        "token_mean": float(tokens.mean()),
        "token_std": float(tokens.std()),
        "struct_mean": float(structure.mean()),
        "struct_std": float(structure.std())
    }


def write_summary_to_csv(
    results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write collinearity results to CSV file.
    
    Args:
        results: Dictionary from calculate_collinearity().
        output_path: Optional path for output file. Defaults to 
                    data/results/analysis_summary.csv.
                    
    Returns:
        Path to the written CSV file.
    """
    if output_path is None:
        output_path = Paths.RESULTS_DIR / "analysis_summary.csv"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to DataFrame for CSV writing
    df = pd.DataFrame([results])
    df.to_csv(output_path, index=False)
    
    logger.info(f"Wrote collinearity summary to {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point: load prompt variants, calculate collinearity, write results.
    
    This script is designed to be run as:
        python code/analysis/collinearity_check.py
        
    It reads from data/processed/prompt_variants.parquet and writes to
    data/results/analysis_summary.csv.
    """
    from data.storage import load_variants_from_parquet
    
    logger.info("Starting collinearity check analysis")
    
    # Load prompt variants
    variants_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    if not variants_path.exists():
        raise FileNotFoundError(
            f"Prompt variants file not found: {variants_path}. "
            "Run data generation pipeline first."
        )
        
    variants_df = load_variants_from_parquet(variants_path)
    logger.info(f"Loaded {len(variants_df)} prompt variants")
    
    # Calculate collinearity
    results = calculate_collinearity(variants_df)
    
    # Write results
    output_path = write_summary_to_csv(results)
    
    # Log severity warning if high collinearity
    if results["severity"] == "HIGH":
        logger.warning(
            f"HIGH collinearity detected (r={results['correlation_coefficient']:.4f}). "
            "Consider combining metrics or using PCA for downstream analysis."
        )
        
    logger.info("Collinearity check complete")


if __name__ == "__main__":
    main()
