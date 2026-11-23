"""
Regression analysis module for modeling the relationship between centrality and motor memory.
Implements float32 optimization and batch processing.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.config import get_output_paths, get_regression_config
from analysis.optimization_utils import (
    ensure_float32,
    optimize_memory_usage,
    validate_float32_compliance
)

logger = logging.getLogger(__name__)

def load_behavioral_data(file_path: str) -> pd.DataFrame:
    """
    Load behavioral data from CSV file.
    
    Args:
        file_path: Path to behavioral data CSV
        
    Returns:
        DataFrame with behavioral metrics
    """
    df = pd.read_csv(file_path)
    df = optimize_memory_usage(df)
    logger.info(f"Loaded behavioral data: {len(df)} subjects")
    return df

def load_centrality_or_pca_data(file_path: str) -> pd.DataFrame:
    """
    Load centrality or PCA data from CSV file.
    
    Args:
        file_path: Path to centrality/PCA data CSV
        
    Returns:
        DataFrame with centrality metrics
    """
    df = pd.read_csv(file_path)
    df = optimize_memory_usage(df)
    logger.info(f"Loaded centrality/PCA data: {len(df)} rows")
    return df

def load_mean_fd_data(file_path: str) -> pd.DataFrame:
    """
    Load mean FD data from CSV file.
    
    Args:
        file_path: Path to mean FD CSV
        
    Returns:
        DataFrame with mean FD values
    """
    df = pd.read_csv(file_path)
    df = optimize_memory_usage(df)
    logger.info(f"Loaded mean FD data: {len(df)} subjects")
    return df

def merge_all_data(
    behavioral_df: pd.DataFrame,
    centrality_df: pd.DataFrame,
    fd_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge all data sources on subject_id.
    
    Args:
        behavioral_df: Behavioral data DataFrame
        centrality_df: Centrality or PCA data DataFrame
        fd_df: Mean FD data DataFrame
        
    Returns:
        Merged DataFrame
    """
    # Merge behavioral with centrality
    merged = pd.merge(behavioral_df, centrality_df, on='subject_id', how='inner')
    
    # Merge with FD
    merged = pd.merge(merged, fd_df, on='subject_id', how='inner')
    
    # Optimize memory
    merged = optimize_memory_usage(merged)
    
    # Validate float32 compliance
    is_compliant, dtype_info = validate_float32_compliance(merged)
    if not is_compliant:
        logger.warning("Merged data contains non-float32 columns: {}".format(dtype_info))
    
    logger.info(f"Merged data: {len(merged)} subjects, {len(merged.columns)} columns")
    return merged

def fit_linear_regression(
    data: pd.DataFrame,
    formula: str
) -> sm.OLSResults:
    """
    Fit a linear regression model.
    
    Args:
        data: DataFrame with variables
        formula: Statsmodels formula string
        
    Returns:
        Fitted model results
    """
    # Ensure float32 for numeric columns
    data = ensure_float32(data)
    
    # Fit model
    model = smf.ols(formula, data=data)
    results = model.fit()
    
    logger.info(f"Linear regression fitted: {formula}")
    logger.info(f"R-squared: {results.rsquared:.4f}")
    
    return results

def save_regression_summary(
    results: sm.OLSResults,
    output_file: str
):
    """
    Save regression summary to CSV.
    
    Args:
        results: Fitted model results
        output_file: Path to output CSV
    """
    # Extract summary data
    summary_data = []
    
    for name, param in results.params.items():
        summary_data.append({
            'term': name,
            'coefficient': float(param),
            'std_err': float(results.bse[name]),
            't_value': float(results.tvalues[name]),
            'p_value': float(results.pvalues[name])
        })
    
    df = pd.DataFrame(summary_data)
    df = optimize_memory_usage(df)
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    logger.info(f"Saved regression summary to {output_file}")

def generate_scatter_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_file: str,
    model_results: Optional[sm.OLSResults] = None
):
    """
    Generate scatter plot with regression line.
    
    Args:
        data: DataFrame with data
        x_col: X-axis column name
        y_col: Y-axis column name
        output_file: Path to output image
        model_results: Optional fitted model for regression line
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=data, x=x_col, y=y_col, alpha=0.6)
    
    if model_results is not None:
        # Add regression line
        sns.regplot(data=data, x=x_col, y=y_col, scatter=False, color='red')
    
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f'{y_col} vs {x_col}')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    
    logger.info(f"Saved scatter plot to {output_file}")

def run_regression_analysis(
    behavioral_file: str,
    centrality_file: str,
    fd_file: str,
    model_predictors_file: str,
    output_summary_file: str,
    output_plot_file: str
):
    """
    Run full regression analysis pipeline.
    
    Args:
        behavioral_file: Path to behavioral data CSV
        centrality_file: Path to centrality/PCA data CSV
        fd_file: Path to mean FD CSV
        model_predictors_file: Path to model predictors CSV
        output_summary_file: Path to output summary CSV
        output_plot_file: Path to output plot image
    """
    # Load data
    behavioral_df = load_behavioral_data(behavioral_file)
    centrality_df = load_centrality_or_pca_data(centrality_file)
    fd_df = load_mean_fd_data(fd_file)
    
    # Merge data
    merged_df = merge_all_data(behavioral_df, centrality_df, fd_df)
    
    # Get model formula from predictors file
    predictors_df = pd.read_csv(model_predictors_file)
    model_type = predictors_df['model_type'].iloc[0]
    formula_string = predictors_df['formula_string'].iloc[0]
    
    logger.info(f"Using model type: {model_type}")
    logger.info(f"Formula: {formula_string}")
    
    # Fit model
    results = fit_linear_regression(merged_df, formula_string)
    
    # Save summary
    save_regression_summary(results, output_summary_file)
    
    # Generate plot
    # Extract predictor and target names from formula
    terms = formula_string.split('~')
    if len(terms) == 2:
        y_col = terms[0].strip()
        x_cols = [t.strip() for t in terms[1].split('+')]
        x_col = x_cols[0]  # First predictor
        
        generate_scatter_plot(
            merged_df,
            x_col,
            y_col,
            output_plot_file,
            results
        )
    
    logger.info("Regression analysis complete")
    return results

def main():
    """Main entry point for regression analysis."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Regression analysis module loaded")
    logger.info("Functions available: load_behavioral_data, load_centrality_or_pca_data, "
               "load_mean_fd_data, merge_all_data, fit_linear_regression, "
               "save_regression_summary, generate_scatter_plot, run_regression_analysis")

if __name__ == "__main__":
    main()
