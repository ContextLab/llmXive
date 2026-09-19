import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from config_manager import get_results_path, get_data_processed_path, get_config
from logging_config import get_logger

# Configure matplotlib for non-interactive backend (critical for CI/server)
plt.switch_backend('Agg')
sns.set_theme(style="whitegrid", context="talk")

logger = get_logger(__name__)

def load_csv_safely(path: Path) -> Optional[pd.DataFrame]:
    """Safely load a CSV file, returning None if it doesn't exist or is empty."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        df = pd.read_csv(path)
        if df.empty:
            logger.warning(f"File is empty: {path}")
            return None
        return df
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return None

def load_results_from_files() -> Dict[str, Any]:
    """
    Load all necessary result files for plotting and reporting.
    Returns a dictionary containing:
      - 'primary_model': DataFrame from results/primary_model.csv
      - 'bootstrap': DataFrame from results/bootstrap_results.csv
      - 'alpha_sweep': DataFrame from results/alpha_sweep.csv
      - 'covariate': DataFrame from results/covariate_model.csv
      - 'binary': DataFrame from results/binary_model.csv
      - 'power': DataFrame from results/power_analysis.csv
      - 'imputed_data': DataFrame from data/processed/imputed_data.csv
    """
    results_path = get_results_path()
    processed_path = get_data_processed_path()
    
    results = {}
    
    # Load primary model
    primary_path = results_path / "primary_model.csv"
    results['primary_model'] = load_csv_safely(primary_path)
    
    # Load bootstrap results
    bootstrap_path = results_path / "bootstrap_results.csv"
    results['bootstrap'] = load_csv_safely(bootstrap_path)
    
    # Load alpha sweep
    alpha_path = results_path / "alpha_sweep.csv"
    results['alpha_sweep'] = load_csv_safely(alpha_path)
    
    # Load covariate model
    covariate_path = results_path / "covariate_model.csv"
    results['covariate'] = load_csv_safely(covariate_path)
    
    # Load binary model
    binary_path = results_path / "binary_model.csv"
    results['binary'] = load_csv_safely(binary_path)
    
    # Load power analysis
    power_path = results_path / "power_analysis.csv"
    results['power'] = load_csv_safely(power_path)
    
    # Load imputed data for interaction plot
    imputed_path = processed_path / "imputed_data.csv"
    results['imputed_data'] = load_csv_safely(imputed_path)
    
    return results

def generate_interaction_plot(df: pd.DataFrame, output_path: Path) -> str:
    """
    Generate an interaction plot showing the relationship between 
    news exposure and IAT score across political ideologies.
    
    Args:
        df: Imputed data containing 'IAT_D_score', 'news_exposure_z', 'political_ideology'
        output_path: Path to save the plot (PNG)
        
    Returns:
        Relative path to the saved plot
    """
    if df is None or df.empty:
        logger.error("Cannot generate interaction plot: No data provided")
        return ""
        
    required_cols = ['IAT_D_score', 'news_exposure_z', 'political_ideology']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Interaction plot missing required columns. Found: {df.columns.tolist()}")
        return ""
        
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate binned means for cleaner visualization
        df_plot = df.copy()
        df_plot['ideology_bin'] = pd.qcut(df_plot['political_ideology'], q=3, labels=['Left', 'Center', 'Right'], duplicates='drop')
        
        # If qcut fails due to too few unique values, use a simple split
        if 'ideology_bin' not in df_plot.columns:
            median_val = df_plot['political_ideology'].median()
            df_plot['ideology_bin'] = df_plot['political_ideology'].apply(
                lambda x: 'Left' if x < median_val else 'Right'
            )
        
        # Group by ideology bin and calculate mean and std for news exposure bins
        sns.lineplot(
            data=df_plot,
            x='news_exposure_z',
            y='IAT_D_score',
            hue='ideology_bin',
            ax=ax,
            ci=68, # 68% confidence interval approx 1 SD
            marker='o',
            palette='Set2'
        )
        
        ax.set_xlabel('News Exposure (Z-scored)', fontsize=12)
        ax.set_ylabel('Implicit Bias (IAT D-Score)', fontsize=12)
        ax.set_title('Interaction: News Exposure × Political Ideology on Implicit Bias', fontsize=14)
        ax.legend(title='Political Ideology', title_fontsize=12)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Interaction plot saved to: {output_path}")
        return output_path.name
        
    except Exception as e:
        logger.error(f"Failed to generate interaction plot: {e}", exc_info=True)
        return ""

def generate_bootstrap_plot(bootstrap_data: pd.DataFrame, output_path: Path) -> str:
    """
    Generate a distribution plot of the bootstrap interaction coefficients.
    
    Args:
        bootstrap_data: DataFrame containing bootstrap resamples with interaction term coefficients
        output_path: Path to save the plot (PNG)
        
    Returns:
        Relative path to the saved plot
    """
    if bootstrap_data is None or bootstrap_data.empty:
        logger.error("Cannot generate bootstrap plot: No data provided")
        return ""
        
    # Identify the interaction coefficient column
    interaction_col = None
    for col in bootstrap_data.columns:
        if 'interaction' in col.lower() or 'news' in col.lower() and 'ideology' in col.lower():
            interaction_col = col
            break
        
    # Fallback: look for the last column if no specific match
    if interaction_col is None and len(bootstrap_data.columns) > 0:
        interaction_col = bootstrap_data.columns[-1]
        
    if interaction_col is None:
        logger.error("Cannot identify interaction coefficient column in bootstrap data")
        return ""
        
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot distribution
        sns.histplot(
            data=bootstrap_data,
            x=interaction_col,
            kde=True,
            ax=ax,
            color='steelblue',
            alpha=0.7
        )
        
        # Add mean line
        mean_val = bootstrap_data[interaction_col].mean()
        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.4f}')
        
        # Add confidence interval lines
        ci_lower = bootstrap_data[interaction_col].quantile(0.025)
        ci_upper = bootstrap_data[interaction_col].quantile(0.975)
        ax.axvline(ci_lower, color='green', linestyle=':', linewidth=2, label=f'95% CI Lower: {ci_lower:.4f}')
        ax.axvline(ci_upper, color='green', linestyle=':', linewidth=2, label=f'95% CI Upper: {ci_upper:.4f}')
        
        ax.set_xlabel('Bootstrap Interaction Coefficient', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Bootstrap Distribution of Interaction Effect (News Exposure × Ideology)', fontsize=14)
        ax.legend(loc='best')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Bootstrap plot saved to: {output_path}")
        return output_path.name
        
    except Exception as e:
        logger.error(f"Failed to generate bootstrap plot: {e}", exc_info=True)
        return ""

def render_report_html(results: Dict[str, Any], plot_paths: Dict[str, str], output_path: Path) -> None:
    """
    Render the final report HTML using Jinja2 template.
    
    Args:
        results: Dictionary of loaded results DataFrames
        plot_paths: Dictionary mapping plot types to their file names
        output_path: Path to save the HTML report
    """
    # Setup Jinja2 environment
    template_dir = Path('code/templates')
    if not template_dir.exists():
        logger.error(f"Template directory not found: {template_dir}")
        return
        
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report.j2')
    
    # Prepare context for template
    context = {
        'primary_model': results.get('primary_model'),
        'bootstrap': results.get('bootstrap'),
        'alpha_sweep': results.get('alpha_sweep'),
        'covariate': results.get('covariate'),
        'binary': results.get('binary'),
        'power': results.get('power'),
        'plots': plot_paths,
        'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        html_content = template.render(context)
        output_path.write_text(html_content, encoding='utf-8')
        logger.info(f"Report HTML saved to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to render report HTML: {e}", exc_info=True)

def save_report_html(html_path: Path, pdf_path: Path) -> None:
    """
    Convert HTML report to PDF (placeholder for actual conversion logic).
    In a real implementation, this would use a tool like wkhtmltopdf or WeasyPrint.
    For now, we just copy the HTML as a text file if PDF conversion isn't available.
    """
    if not html_path.exists():
        logger.error(f"Source HTML not found: {html_path}")
        return
        
    try:
        # Attempt to convert to PDF if a converter is available
        # This is a simplified version; real implementation would use external tools
        logger.warning("PDF conversion not fully implemented. HTML report generated instead.")
        
        # For the purpose of this task, we ensure the HTML exists and note the PDF constraint
        # In a full implementation, we would call:
        # subprocess.run(['wkhtmltopdf', str(html_path), str(pdf_path)])
        
        # As a fallback, we create a placeholder PDF note
        with open(pdf_path, 'w') as f:
            f.write(f"PDF Report Placeholder\n")
            f.write(f"Source: {html_path}\n")
            f.write(f"Note: Full PDF conversion requires external tool (wkhtmltopdf/WeasyPrint)\n")
            
        logger.info(f"PDF placeholder saved to: {pdf_path}")
        
    except Exception as e:
        logger.error(f"Failed to save report PDF: {e}", exc_info=True)

def run_reporting_pipeline() -> None:
    """
    Execute the full reporting pipeline:
    1. Load all results
    2. Generate plots
    3. Render HTML report
    4. Save PDF (placeholder)
    """
    logger.info("Starting reporting pipeline...")
    
    results_path = get_results_path()
    plots_path = results_path / "plots"
    plots_path.mkdir(parents=True, exist_ok=True)
    
    # Load results
    results = load_results_from_files()
    if not results or not any(v is not None for v in results.values()):
        logger.error("No results found to generate report. Pipeline aborted.")
        return
        
    # Generate plots
    plot_paths = {}
    
    # Interaction plot
    if results.get('imputed_data') is not None:
        interaction_plot_path = plots_path / "interaction_plot.png"
        plot_name = generate_interaction_plot(results['imputed_data'], interaction_plot_path)
        if plot_name:
            plot_paths['interaction'] = plot_name
    
    # Bootstrap plot
    if results.get('bootstrap') is not None:
        bootstrap_plot_path = plots_path / "bootstrap_distribution.png"
        plot_name = generate_bootstrap_plot(results['bootstrap'], bootstrap_plot_path)
        if plot_name:
            plot_paths['bootstrap'] = plot_name
            
    # Render HTML report
    html_path = results_path / "report.html"
    render_report_html(results, plot_paths, html_path)
    
    # Save PDF (placeholder)
    pdf_path = results_path / "report.pdf"
    save_report_html(html_path, pdf_path)
    
    logger.info("Reporting pipeline completed.")

def main():
    """Entry point for the reporting module."""
    setup_logging()
    run_reporting_pipeline()

if __name__ == "__main__":
    main()
