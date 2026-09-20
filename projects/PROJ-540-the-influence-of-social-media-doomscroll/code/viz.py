"""
Visualization module for the Doomscrolling Anxiety study.
Generates scatter plots, regression lines, and diagnostic plots.
"""
import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional

from model import fit_regression_model, check_assumptions

logger = logging.getLogger(__name__)

def load_processed_data(input_path: Path) -> pd.DataFrame:
    """Loads processed data."""
    logger.info(f"Loading data from {input_path}")
    return pd.read_csv(input_path)

def plot_scatter_with_regression(df: pd.DataFrame, x: str = 'news_exposure_freq', y: str = 'anxiety_score', output_path: Optional[Path] = None) -> Path:
    """
    Generates a scatter plot with regression line and 95% CI.

    Args:
        df: DataFrame.
        x: X-axis column.
        y: Y-axis column.
        output_path: Path to save the plot.

    Returns:
        Path to the saved plot.
    """
    plt.figure(figsize=(10, 6))
    sns.regplot(data=df, x=x, y=y, ci=95, scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
    plt.title(f'{y} vs {x}')
    plt.xlabel(x)
    plt.ylabel(y)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path)
        logger.info(f"Plot saved to {output_path}")
    
    plt.close()
    return output_path

def plot_robustness_comparison(full_df: pd.DataFrame, subset_df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Generates a comparison plot for robustness check.
    Overlays full sample and high-engagement subset with distinct regression lines.

    Args:
        full_df: Full DataFrame.
        subset_df: High-engagement subset DataFrame.
        output_path: Path to save the plot.

    Returns:
        Path to the saved plot.
    """
    plt.figure(figsize=(12, 8))
    x_col = 'news_exposure_freq'
    y_col = 'anxiety_score'

    # Plot full sample
    sns.regplot(data=full_df, x=x_col, y=y_col, scatter=False, color='blue', label='Full Sample', line_kws={'linestyle':'--'})
    sns.scatterplot(data=full_df, x=x_col, y=y_col, color='blue', alpha=0.3, label='Full Sample Data')

    # Plot subset
    sns.regplot(data=subset_df, x=x_col, y=y_col, scatter=False, color='red', label='High Engagement Subset', line_kws={'linestyle':'-'})
    sns.scatterplot(data=subset_df, x=x_col, y=y_col, color='red', alpha=0.6, label='High Engagement Data')

    plt.title('Robustness Check: Full Sample vs High Engagement Subset')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.legend()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path)
        logger.info(f"Robustness plot saved to {output_path}")
    
    plt.close()
    return output_path

def plot_diagnostics(df: pd.DataFrame, model_results: dict, output_dir: Path) -> None:
    """
    Generates diagnostic plots: Residuals vs Fitted and Q-Q Plot.
    Includes test statistics in titles.

    Args:
        df: DataFrame used for model.
        model_results: Dictionary containing model results (needs formula).
        output_dir: Directory to save plots.
    """
    from statsmodels.formula.api import ols
    
    # Refit to get residuals easily
    formula = model_results.get('formula', 'anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender')
    model = ols(formula, data=df).fit()
    residuals = model.resid
    fitted = model.fittedvalues

    # Get stats for title
    # Re-run assumptions to get stats if not in model_results directly
    # Assuming model_results has 'assumptions' key if populated, else re-calc
    # For simplicity in this helper, we assume we can re-calc or extract from model_results if available
    # If not, we just use generic titles or re-run check_assumptions logic briefly
    
    # Re-calc for stats
    from statsmodels.stats.diagnostic import het_breuschpagan
    from scipy import stats as sp_stats
    
    bp_test = het_breuschpagan(residuals, model.model.exog)
    shapiro_stat, shapiro_p = sp_stats.shapiro(residuals)

    # Plot 1: Residuals vs Fitted
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(fitted, residuals, alpha=0.5)
    ax.axhline(0, color='red', linestyle='--')
    ax.set_title(f"Residuals vs Fitted (BP p={bp_test[1]:.3f})")
    ax.set_xlabel("Fitted Values")
    ax.set_ylabel("Residuals")
    
    path1 = output_dir / 'diagnostics_residuals.png'
    path1.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path1)
    logger.info(f"Saved {path1}")
    plt.close()

    # Plot 2: Q-Q Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sm.qqplot(residuals, line='s', ax=ax)
    ax.set_title(f"Q-Q Plot (Shapiro p={shapiro_p:.3f})")
    
    path2 = output_dir / 'diagnostics_qq.png'
    path2.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(path2)
    logger.info(f"Saved {path2}")
    plt.close()

def main():
    """
    Main entry point for visualization.
    """
    from config import load_config, ensure_directories
    import json
    
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    output_plot = Path(config['paths']['outputs']) / 'plot.png'
    output_diag_dir = Path(config['paths']['outputs'])
    output_robust = Path(config['paths']['outputs']) / 'robustness_comparison.png'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found: {input_path}")
    
    df = load_processed_data(input_path)
    
    # Main Scatter
    plot_scatter_with_regression(df, output_path=output_plot)
    
    # Diagnostics
    # Load regression results to get formula/stats
    reg_path = Path(config['paths']['outputs']) / 'regression_results.json'
    if reg_path.exists():
        with open(reg_path) as f:
            reg_data = json.load(f)
        plot_diagnostics(df, reg_data, output_diag_dir)
    else:
        logger.warning("Regression results not found. Skipping diagnostics plots.")
    
    # Robustness Plot (if data exists)
    if 'social_media_engagement' in df.columns:
        from robustness import calculate_engagement_correlation, select_high_engagement_subset
        corr = calculate_engagement_correlation(df)
        if corr and corr > 0.3:
            try:
                subset = select_high_engagement_subset(df)
                plot_robustness_comparison(df, subset, output_robust)
            except Exception as e:
                logger.warning(f"Could not generate robustness plot: {e}")
        else:
            logger.info("Robustness check skipped or correlation low. No robustness plot generated.")

if __name__ == '__main__':
    main()
