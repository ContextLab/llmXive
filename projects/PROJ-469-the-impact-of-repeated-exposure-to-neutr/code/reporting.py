import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config_manager import get_results_path, get_config, get_data_processed_path
from logging_config import get_logger

logger = get_logger(__name__)

def load_results_from_files() -> Dict[str, Any]:
    """
    Load all result CSVs from the results directory into a dictionary.
    Returns a dict with keys: 'model_summary', 'diagnostics', 'robustness', 'power_analysis', 'binary_model'.
    """
    results_path = get_results_path()
    data = {}

    # Map expected filenames to keys
    file_map = {
        'model_summary.csv': 'model_summary',
        'diagnostics.csv': 'diagnostics',
        'robustness_metrics.csv': 'robustness',
        'power_analysis.csv': 'power_analysis',
        'binary_model.csv': 'binary_model'
    }

    for filename, key in file_map.items():
        filepath = results_path / filename
        if filepath.exists():
            try:
                data[key] = pd.read_csv(filepath)
                logger.info(f"Loaded {filename} into {key}")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
                data[key] = pd.DataFrame()
        else:
            logger.warning(f"Result file not found: {filename}")
            data[key] = pd.DataFrame()

    return data

def generate_interaction_plot(
    model_summary: pd.DataFrame,
    output_path: Path,
    figsize: Tuple[int, int] = (10, 6)
) -> Optional[Path]:
    """
    Generates an interaction plot based on the primary model results.
    Since the primary model uses continuous variables (z-scored news exposure and continuous ideology),
    we simulate a plot by creating a grid of values across the range of the data to show the predicted interaction.
    
    This function assumes the model_summary contains coefficients for:
    - Intercept
    - news_exposure_z
    - political_ideology
    - news_exposure_z:political_ideology
    
    If the model_summary is empty or missing these columns, it returns None.
    """
    if model_summary.empty:
        logger.warning("model_summary is empty, cannot generate interaction plot.")
        return None

    # Check for required coefficients
    required_terms = ['news_exposure_z', 'political_ideology', 'news_exposure_z:political_ideology']
    if not all(term in model_summary['term'].values for term in required_terms):
        logger.warning("Model summary missing required interaction terms.")
        return None

    # Extract coefficients
    coeffs = model_summary.set_index('term')['coef']
    intercept = coeffs.get('Intercept', 0)
    beta_exposure = coeffs.get('news_exposure_z', 0)
    beta_ideology = coeffs.get('political_ideology', 0)
    beta_interaction = coeffs.get('news_exposure_z:political_ideology', 0)

    # Create a grid for plotting
    # We'll use the range of ideology (-2 to 2 standard deviations)
    ideology_vals = np.linspace(-2, 2, 100)
    
    # Plot for different levels of news exposure (low, medium, high)
    # Assuming news_exposure_z is roughly in the same range
    exposure_levels = [-1, 0, 1]  # Low, Medium, High
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    labels = ['Low Exposure', 'Medium Exposure', 'High Exposure']

    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")

    for exp_val, color, label in zip(exposure_levels, colors, labels):
        # Calculate predicted IAT_D_score
        # IAT = Intercept + beta_exp * exp_val + beta_id * ideology + beta_int * exp_val * ideology
        predicted_iat = (
            intercept + 
            beta_exposure * exp_val + 
            beta_ideology * ideology_vals + 
            beta_interaction * exp_val * ideology_vals
        )
        plt.plot(ideology_vals, predicted_iat, color=color, label=label, linewidth=2)

    plt.xlabel('Political Ideology (Z-scored)', fontsize=12)
    plt.ylabel('Predicted IAT D-Score', fontsize=12)
    plt.title('Interaction: News Exposure × Political Ideology on Implicit Bias', fontsize=14)
    plt.legend()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Interaction plot saved to {output_path}")
    return output_path

def generate_bootstrap_plot(
    robustness_data: pd.DataFrame,
    output_path: Path,
    figsize: Tuple[int, int] = (10, 6)
) -> Optional[Path]:
    """
    Generates a histogram of the bootstrap distribution for the interaction term.
    Expects robustness_data to have a column 'bootstrap_interaction_coef' or similar.
    """
    if robustness_data.empty:
        logger.warning("Robustness data is empty, cannot generate bootstrap plot.")
        return None

    # Try to find the interaction coefficient column
    interaction_col = None
    possible_cols = ['bootstrap_interaction_coef', 'interaction_coef', 'coef']
    for col in possible_cols:
        if col in robustness_data.columns:
            interaction_col = col
            break
    
    if interaction_col is None:
        logger.warning("Could not find interaction coefficient column in robustness data.")
        return None

    plt.figure(figsize=figsize)
    sns.set_style("whitegrid")
    
    # Plot histogram
    sns.histplot(robustness_data[interaction_col], kde=True, color='skyblue', bins=30)
    
    # Add vertical lines for mean and CI if available
    if 'bootstrap_mean' in robustness_data.columns:
        mean_val = robustness_data['bootstrap_mean'].iloc[0]
        plt.axvline(mean_val, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_val:.4f}')
    
    if 'bootstrap_ci_lower' in robustness_data.columns and 'bootstrap_ci_upper' in robustness_data.columns:
        lower = robustness_data['bootstrap_ci_lower'].iloc[0]
        upper = robustness_data['bootstrap_ci_upper'].iloc[0]
        plt.axvline(lower, color='green', linestyle='dotted', linewidth=2, label=f'95% CI: [{lower:.4f}, {upper:.4f}]')
        plt.axvline(upper, color='green', linestyle='dotted', linewidth=2)

    plt.xlabel('Bootstrap Interaction Coefficient', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Bootstrap Distribution of Interaction Term', fontsize=14)
    plt.legend()
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Bootstrap plot saved to {output_path}")
    return output_path

def render_report_html(
    results: Dict[str, Any],
    plots: Dict[str, Path],
    template_name: str = "report.j2",
    output_html_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Renders the Jinja2 report template with results and plot paths.
    """
    config = get_config()
    results_path = get_results_path()
    
    # Default template path relative to code/
    template_dir = Path(__file__).parent / "templates"
    if not template_dir.exists():
        logger.error(f"Template directory not found: {template_dir}")
        return None

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    try:
        template = env.get_template(template_name)
    except Exception as e:
        logger.error(f"Failed to load template {template_name}: {e}")
        return None

    # Prepare context
    context = {
        'model_summary': results.get('model_summary', pd.DataFrame()),
        'diagnostics': results.get('diagnostics', pd.DataFrame()),
        'robustness': results.get('robustness', pd.DataFrame()),
        'power_analysis': results.get('power_analysis', pd.DataFrame()),
        'binary_model': results.get('binary_model', pd.DataFrame()),
        'interaction_plot': str(plots.get('interaction_plot', '')),
        'bootstrap_plot': str(plots.get('bootstrap_plot', '')),
        'project_config': config
    }

    html_content = template.render(**context)

    if output_html_path is None:
        output_html_path = results_path / "report.html"
    
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Report HTML saved to {output_html_path}")
    return output_html_path

def save_report_html(html_path: Path, pdf_path: Optional[Path] = None) -> Optional[Path]:
    """
    Converts the HTML report to PDF.
    Note: This requires 'weasyprint' or 'wkhtmltopdf' to be installed.
    If not available, it simply returns the HTML path and logs a warning.
    """
    if pdf_path is None:
        results_path = get_results_path()
        pdf_path = results_path / "report.pdf"

    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
        logger.info(f"PDF report saved to {pdf_path}")
        return pdf_path
    except ImportError:
        logger.warning("weasyprint not installed. PDF generation skipped. Install with: pip install weasyprint")
        return None
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None

def run_reporting_pipeline() -> Dict[str, Any]:
    """
    Main pipeline for reporting:
    1. Load results from files
    2. Generate plots
    3. Render HTML report
    4. Generate PDF report
    """
    logger.info("Starting reporting pipeline...")
    results_path = get_results_path()
    
    # 1. Load results
    results = load_results_from_files()
    
    # 2. Generate plots
    plots = {}
    
    interaction_plot_path = results_path / "interaction_plot.png"
    generated = generate_interaction_plot(results.get('model_summary', pd.DataFrame()), interaction_plot_path)
    if generated:
        plots['interaction_plot'] = generated
    
    bootstrap_plot_path = results_path / "bootstrap_distribution.png"
    generated = generate_bootstrap_plot(results.get('robustness', pd.DataFrame()), bootstrap_plot_path)
    if generated:
        plots['bootstrap_plot'] = generated
    
    # 3. Render HTML report
    html_path = render_report_html(results, plots)
    
    # 4. Generate PDF report
    pdf_path = None
    if html_path:
        pdf_path = save_report_html(html_path)
    
    logger.info("Reporting pipeline completed.")
    return {
        'html_report': html_path,
        'pdf_report': pdf_path,
        'plots': plots
    }

if __name__ == "__main__":
    run_reporting_pipeline()
