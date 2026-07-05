"""
Sensitivity Analysis: Correlation Calculation for SNR Thresholds.

Implements T030b: Compute correlation (r) for each threshold dataset generated in T030a.
"""
import os
import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from src.utils.config import get_processed_data_dir, get_interim_data_dir
from src.utils.logging import setup_logger

# Configure logger
logger = setup_logger(__name__)


def pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """
    Calculate Pearson correlation coefficient (r) between two lists.
    Returns None if calculation is not possible (e.g., constant values, insufficient data).
    """
    if len(x) != len(y) or len(x) < 2:
        return None
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    sum_y2 = sum(yi ** 2 for yi in y)

    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))

    if denominator == 0:
        return None
    
    return numerator / denominator


def calculate_correlations_for_thresholds(thresholds: List[int]) -> List[Dict]:
    """
    Load sensitivity datasets for each SNR threshold and calculate correlation (r)
    between noise_level_db and complexity metrics.
    
    Args:
        thresholds: List of SNR thresholds (e.g., [5, 10, 15])
        
    Returns:
        List of dicts containing threshold, sample_size, and correlation_r
    """
    processed_dir = get_processed_data_dir()
    results = []
    
    for threshold in thresholds:
        input_file = processed_dir / f"sensitivity_{threshold}db.csv"
        
        if not input_file.exists():
            logger.warning(f"Dataset for threshold {threshold}dB not found: {input_file}")
            results.append({
                "threshold": threshold,
                "sample_size": 0,
                "correlation_r": None
            })
            continue
        
        try:
            df = pd.read_csv(input_file)
            
            # Identify columns
            noise_col = None
            complexity_col = None
            
            # Look for noise level column
            for col in ['noise_level_db', 'noise_level']:
                if col in df.columns:
                    noise_col = col
                    break
            
            # Look for a complexity metric (prefer spectral_entropy, then syllable_count, etc.)
            for col in ['spectral_entropy', 'syllable_count', 'duration', 'bandwidth']:
                if col in df.columns:
                    complexity_col = col
                    break
            
            if noise_col is None or complexity_col is None:
                logger.error(f"Required columns not found in {input_file}. Found: {df.columns.tolist()}")
                results.append({
                    "threshold": threshold,
                    "sample_size": len(df),
                    "correlation_r": None
                })
                continue
            
            # Drop rows with missing values in these columns
            valid_df = df[[noise_col, complexity_col]].dropna()
            sample_size = len(valid_df)
            
            if sample_size < 2:
                logger.warning(f"Insufficient data for threshold {threshold}dB (n={sample_size})")
                results.append({
                    "threshold": threshold,
                    "sample_size": sample_size,
                    "correlation_r": None
                })
                continue
            
            # Calculate correlation
            r = pearson_correlation(valid_df[noise_col].tolist(), valid_df[complexity_col].tolist())
            
            results.append({
                "threshold": threshold,
                "sample_size": sample_size,
                "correlation_r": r
            })
            
            logger.info(f"Threshold {threshold}dB: n={sample_size}, r={r:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing threshold {threshold}dB: {e}")
            results.append({
                "threshold": threshold,
                "sample_size": 0,
                "correlation_r": None
            })
    
    return results


def save_correlation_results(results: List[Dict], output_file: Optional[Path] = None) -> Path:
    """
    Save correlation results to CSV.
    
    Args:
        results: List of result dicts
        output_file: Optional path for output file. Defaults to processed/sensitivity_correlations.csv
        
    Returns:
        Path to the output file
    """
    if output_file is None:
        processed_dir = get_processed_data_dir()
        output_file = processed_dir / "sensitivity_correlations.csv"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["threshold", "sample_size", "correlation_r"]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow({
                "threshold": row["threshold"],
                "sample_size": row["sample_size"],
                "correlation_r": row["correlation_r"] if row["correlation_r"] is not None else ""
            })
    
    logger.info(f"Saved correlation results to {output_file}")
    return output_file


def main():
    """
    Main entry point for T030b: Correlation Calculation for Sensitivity Analysis.
    
    Reads datasets generated by T030a (sensitivity_5db.csv, sensitivity_10db.csv, etc.),
    calculates Pearson correlation (r) for each, and saves results to sensitivity_correlations.csv.
    """
    logger.info("Starting T030b: Correlation Calculation for Sensitivity Analysis")
    
    # Define thresholds to analyze (matching T030a execution)
    thresholds = [5, 10, 15]
    
    # Calculate correlations
    results = calculate_correlations_for_thresholds(thresholds)
    
    # Save results
    output_path = save_correlation_results(results)
    
    logger.info(f"T030b completed. Results saved to {output_path}")
    
    # Print summary
    print("\nSensitivity Analysis Correlation Results:")
    print("-" * 50)
    print(f"{'Threshold (dB)':<15} {'Sample Size':<15} {'Correlation (r)':<15}")
    print("-" * 50)
    for res in results:
        r_str = f"{res['correlation_r']:.4f}" if res['correlation_r'] is not None else "N/A"
        print(f"{res['threshold']:<15} {res['sample_size']:<15} {r_str:<15}")
    print("-" * 50)
    
    return results


if __name__ == "__main__":
    main()
