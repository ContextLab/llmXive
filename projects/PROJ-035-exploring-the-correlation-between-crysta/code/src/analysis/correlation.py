"""
Correlation analysis for perovskite descriptors and thermal conductivity.

This module computes Pearson and Spearman correlation coefficients with
multiple-comparison correction using the Bonferroni method.

Usage:
    python src/analysis/correlation.py --input data/results/descriptors.csv --output data/results/correlation_matrix.json --seed 42
"""
import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy import stats

# Import seed management
from src.utils.seed_manager import init_seed, add_seed_argument, get_seed, is_seed_initialized
from src.utils.validation import setup_logger, handle_error
from src.analysis.sensitivity import run_sensitivity_analysis


def compute_correlation_matrix(df: pd.DataFrame, predictors: List[str], target: str = "thermal_conductivity", method: str = "pearson") -> Dict[str, Any]:
    """
    Compute correlation matrix between predictors and target.
    
    Args:
        df: Input dataframe.
        predictors: List of predictor column names.
        target: Target column name.
        method: Correlation method ('pearson' or 'spearman').
    
    Returns:
        Dictionary containing correlation coefficients, p-values, and significance.
    """
    logger = setup_logger(__name__)
    
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataframe")
    
    missing_predictors = [p for p in predictors if p not in df.columns]
    if missing_predictors:
        raise ValueError(f"Missing predictor columns: {missing_predictors}")
    
    # Filter out rows with NaN values
    valid_data = df[predictors + [target]].dropna()
    
    if len(valid_data) < 3:
        logger.warning("Insufficient data for correlation analysis")
        return {
            "correlations": {},
            "p_values": {},
            "significant": {},
            "n_samples": len(valid_data)
        }
    
    correlations = {}
    p_values = {}
    significant = {}
    
    for predictor in predictors:
        if method == "pearson":
            corr, p_val = stats.pearsonr(valid_data[predictor], valid_data[target])
        elif method == "spearman":
            corr, p_val = stats.spearmanr(valid_data[predictor], valid_data[target])
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        correlations[predictor] = float(corr)
        p_values[predictor] = float(p_val)
        significant[predictor] = p_val < 0.05  # Initial significance without correction
    
    # Apply Bonferroni correction
    n_tests = len(predictors)
    adjusted_alpha = 0.05 / n_tests if n_tests > 0 else 0.05
    
    for predictor in predictors:
        significant[predictor] = p_values[predictor] < adjusted_alpha
    
    result = {
        "correlations": correlations,
        "p_values": p_values,
        "significant": significant,
        "n_samples": len(valid_data),
        "method": method,
        "bonferroni_adjusted_alpha": adjusted_alpha
    }
    
    return result


def stratified_correlation_analysis(df: pd.DataFrame, predictors: List[str], target: str = "thermal_conductivity", stratification_col: str = "chemistry_class") -> Dict[str, Any]:
    """
    Perform correlation analysis stratified by a categorical column.
    
    Args:
        df: Input dataframe.
        predictors: List of predictor column names.
        target: Target column name.
        stratification_col: Column name for stratification.
    
    Returns:
        Dictionary with stratified correlation results.
    """
    logger = setup_logger(__name__)
    
    if stratification_col not in df.columns:
        raise ValueError(f"Stratification column '{stratification_col}' not found in dataframe")
    
    results = {}
    
    for category in df[stratification_col].unique():
        if pd.isna(category):
            continue
        
        subset = df[df[stratification_col] == category]
        logger.info(f"Analyzing category: {category} (n={len(subset)})")
        
        if len(subset) < 5:
            logger.warning(f"Insufficient samples for category {category}, skipping")
            continue
        
        category_results = {
            "pearson": compute_correlation_matrix(subset, predictors, target, method="pearson"),
            "spearman": compute_correlation_matrix(subset, predictors, target, method="spearman")
        }
        
        # Run sensitivity analysis for this category
        category_results["sensitivity"] = run_sensitivity_analysis(
            subset, predictors, target, 
            p_values=category_results["pearson"]["p_values"]
        )
        
        results[str(category)] = category_results
    
    return results


def save_correlation_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save correlation results to a JSON file.
    
    Args:
        results: The correlation results dictionary.
        output_path: Path to save the results.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Correlation analysis for perovskite descriptors")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, default="data/results/correlation_matrix.json", help="Output JSON file path")
    parser.add_argument("--predictors", type=str, nargs="+", default=["tolerance_factor", "unit_cell_volume", "bond_length_variance", "avg_tilting_angle"], help="Predictor column names")
    parser.add_argument("--target", type=str, default="thermal_conductivity", help="Target column name")
    parser.add_argument("--stratify-by", type=str, default="chemistry_class", help="Column to stratify by")
    parser = add_seed_argument(parser)
    
    args = parser.parse_args()
    
    # Initialize seed
    init_seed(args.seed)
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger = setup_logger(__name__)
        logger.info(f"Loading data from {input_path}")
        
        df = pd.read_csv(input_path)
        
        logger.info("Performing stratified correlation analysis...")
        
        results = stratified_correlation_analysis(df, args.predictors, args.target, args.stratify_by)
        
        save_correlation_results(results, output_path)
        logger.info(f"Saved correlation results to {output_path}")
        
    except Exception as e:
        handle_error(f"Error in correlation analysis: {e}", level="CRITICAL")
        sys.exit(1)


if __name__ == "__main__":
    main()
