"""
T020: Implement correlation check between token count and structural element count.

This module diagnoses collinearity (FR-013) between prompt token count and
structural element count. It loads the generated prompt variants from the
parquet file, computes the Pearson correlation coefficient, and writes the
result to data/results/analysis_summary.csv.
"""
import os
import csv
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from scipy import stats

# Import from project modules
from config import Paths
from data.storage import load_variants_from_parquet
from utils.logger import get_logger

logger = get_logger(__name__)

def calculate_collinearity(
    df: pd.DataFrame,
    token_col: str = "prompt_token_count",
    struct_col: str = "structural_element_count"
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation between token count and structural element count.
    
    Args:
        df: DataFrame containing prompt variant data.
        token_col: Column name for token counts.
        struct_col: Column name for structural element counts.
        
    Returns:
        Dictionary with correlation coefficient, p-value, and sample size.
    """
    if token_col not in df.columns or struct_col not in df.columns:
        raise ValueError(
            f"Required columns not found. "
            f"Expected '{token_col}' and '{struct_col}' in {df.columns.tolist()}"
        )
    
    # Drop rows with missing values in either column
    valid_data = df[[token_col, struct_col]].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data points for correlation calculation.")
        return {
            "correlation": None,
            "p_value": None,
            "sample_size": len(valid_data),
            "status": "insufficient_data"
        }
    
    # Calculate Pearson correlation
    correlation, p_value = stats.pearsonr(
        valid_data[token_col], 
        valid_data[struct_col]
    )
    
    logger.info(
        f"Collinearity check: r={correlation:.4f}, p={p_value:.4f}, n={len(valid_data)}"
    )
    
    return {
        "correlation": correlation,
        "p_value": p_value,
        "sample_size": len(valid_data),
        "status": "success"
    }

def write_summary_to_csv(
    result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write the correlation analysis result to a CSV file.
    
    Args:
        result: Dictionary containing correlation metrics.
        output_path: Path to the output CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare row data
    row = {
        "metric": "prompt_token_vs_structural_element_correlation",
        "correlation_coefficient": result.get("correlation"),
        "p_value": result.get("p_value"),
        "sample_size": result.get("sample_size"),
        "status": result.get("status"),
        "description": "Pearson correlation between prompt token count and structural element count (FR-013)"
    }
    
    # Check if file exists to determine if header is needed
    write_header = not output_path.exists()
    
    with open(output_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    
    logger.info(f"Analysis summary written to {output_path}")

def main() -> None:
    """
    Main entry point for T020.
    
    1. Load prompt variants from parquet.
    2. Calculate correlation between token count and structural element count.
    3. Write results to data/results/analysis_summary.csv.
    """
    logger.info("Starting T020: Collinearity Check")
    
    # Load data
    variants_path = Paths.PROCESSED_DATA_DIR / "prompt_variants.parquet"
    
    if not variants_path.exists():
        logger.error(f"Data file not found: {variants_path}")
        logger.error("Run T018 (storage) before running T020.")
        raise FileNotFoundError(
            f"Required data file not found: {variants_path}. "
            "Ensure T018 has completed successfully."
        )
    
    logger.info(f"Loading variants from {variants_path}")
    df = load_variants_from_parquet(variants_path)
    logger.info(f"Loaded {len(df)} variants")
    
    # Calculate correlation
    result = calculate_collinearity(df)
    
    # Write to summary CSV
    summary_path = Paths.RESULTS_DIR / "analysis_summary.csv"
    write_summary_to_csv(result, summary_path)
    
    logger.info("T020 completed successfully")

if __name__ == "__main__":
    main()
