import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
DOCS_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR = DOCS_DIR / "output"

def ensure_directories():
    """Ensure all required output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {OUTPUT_DIR}")

def load_analysis_results() -> Dict[str, Any]:
    """Load the main analysis results from JSON."""
    results_path = DERIVED_DIR / "analysis_results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Analysis results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_sensitivity_results() -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON."""
    results_path = DERIVED_DIR / "sensitivity_analysis.json"
    if not results_path.exists():
        logger.warning(f"Sensitivity analysis results not found at {results_path}. Skipping sensitivity plot.")
        return {}
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_stratified_results() -> Dict[str, Any]:
    """Load stratified (signal separation) analysis results from JSON."""
    results_path = DERIVED_DIR / "stratified_analysis_results.json"
    if not results_path.exists():
        logger.warning(f"Stratified analysis results not found at {results_path}. Skipping signal separation section.")
        return {}
    
    with open(results_path, 'r') as f:
        return json.load(f)

def generate_forest_plot(results: Dict[str, Any], output_path: Path):
    """Generate a forest plot of effect sizes with confidence intervals."""
    if not results:
        logger.warning("No results provided for forest plot generation.")
        return

    # Extract data for plotting
    proxies = []
    coefficients = []
    ci_lower = []
    ci_upper = []
    p_values = []
    significant = []

    for model_name, model_data in results.get("models", {}).items():
        for proxy, stats in model_data.get("coefficients", {}).items():
            if proxy == "intercept":
                continue
            
            coef = stats.get("coef", 0)
            std_err = stats.get("std_err", 0)
            p_val = stats.get("p_value", 1.0)
            adj_p_val = stats.get("adj_p_value", p_val)
            
            # Calculate 95% CI
            ci_l = coef - 1.96 * std_err
            ci_u = coef + 1.96 * std_err

            proxies.append(proxy)
            coefficients.append(coef)
            ci_lower.append(ci_l)
            ci_upper.append(ci_u)
            p_values.append(adj_p_val)
            significant.append(adj_p_val < 0.05)

    df = pd.DataFrame({
        'Proxy': proxies,
        'Coefficient': coefficients,
        'CI_Lower': ci_lower,
        'CI_Upper': ci_upper,
        'P_Value': p_values,
        'Significant': significant
    })

    # Sort by coefficient for better visualization
    df = df.sort_values('Coefficient')

    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")
    
    # Plot error bars
    plt.errorbar(
        df['Coefficient'], 
        range(len(df)), 
        xerr=[df['Coefficient'] - df['CI_Lower'], df['CI_Upper'] - df['Coefficient']], 
        fmt='o', 
        capsize=5, 
        linestyle='None',
        color='blue',
        alpha=0.7
    )

    # Plot significant points in red
    sig_indices = df[df['Significant']].index
    if len(sig_indices) > 0:
        plt.scatter(
            df.loc[sig_indices, 'Coefficient'], 
            sig_indices, 
            color='red', 
            zorder=3, 
            label='Significant (p < 0.05)'
        )
    
    # Non-significant
    non_sig_indices = df[~df['Significant']].index
    if len(non_sig_indices) > 0:
        plt.scatter(
            df.loc[non_sig_indices, 'Coefficient'], 
            non_sig_indices, 
            color='blue', 
            zorder=3, 
            label='Not Significant'
        )

    plt.axvline(x=0, color='black', linestyle='--', linewidth=1)
    plt.yticks(range(len(df)), df['Proxy'])
    plt.xlabel('Coefficient (Effect Size)')
    plt.title('Forest Plot: LLM Adoption Effect on Cognitive Load Proxies')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Forest plot saved to {output_path}")

def generate_sensitivity_plot(sensitivity_data: Dict[str, Any], output_path: Path):
    """Generate a plot showing effect variation across thresholds."""
    if not sensitivity_data:
        logger.warning("No sensitivity data provided for plotting.")
        return

    thresholds = sensitivity_data.get("thresholds", [])
    effects = sensitivity_data.get("effect_sizes", [])
    cis = sensitivity_data.get("confidence_intervals", [])

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    plt.errorbar(
        thresholds, 
        effects, 
        yerr=[[c[0] for c in cis], [c[1] for c in cis]], 
        fmt='o-', 
        capsize=5, 
        color='green', 
        alpha=0.8
    )
    
    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
    plt.xlabel('Iteration Count Threshold')
    plt.ylabel('Effect Size (Coefficient)')
    plt.title('Sensitivity Analysis: Effect Size vs. Iteration Threshold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Sensitivity plot saved to {output_path}")

def generate_stratified_plot(stratified_data: Dict[str, Any], output_path: Path):
    """Generate a plot comparing effect sizes between High and Low AI-Noise groups."""
    if not stratified_data:
        logger.warning("No stratified data provided for plotting.")
        return

    groups = list(stratified_data.keys())
    effects = []
    cis = []

    for group in groups:
        group_data = stratified_data[group]
        coef = group_data.get("llm_adoption_coef", 0)
        std_err = group_data.get("llm_adoption_se", 0)
        ci_l = coef - 1.96 * std_err
        ci_u = coef + 1.96 * std_err
        effects.append(coef)
        cis.append([ci_l, ci_u])

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    plt.errorbar(
        groups, 
        effects, 
        yerr=[[c[0] for c in cis], [c[1] for c in cis]], 
        fmt='o-', 
        capsize=5, 
        color='purple', 
        alpha=0.8
    )
    
    plt.axhline(y=0, color='black', linestyle='--', linewidth=1)
    plt.xlabel('AI-Noise Group')
    plt.ylabel('Effect Size (Coefficient)')
    plt.title('Signal Separation: LLM Adoption Effect by AI-Noise Level')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Stratified plot saved to {output_path}")

def generate_report_text(
    analysis_results: Dict[str, Any], 
    sensitivity_results: Dict[str, Any],
    stratified_results: Dict[str, Any]
) -> str:
    """Generate the text content of the report."""
    text_parts = []

    # Title
    text_parts.append("# Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load")
    text_parts.append("")
    text_parts.append("## Executive Summary")
    text_parts.append("")
    text_parts.append("This study investigates the association between LLM-based code completion adoption and various proxy metrics for developer cognitive load. "
                    "Using a mixed-methods approach on GitHub repositories, we analyze code review patterns, iteration counts, and reversion frequencies.")
    text_parts.append("")

    # Theoretical Grounding (Per T005/FR-009)
    text_parts.append("## Theoretical Grounding")
    text_parts.append("")
    text_parts.append("This study is grounded in the framework of distributed cognition (Holland et al.), which posits that cognitive processes are not confined to the individual "
                    "but are distributed across internal and external representations. The introduction of LLM-based tools represents a significant shift in this cognitive distribution, "
                    "potentially offloading internal problem-solving to external artifacts while introducing new coordination costs.")
    text_parts.append("")

    # Data Gap (Per T005/FR-009)
    text_parts.append("## Data Gap and Limitations")
    text_parts.append("")
    text_parts.append("Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.")
    text_parts.append("")
    text_parts.append("Due to the observational nature of this study using public GitHub data, we could not collect self-reported cognitive load data. "
                    "Consequently, we rely on behavioral proxies such as iteration count, review thread depth, and comment length as indicators of cognitive effort.")
    text_parts.append("")

    # Methodology Summary
    text_parts.append("## Methodology")
    text_parts.append("")
    text_parts.append("We employed Generalized Linear Mixed Models (GLMM) with random intercepts for repositories to account for clustering effects. "
                    "For zero-inflated outcomes (e.g., reverts), we utilized Zero-Inflated Negative Binomial (ZINB) models. "
                    "Multiple-comparison corrections (Bonferroni) were applied to control for false discovery rates.")
    text_parts.append("")

    # Results
    text_parts.append("## Results")
    text_parts.append("")
    
    if analysis_results and "models" in analysis_results:
        text_parts.append("### Primary Analysis: LLM Adoption Effects")
        text_parts.append("")
        text_parts.append("The following table summarizes the effect sizes (coefficients) of LLM adoption on various cognitive load proxies:")
        text_parts.append("")
        text_parts.append("| Proxy | Coefficient | Std. Error | P-Value | Adj. P-Value | Significant? |")
        text_parts.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        
        for model_name, model_data in analysis_results.get("models", {}).items():
            for proxy, stats in model_data.get("coefficients", {}).items():
                if proxy == "intercept":
                    continue
                coef = stats.get("coef", 0)
                std_err = stats.get("std_err", 0)
                p_val = stats.get("p_value", 1.0)
                adj_p_val = stats.get("adj_p_value", p_val)
                sig = "Yes" if adj_p_val < 0.05 else "No"
                text_parts.append(f"| {proxy} | {coef:.4f} | {std_err:.4f} | {p_val:.4f} | {adj_p_val:.4f} | {sig} |")
        
        text_parts.append("")
        text_parts.append("**Null Hypothesis Status:** Based on the Bonferroni-corrected p-values, we [reject/fail to reject] the null hypothesis that LLM adoption has no effect on cognitive load proxies.")
        text_parts.append("")
    else:
        text_parts.append("No analysis results available.")
        text_parts.append("")

    # Sensitivity Analysis
    if sensitivity_results:
        text_parts.append("### Sensitivity Analysis")
        text_parts.append("")
        text_parts.append("We performed a sensitivity analysis by sweeping the `iteration_count` threshold over a range of low integer values. "
                        "The effect estimates remained [stable/unstable] across thresholds, suggesting [robustness/sensitivity] of our findings.")
        text_parts.append("")
    
    # Signal Separation (New Section for T052)
    if stratified_results:
        text_parts.append("## Signal Separation: Distinguishing Tool Utility from AI Noise")
        text_parts.append("")
        text_parts.append("To address concerns regarding the conflation of 'fixing AI's mess' with 'solving the problem,' we conducted a stratified analysis based on the `diff_complexity_score`. "
                        "Repos were split into 'High AI-Noise' (high diff complexity, likely fixing AI errors) and 'Low AI-Noise' groups.")
        text_parts.append("")
        
        high_noise = stratified_results.get("High AI-Noise", {})
        low_noise = stratified_results.get("Low AI-Noise", {})
        
        high_coef = high_noise.get("llm_adoption_coef", 0)
        high_se = high_noise.get("llm_adoption_se", 0)
        low_coef = low_noise.get("llm_adoption_coef", 0)
        low_se = low_noise.get("llm_adoption_se", 0)
        
        text_parts.append(f"**High AI-Noise Group:** Coefficient = {high_coef:.4f} (SE = {high_se:.4f})")
        text_parts.append(f"**Low AI-Noise Group:** Coefficient = {low_coef:.4f} (SE = {low_se:.4f})")
        text_parts.append("")
        
        if abs(high_coef) > abs(low_coef):
            text_parts.append("The effect size is larger in the High AI-Noise group, suggesting that a significant portion of the observed 'cognitive load' may be attributable to the effort of correcting AI-generated errors rather than the inherent complexity of the task.")
        else:
            text_parts.append("The effect sizes are comparable between groups, suggesting that LLM adoption impacts cognitive load even when controlling for 'AI noise' (fixing errors).")
        
        text_parts.append("")
        text_parts.append("This stratification provides a methodological boundary, allowing us to distinguish between the tool's utility in problem-solving and the overhead introduced by AI-generated artifacts.")
        text_parts.append("")

    # Conclusion
    text_parts.append("## Conclusion")
    text_parts.append("")
    text_parts.append("This study provides initial evidence regarding the association between LLM-based code completion and developer cognitive load proxies. "
                    "While we observe [significant/non-significant] associations, the observational nature of the data and the reliance on proxy metrics limit causal inference. "
                    "Future work should aim to incorporate self-report measures and physiological proxies to triangulate these findings.")
    text_parts.append("")

    return "\n".join(text_parts)

def write_pdf_report(text: str, output_path: Path):
    """Write the report text to a PDF file."""
    # For this implementation, we will write a Markdown file as the primary artifact.
    # Generating a true PDF requires additional dependencies (e.g., reportlab, weasyprint)
    # which are not in the standard requirements. We will output the Markdown content
    # which can be converted to PDF by external tools.
    md_path = output_path.with_suffix('.md')
    with open(md_path, 'w') as f:
        f.write(text)
    
    logger.info(f"Report text saved to {md_path}")
    
    # Attempt to create a simple PDF if reportlab is available, otherwise just log
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Simple text processing for PDF (very basic)
        for line in text.split('\n'):
            if line.startswith('# '):
                story.append(Paragraph(line[2:], styles['Heading1']))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], styles['Heading2']))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading3']))
            elif line:
                story.append(Paragraph(line, styles['Normal']))
            story.append(Spacer(1, 12))
        
        doc.build(story)
        logger.info(f"PDF report generated at {output_path}")
    except ImportError:
        logger.warning("reportlab not installed. Skipping PDF generation. Markdown report available.")

def run_report_pipeline():
    """Execute the full report generation pipeline."""
    logger.info("Starting report generation pipeline...")
    
    ensure_directories()
    
    # Load data
    try:
        analysis_results = load_analysis_results()
        sensitivity_results = load_sensitivity_results()
        stratified_results = load_stratified_results()
    except FileNotFoundError as e:
        logger.error(f"Failed to load required data: {e}")
        return

    # Generate plots
    forest_plot_path = OUTPUT_DIR / "forest_plot.png"
    generate_forest_plot(analysis_results, forest_plot_path)

    sensitivity_plot_path = OUTPUT_DIR / "sensitivity_plot.png"
    generate_sensitivity_plot(sensitivity_results, sensitivity_plot_path)

    stratified_plot_path = OUTPUT_DIR / "stratified_plot.png"
    generate_stratified_plot(stratified_results, stratified_plot_path)

    # Generate text
    report_text = generate_report_text(analysis_results, sensitivity_results, stratified_results)

    # Write report
    pdf_path = OUTPUT_DIR / "final_report.pdf"
    write_pdf_report(report_text, pdf_path)

    logger.info("Report generation pipeline completed.")

def main():
    run_report_pipeline()

if __name__ == "__main__":
    main()