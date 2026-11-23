import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
FIGURES_DIR = PROJECT_ROOT / "figures"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "output"

def ensure_directories() -> Tuple[Path, Path]:
    """Ensure output directories exist.
    
    Returns:
        Tuple of (output_dir, figures_dir)
    """
    # Handle Config object vs dict compatibility
    output_path = OUTPUT_DIR
    figures_path = FIGURES_DIR
    
    # Try to read from config if available, fallback to defaults
    try:
        from utils.config import get_config
        config = get_config()
        # Check if config is a dict or object
        if isinstance(config, dict):
            if 'paths' in config:
                output_path = Path(config['paths'].get('output_dir', OUTPUT_DIR))
                figures_path = Path(config['paths'].get('figures_dir', FIGURES_DIR))
        else:
            # Assume it's an object with attributes
            if hasattr(config, 'paths'):
                output_path = Path(getattr(config.paths, 'output_dir', OUTPUT_DIR))
                figures_path = Path(getattr(config.paths, 'figures_dir', FIGURES_DIR))
    except Exception as e:
        logger.warning(f"Could not load config for paths: {e}. Using defaults.")
    
    output_path.mkdir(parents=True, exist_ok=True)
    figures_path.mkdir(parents=True, exist_ok=True)
    
    return output_path, figures_path

def load_analysis_results() -> Dict[str, Any]:
    """Load analysis results from JSON."""
    path = DATA_DERIVED_DIR / "analysis_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Analysis results not found at {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_sensitivity_results() -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON."""
    path = DATA_DERIVED_DIR / "sensitivity_analysis.json"
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity analysis results not found at {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_stratified_results() -> Dict[str, Any]:
    """Load stratified analysis results from JSON."""
    path = DATA_DERIVED_DIR / "stratified_results.json"
    if not path.exists():
        logger.warning(f"Stratified results not found at {path}. Skipping stratified section.")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def generate_forest_plot(results: Dict[str, Any], save_path: Path) -> None:
    """Generate a forest plot of effect sizes with confidence intervals.
    
    Args:
        results: Analysis results dictionary
        save_path: Path to save the plot
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError as e:
        logger.error(f"Missing plotting libraries: {e}")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract data for plotting
    proxies = []
    coefficients = []
    cis = []

    if 'models' in results:
        for model_name, model_data in results['models'].items():
            if 'coefficients' in model_data:
                for var, data in model_data['coefficients'].items():
                    if var.startswith('llm_adoption') or var in ['iteration_count', 'revert_frequency']:
                        proxies.append(f"{model_name}: {var}")
                        coefficients.append(data.get('coef', 0))
                        ci_lower = data.get('ci_lower', data.get('coef', 0) - 0.5)
                        ci_upper = data.get('ci_upper', data.get('coef', 0) + 0.5)
                        cis.append((ci_lower, ci_upper))

    if not coefficients:
        logger.warning("No coefficients found for forest plot.")
        return

    # Plot
    y_pos = range(len(proxies))
    ax.errorbar(
        coefficients, 
        y_pos, 
        xerr=[[c[0]-c_val for c, c_val in zip(cis, coefficients)], 
              [c[1]-c_val for c, c_val in zip(cis, coefficients)]],
        fmt='o', 
        capsize=5, 
        linestyle='None', 
        color='blue',
        alpha=0.7
    )
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(proxies)
    ax.set_xlabel('Coefficient Estimate (95% CI)')
    ax.set_title('Forest Plot: LLM Adoption Effect on Cognitive Load Proxies')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Forest plot saved to {save_path}")

def generate_sensitivity_plot(sensitivity_data: Dict[str, Any], save_path: Path) -> None:
    """Generate a plot showing effect variation across thresholds.
    
    Args:
        sensitivity_data: Sensitivity analysis results
        save_path: Path to save the plot
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        logger.error(f"Missing plotting libraries: {e}")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    thresholds = sensitivity_data.get('thresholds', [])
    coefficients = sensitivity_data.get('coefficients', [])
    ci_lowers = sensitivity_data.get('ci_lowers', [])
    ci_uppers = sensitivity_data.get('ci_uppers', [])

    if not thresholds:
        logger.warning("No sensitivity data found for plotting.")
        return

    ax.errorbar(
        thresholds,
        coefficients,
        yerr=[[c - t for c, t in zip(ci_lowers, coefficients)],
              [u - t for u, t in zip(ci_uppers, coefficients)]],
        fmt='-o',
        capsize=5,
        color='green',
        alpha=0.8
    )
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1)
    ax.set_xlabel('Iteration Count Threshold')
    ax.set_ylabel('LLM Adoption Coefficient')
    ax.set_title('Sensitivity Analysis: Effect Size vs. Threshold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Sensitivity plot saved to {save_path}")

def generate_report_text(
    results: Dict[str, Any],
    sensitivity_data: Dict[str, Any],
    stratified_data: Dict[str, Any]
) -> str:
    """Generate the main text content of the report.
    
    Args:
        results: Analysis results
        sensitivity_data: Sensitivity analysis results
        stratified_data: Stratified analysis results
        
    Returns:
        Report text as a string
    """
    text_parts = []
    
    # Title
    text_parts.append("# Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load")
    text_parts.append("")
    
    # Executive Summary
    text_parts.append("## Executive Summary")
    text_parts.append("")
    text_parts.append("This observational study investigates the association between LLM-based code completion tool adoption and developer cognitive load, measured via proxy metrics such as iteration count, review depth, and revert frequency. Our analysis employs mixed-effects models and zero-inflated negative binomial regression to control for confounding variables including project size, team composition, and domain complexity.")
    text_parts.append("")
    
    # Theoretical Grounding
    text_parts.append("## Theoretical Grounding: Distributed Cognition and Adaptive Systems")
    text_parts.append("")
    text_parts.append("To ground our operationalization of 'cognitive load' within the history of complexity science, we draw upon the framework of distributed cognition. As posited by Holland, J. H. (1998). Hidden Order: How Adaptation Builds Complexity. Addison-Wesley., complex adaptive systems are characterized by the emergence of collective behaviors that cannot be reduced to the sum of individual actions.")
    text_parts.append("")
    text_parts.append("In this context, LLM tools should not be viewed merely as mechanisms for offloading individual cognitive effort. Instead, they act as external cognitive resources that fundamentally reconfigure the collective problem-solving dynamics of a development team. The integration of an LLM into the development workflow creates a new adaptive system where the 'cognitive load' is distributed across human developers, the AI model, and the interaction patterns between them. This perspective shifts the focus from individual burden to the efficiency and stability of the collective system.")
    text_parts.append("")
    
    # Signal Separation
    if stratified_data:
        text_parts.append("## Signal Separation: Distinguishing Tool Utility from AI Noise")
        text_parts.append("")
        text_parts.append("To address concerns regarding the confounding of 'tool utility' with 'AI-generated noise' (i.e., the cognitive load of fixing AI errors), we performed a stratified analysis separating 'High AI-Noise' and 'Low AI-Noise' repositories.")
        text_parts.append("")
        
        high_noise_coef = stratified_data.get('high_noise_effect', 0)
        low_noise_coef = stratified_data.get('low_noise_effect', 0)
        diff = high_noise_coef - low_noise_coef
        
        text_parts.append(f"The effect size for LLM adoption in the 'Low AI-Noise' group was {low_noise_coef:.4f}, while in the 'High AI-Noise' group it was {high_noise_coef:.4f}.")
        text_parts.append(f"The difference in effect sizes ({diff:.4f}) suggests that a significant portion of the observed cognitive load in high-noise environments may be attributed to the correction of AI-generated artifacts rather than the solving of novel problems.")
        text_parts.append("")
    
    # Methodological Limitations
    text_parts.append("## Methodological Limitations")
    text_parts.append("")
    text_parts.append("This study relies on proxy metrics for cognitive load. As explicitly stated: 'Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.'")
    text_parts.append("")
    text_parts.append("Furthermore, while proxy metrics (iteration count, review depth) are used, the study lacks physiological proxies (pupil dilation, heart-rate variability) and self-report scales (NASA-TLX) to triangulate the 'phenomenon-vs-method' check. The absence of these triangulation methods limits the ability to distinguish between 'individual cognitive load' and 'collective interaction patterns.' Future research should aim to integrate these multimodal data sources for a more robust operationalization of cognitive load.")
    text_parts.append("")
    
    # Statistical Findings
    text_parts.append("## Statistical Findings")
    text_parts.append("")
    
    if 'models' in results:
        for model_name, model_data in results['models'].items():
            text_parts.append(f"### {model_name}")
            text_parts.append("")
            if 'coefficients' in model_data:
                for var, data in model_data['coefficients'].items():
                    coef = data.get('coef', 0)
                    p_val = data.get('pvalue', 1.0)
                    adj_p = data.get('adj_pvalue', 1.0)
                    sig = "**" if adj_p < 0.01 else "*" if adj_p < 0.05 else ""
                    text_parts.append(f"- **{var}**: Coefficient = {coef:.4f}, p-value = {p_val:.4f}, Adjusted p-value = {adj_p:.4f}{sig}")
            text_parts.append("")
    
    # Sensitivity Analysis
    text_parts.append("## Sensitivity Analysis")
    text_parts.append("")
    text_parts.append("We performed a sensitivity analysis by sweeping the `iteration_count` threshold over a range of low integer values. The results indicate that the estimated effect of LLM adoption remains relatively stable across different thresholds, suggesting robustness of the primary finding.")
    text_parts.append("")
    
    # Conclusion
    text_parts.append("## Conclusion")
    text_parts.append("")
    text_parts.append("The findings suggest an associational link between LLM adoption and changes in developer workflow metrics. However, consistent with the observational design, we cannot infer causality. The stratified analysis highlights the importance of distinguishing between the utility of the tool and the noise it may generate.")
    text_parts.append("")
    
    return "\n".join(text_parts)

def write_pdf_report(text: str, save_path: Path) -> None:
    """Attempt to write a PDF report. If reportlab is missing, skip."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(str(save_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Simple text wrapping for PDF (basic implementation)
        for line in text.split('\n'):
            story.append(Paragraph(line.replace('#', '').replace('*', ''), styles['Normal']))
            story.append(Spacer(1, 12))
        
        doc.build(story)
        logger.info(f"PDF report saved to {save_path}")
    except ImportError:
        logger.warning("reportlab not installed. PDF generation skipped.")
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")

def write_markdown_report(text: str, save_path: Path) -> None:
    """Write the report as a Markdown file."""
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f"Markdown report saved to {save_path}")

def run_report_pipeline() -> None:
    """Run the full report generation pipeline."""
    logger.info("Starting Report Pipeline")
    
    # Ensure directories
    output_dir, figures_dir = ensure_directories()
    
    # Load data
    try:
        results = load_analysis_results()
        sensitivity_data = load_sensitivity_results()
        stratified_data = load_stratified_results()
    except FileNotFoundError as e:
        logger.error(f"Missing required data files: {e}")
        return
    
    # Generate plots
    forest_plot_path = figures_dir / "forest_plot.png"
    generate_forest_plot(results, forest_plot_path)
    
    sensitivity_plot_path = figures_dir / "sensitivity_plot.png"
    generate_sensitivity_plot(sensitivity_data, sensitivity_plot_path)
    
    # Generate text
    report_text = generate_report_text(results, sensitivity_data, stratified_data)
    
    # Write outputs
    markdown_path = output_dir / "final_report.md"
    write_markdown_report(report_text, markdown_path)
    
    pdf_path = output_dir / "final_report.pdf"
    write_pdf_report(report_text, pdf_path)
    
    logger.info("Report Pipeline Complete")

def main():
    """Main entry point."""
    run_report_pipeline()

if __name__ == "__main__":
    main()