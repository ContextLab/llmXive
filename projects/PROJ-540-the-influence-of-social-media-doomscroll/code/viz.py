"""
Visualization module for the Doomscrolling Anxiety Analysis Pipeline.
Generates scatter plots, diagnostic plots, and robustness comparisons.
"""
import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load processed data for visualization."""
    path = Path("data/processed/analysis_data.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}")
    return pd.read_csv(path)

def plot_scatter_with_regression(df: pd.DataFrame, results: dict = None):
    """
    Generate scatter plot with regression line and 95% CI.
    Saves to outputs/plot.png
    """
    logger.info("Generating scatter plot with regression line...")
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract variables
    x = df['news_exposure_freq']
    y = df['anxiety_score']
    
    # Scatter plot
    sns.scatterplot(x=x, y=y, ax=ax, alpha=0.6, s=50, edgecolor='k', linewidth=0.5)
    
    # Regression line
    if results is None:
        # Fit simple regression for plot
        model = smf.ols('anxiety_score ~ news_exposure_freq', data=df).fit()
    else:
        model = smf.ols('anxiety_score ~ news_exposure_freq', data=df).fit()
    
    # Create line points
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = model.params['Intercept'] + model.params['news_exposure_freq'] * x_line
    
    # Plot regression line
    ax.plot(x_line, y_line, color='red', linewidth=2, label='Regression Line')
    
    # 95% Confidence Interval
    pred = model.get_prediction(sm.add_constant(x_line))
    ci = pred.conf_int(alpha=0.05)
    ax.fill_between(x_line, ci[:, 0], ci[:, 1], color='red', alpha=0.2, label='95% CI')
    
    # Labels and title
    ax.set_xlabel('News Exposure Frequency', fontsize=12)
    ax.set_ylabel('Anxiety Score', fontsize=12)
    ax.set_title('News Exposure vs. Anxiety Score with Regression Line', fontsize=14)
    ax.legend()
    
    # Save plot
    output_path = Path("outputs/plot.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to: {output_path}")

def plot_diagnostics(results: dict):
    """
    Generate diagnostic plots: Residuals vs Fitted and Q-Q Plot.
    Saves to outputs/diagnostics_residuals.png and outputs/diagnostics_qq.png
    """
    logger.info("Generating diagnostic plots...")
    
    # Load data and refit model for diagnostics
    df = load_processed_data()
    formula = results.get('regression', {}).get('formula', 'anxiety_score ~ news_exposure_freq + age + gender')
    model = smf.ols(formula, data=df).fit()
    
    residuals = model.resid
    fitted = model.fittedvalues
    
    # Get test statistics for titles
    bp_stat = results.get('regression', {}).get('assumptions', {}).get('homoscedasticity', {}).get('statistic', 'N/A')
    shapiro_stat = results.get('regression', {}).get('assumptions', {}).get('normality', {}).get('statistic', 'N/A')
    
    # 1. Residuals vs Fitted
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(fitted, residuals, alpha=0.6, edgecolor='k', linewidth=0.5)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=2)
    ax.set_xlabel('Fitted Values', fontsize=12)
    ax.set_ylabel('Residuals', fontsize=12)
    title = f'Residuals vs Fitted (Breusch-Pagan stat: {bp_stat:.4f} if available)'
    ax.set_title(title, fontsize=14)
    ax.grid(True, alpha=0.3)
    
    output_path = Path("outputs/diagnostics_residuals.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Residuals plot saved to: {output_path}")
    
    # 2. Q-Q Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    sm.qqplot(residuals, line='s', ax=ax)
    ax.set_title(f'Q-Q Plot of Residuals (Shapiro-Wilk stat: {shapiro_stat} if available)', fontsize=14)
    
    output_path = Path("outputs/diagnostics_qq.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Q-Q plot saved to: {output_path}")

def plot_robustness_comparison(df: pd.DataFrame, full_results: dict, robustness_results: dict):
    """
    Generate robustness comparison plot.
    Overlay subset data with different color and plot two regression lines.
    Saves to outputs/robustness_comparison.png
    """
    logger.info("Generating robustness comparison plot...")
    
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Full sample
    x_full = df['news_exposure_freq']
    y_full = df['anxiety_score']
    sns.scatterplot(x=x_full, y=y_full, ax=ax, alpha=0.4, s=40, color='blue', label='Full Sample')
    
    # Subset (high engagement)
    if robustness_results.get('status') != 'run':
        logger.warning("No subset data available for comparison.")
        plt.close()
        return
    
    subset_n = robustness_results.get('subset', {}).get('n', 0)
    if subset_n == 0:
        logger.warning("Subset size is 0.")
        plt.close()
        return
    
    # Re-create subset for plotting
    if 'social_media_engagement' in df.columns:
        threshold = df['social_media_engagement'].quantile(0.75)
        subset_df = df[df['social_media_engagement'] >= threshold]
        
        x_sub = subset_df['news_exposure_freq']
        y_sub = subset_df['anxiety_score']
        sns.scatterplot(x=x_sub, y=y_sub, ax=ax, alpha=0.8, s=60, color='red', label='High Engagement Subset')
        
        # Full sample regression line
        formula_full = full_results.get('regression', {}).get('formula', 'anxiety_score ~ news_exposure_freq')
        model_full = smf.ols(formula_full, data=df).fit()
        x_line = np.linspace(x_full.min(), x_full.max(), 100)
        y_line = model_full.params['Intercept'] + model_full.params.get('news_exposure_freq', 0) * x_line
        ax.plot(x_line, y_line, color='blue', linewidth=2, linestyle='-', label='Full Sample Regression')
        
        # Subset regression line
        model_sub = smf.ols(formula_full, data=subset_df).fit()
        y_line_sub = model_sub.params['Intercept'] + model_sub.params.get('news_exposure_freq', 0) * x_line
        ax.plot(x_line, y_line_sub, color='red', linewidth=2, linestyle='--', label='Subset Regression')
        
        # Labels and title
        ax.set_xlabel('News Exposure Frequency', fontsize=12)
        ax.set_ylabel('Anxiety Score', fontsize=12)
        ax.set_title(f'Robustness Check: Full Sample vs High Engagement Subset (N={subset_n})', fontsize=14)
        ax.legend()
        
        output_path = Path("outputs/robustness_comparison.png")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Robustness comparison plot saved to: {output_path}")
    else:
        logger.warning("social_media_engagement not found in data.")
        plt.close()

def main():
    """CLI entry point for visualization."""
    try:
        df = load_processed_data()
        
        # Load results
        results_path = Path("outputs/regression_results.json")
        if results_path.exists():
            import json
            with open(results_path, 'r') as f:
                results = json.load(f)
        else:
            results = None
        
        plot_scatter_with_regression(df, results)
        if results:
            plot_diagnostics(results)
        
        # Robustness plot
        robustness_path = Path("outputs/robustness_results.json")
        if robustness_path.exists():
            import json
            with open(robustness_path, 'r') as f:
                robustness_results = json.load(f)
            if robustness_results.get('status') == 'run':
                plot_robustness_comparison(df, results, robustness_results)
        
        logger.info("Visualization complete.")
        return 0
    except Exception as e:
        logger.error(f"Error during visualization: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
