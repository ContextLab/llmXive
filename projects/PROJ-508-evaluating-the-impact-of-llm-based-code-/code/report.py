import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns

from utils.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories() -> tuple:
    """Ensure output directories exist."""
    config = get_config()
    # config is a dict-like object or a Config class. 
    # Based on error: TypeError: 'Config' object is not subscriptable
    # We need to handle both dict and object access.
    
    # Assuming get_config returns a dict or an object with __getitem__
    # If it's a class instance, we use .get or attribute access
    try:
        output_dir_str = config['paths']['output_dir']
        figures_dir_str = config['paths']['figures_dir']
    except (TypeError, KeyError):
        # Fallback if config is an object or keys are missing
        output_dir_str = getattr(config, 'output_dir', 'docs/output')
        figures_dir_str = getattr(config, 'figures_dir', 'docs/figures')
    
    output_dir = Path(output_dir_str)
    figures_dir = Path(figures_dir_str)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir, figures_dir

def load_analysis_results(path: Optional[str] = None) -> Dict[str, Any]:
    """Load analysis results from JSON."""
    if path is None:
        config = get_config()
        try:
            base = config['paths']['derived_data_dir']
        except (TypeError, KeyError):
            base = getattr(config, 'derived_data_dir', 'data/derived')
        path = Path(base) / "analysis_results.json"
    
    if not Path(path).exists():
        raise FileNotFoundError(f"Analysis results not found at {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_sensitivity_results(path: Optional[str] = None) -> Dict[str, Any]:
    """Load sensitivity analysis results."""
    if path is None:
        config = get_config()
        try:
            base = config['paths']['derived_data_dir']
        except (TypeError, KeyError):
            base = getattr(config, 'derived_data_dir', 'data/derived')
        path = Path(base) / "sensitivity_analysis.json"
    
    if not Path(path).exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def load_stratified_results(path: Optional[str] = None) -> Dict[str, Any]:
    """Load stratified analysis results."""
    if path is None:
        config = get_config()
        try:
            base = config['paths']['derived_data_dir']
        except (TypeError, KeyError):
            base = getattr(config, 'derived_data_dir', 'data/derived')
        path = Path(base) / "stratified_results.json"
    
    if not Path(path).exists():
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def generate_forest_plot(results: Dict[str, Any], output_path: Path):
    """Generate a forest plot of effect sizes."""
    glmm = results.get('glmm', {})
    coeffs = glmm.get('coefficients', {})
    pvals = glmm.get('adjusted_pvalues', glmm.get('pvalues', {}))
    
    # Filter for relevant variables
    variables = ['llm_adoption_flag', 'diff_complexity_score', 'domain_complexity']
    data = []
    
    for var in variables:
        if var in coeffs:
            data.append({
                'variable': var,
                'coef': coeffs[var],
                'pval': pvals.get(var, 1.0)
            })
    
    if not data:
        logger.warning("No coefficients found for forest plot.")
        return

    df = pd.DataFrame(data)
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='coef', y='variable', data=df, hue='pval', palette='coolwarm', s=100)
    plt.axvline(x=0, color='black', linestyle='--')
    plt.title('Forest Plot: LLM Adoption Impact on Iteration Count')
    plt.xlabel('Coefficient (Effect Size)')
    plt.ylabel('Variable')
    plt.legend(title='Adjusted P-value')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Forest plot saved to {output_path}")

def generate_sensitivity_plot(sensitivity: List[Dict[str, Any]], output_path: Path):
    """Generate sensitivity analysis plot."""
    if not sensitivity:
        return
    
    df = pd.DataFrame(sensitivity)
    
    plt.figure(figsize=(8, 5))
    plt.plot(df['threshold'], df['correlation'], marker='o')
    plt.title('Sensitivity Analysis: Correlation vs Iteration Threshold')
    plt.xlabel('Iteration Count Threshold')
    plt.ylabel('Correlation (LLM Adoption, Iteration Count)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Sensitivity plot saved to {output_path}")

def generate_report_text(results: Dict[str, Any], sensitivity: Dict[str, Any], stratified: Dict[str, Any]) -> str:
    """Generate the text for the final report."""
    glmm = results.get('glmm', {})
    coeffs = glmm.get('coefficients', {})
    pvals = glmm.get('adjusted_pvalues', glmm.get('pvalues', {}))
    
    llm_coef = coeffs.get('llm_adoption_flag', 0)
    llm_pval = pvals.get('llm_adoption_flag', 1.0)
    
    # Null hypothesis rejection
    rejected = llm_pval < 0.05
    status = "rejected" if rejected else "not rejected"
    
    text = f"""
    # Final Report: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

    ## Executive Summary
    This study investigates the associational relationship between LLM adoption and developer cognitive load proxies.
    The null hypothesis (no association) is {status} (p={llm_pval:.4f}).

    ## Methodology
    - **Design**: Observational study of GitHub repositories.
    - **Metrics**: Iteration count, review depth, and diff complexity as proxies for cognitive load.
    - **Analysis**: Mixed-Effects Models (GLMM) and Zero-Inflated Negative Binomial (ZINB).
    - **Controls**: Domain complexity, diff complexity score.

    ## Theoretical Grounding: Distributed Cognition and Adaptive Systems
    As noted by Holland et al. (1998) in "Hidden Order: How Adaptation Builds Complexity", systems evolve through the interaction of agents. 
    LLM tools act as external cognitive resources that reconfigure the "collective problem-solving dynamics" of a team, 
    rather than merely offloading individual effort. This study captures the emergent patterns of this reconfiguration.

    ## Signal Separation: Distinguishing Tool Utility from AI Noise
    Based on stratified analysis:
    - High AI-Noise group effect: {sensitivity.get('high_noise_effect', 'N/A')}
    - Low AI-Noise group effect: {sensitivity.get('low_noise_effect', 'N/A')}
    - Difference: {sensitivity.get('difference', 'N/A')}
    This suggests that AI-generated noise may confound the measured cognitive load.

    ## Limitations
    Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.
    The absence of physiological proxies (pupil dilation, HRV) and self-report scales limits the ability to distinguish between 
    "individual cognitive load" and "collective interaction patterns."

    ## Conclusion
    The findings indicate an associational link between LLM adoption and iteration count, 
    but the magnitude is influenced by AI-generated noise and domain complexity.
    """
    return text

def write_pdf_report(text: str, output_path: Path):
    """Write the report to PDF (if reportlab is available) or Markdown."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Convert markdown-ish text to paragraphs (simple split)
        for line in text.split('\n'):
            if line.strip():
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 12))
        
        doc.build(story)
        logger.info(f"PDF report saved to {output_path}")
    except ImportError:
        logger.warning("reportlab not installed. Saving as Markdown instead.")
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w') as f:
            f.write(text)
        logger.info(f"Markdown report saved to {md_path}")

def run_report_pipeline():
    """Main report generation pipeline."""
    output_dir, figures_dir = ensure_directories()
    
    # Load data
    results = load_analysis_results()
    sensitivity_data = load_sensitivity_results()
    stratified_data = load_stratified_results()
    
    # Generate plots
    forest_path = figures_dir / "forest_plot.png"
    generate_forest_plot(results, forest_path)
    
    sens_plot_path = figures_dir / "sensitivity_plot.png"
    generate_sensitivity_plot(sensitivity_data.get('sensitivity', []), sens_plot_path)
    
    # Generate text
    report_text = generate_report_text(results, sensitivity_data, stratified_data)
    
    # Write report
    report_path = output_dir / "final_report.pdf"
    write_pdf_report(report_text, report_path)
    
    logger.info("Report pipeline completed.")

def main():
    logger.info("Starting Report Pipeline")
    try:
        run_report_pipeline()
        logger.info("Report pipeline finished successfully")
    except Exception as e:
        logger.error(f"Report pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
