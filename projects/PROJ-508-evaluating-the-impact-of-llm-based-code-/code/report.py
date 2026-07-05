import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(output_dir: Path) -> None:
    """Ensure output directories exist."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'figures').mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist under {output_dir}")

def load_analysis_results(results_path: Path) -> Dict[str, Any]:
    """Load analysis results from JSON file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Analysis results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    logger.info(f"Loaded analysis results from {results_path}")
    return results

def load_sensitivity_results(sensitivity_path: Path) -> Dict[str, Any]:
    """Load sensitivity analysis results from JSON file."""
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity results not found at {sensitivity_path}")
    
    with open(sensitivity_path, 'r') as f:
        results = json.load(f)
    
    logger.info(f"Loaded sensitivity results from {sensitivity_path}")
    return results

def generate_forest_plot(results: Dict[str, Any], output_path: Path) -> None:
    """Generate a forest plot of effect sizes with confidence intervals."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract data for plotting
    proxies = []
    coefficients = []
    ci_lower = []
    ci_upper = []
    p_values = []
    significance = []

    for proxy, data in results.get('models', {}).items():
        coef = data.get('coefficient', 0)
        se = data.get('std_err', 0)
        p_val = data.get('pvalue', 1.0)
        ci_low = coef - 1.96 * se
        ci_high = coef + 1.96 * se

        proxies.append(proxy)
        coefficients.append(coef)
        ci_lower.append(ci_low)
        ci_upper.append(ci_high)
        p_values.append(p_val)
        significance.append('***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else '')

    y_pos = np.arange(len(proxies))
    ax.errorbar(
        coefficients, y_pos,
        xerr=[np.array(coefficients) - np.array(ci_lower), np.array(ci_upper) - np.array(coefficients)],
        fmt='o',
        capsize=5,
        color='#2c3e50',
        alpha=0.8,
        ecolor='#7f8c8d',
        linewidth=1.5
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([p.replace('_', ' ').title() for p in proxies])
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1)
    
    ax.set_xlabel('Effect Size (Coefficient)')
    ax.set_ylabel('Cognitive Load Proxy')
    ax.set_title('Forest Plot: LLM Adoption Effect on Cognitive Load Proxies')
    ax.set_xlim(min(ci_lower) - 0.1, max(ci_upper) + 0.1)

    # Add significance stars
    for i, sig in enumerate(significance):
        if sig:
            ax.text(coefficients[i] + 0.02, i, sig, va='center', fontsize=10, color='darkred')

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Forest plot saved to {output_path}")

def generate_sensitivity_plot(sensitivity_results: Dict[str, Any], output_path: Path) -> None:
    """Generate a plot showing effect variation across thresholds."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    thresholds = sensitivity_results.get('thresholds', [])
    effect_sizes = sensitivity_results.get('effect_sizes', [])
    ci_lowers = sensitivity_results.get('ci_lowers', [])
    ci_highers = sensitivity_results.get('ci_highers', [])

    ax.errorbar(
        thresholds, effect_sizes,
        yerr=[np.array(effect_sizes) - np.array(ci_lowers), np.array(ci_highers) - np.array(effect_sizes)],
        fmt='o-',
        capsize=5,
        color='#e74c3c',
        alpha=0.8,
        ecolor='#c0392b',
        linewidth=2,
        markersize=8
    )

    ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('Iteration Count Threshold')
    ax.set_ylabel('Effect Size (Coefficient)')
    ax.set_title('Sensitivity Analysis: Effect Size vs. Iteration Threshold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Sensitivity plot saved to {output_path}")

def generate_report_text(
    analysis_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    report_path: Path
) -> None:
    """
    Generate the text content of the final report.
    
    Includes:
    - Associational framing (not causal)
    - Observational study design reference
    - Null hypothesis rejection status
    - Theoretical Grounding section (Holland et al.)
    - Data Gap section (NASA-TLX unavailability)
    """
    models = analysis_results.get('models', {})
    bonferroni_results = analysis_results.get('bonferroni', {})
    
    # Build the report text
    lines = []
    lines.append("=" * 80)
    lines.append("EVALUATING THE IMPACT OF LLM-BASED CODE COMPLETION ON DEVELOPER COGNITIVE LOAD")
    lines.append("=" * 80)
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This study investigates the association between LLM-based code completion adoption")
    lines.append("and developer cognitive load, using proxy metrics derived from code repository")
    lines.append("activity. We employ a mixed-effects modeling approach to control for repository-level")
    lines.append("confounders and apply multiple-comparison corrections to our hypothesis tests.")
    lines.append("")
    
    # Methodology Note - Associational Framing
    lines.append("## Methodology and Study Design")
    lines.append("")
    lines.append("**Observational Study Design**: This research utilizes an observational design")
    lines.append("leveraging existing GitHub repository data. We explicitly frame our findings as")
    lines.append("**associational** rather than causal. The statistical models identify correlations")
    lines.append("between LLM adoption flags and cognitive load proxies, but do not establish")
    lines.append("causal mechanisms without randomized controlled trials.")
    lines.append("")
    
    # Theoretical Grounding
    lines.append("## Theoretical Grounding")
    lines.append("")
    lines.append("This study is grounded in the distributed cognition framework as articulated by")
    lines.append("Holland et al. (1995), which posits that cognitive processes are not confined")
    lines.append("to the individual mind but are distributed across people, artifacts, and")
    lines.append("environments. The introduction of LLM-based code completion tools represents")
    lines.append("a significant shift in the cognitive architecture of software development,")
    lines.append("potentially redistributing the cognitive load between human developers and")
    lines.append("artificial intelligence systems.")
    lines.append("")
    lines.append("By measuring changes in code review metrics (iteration counts, comment lengths,")
    lines.append("revert frequencies), we attempt to capture the emergent properties of this")
    lines.append("distributed cognitive system. However, we acknowledge the limitations of")
    lines.append("inferring internal cognitive states from external behavioral proxies.")
    lines.append("")
    
    # Data Gap Section
    lines.append("## Data Gap and Limitations")
    lines.append("")
    lines.append("A critical limitation of this study is the absence of direct self-report measures")
    lines.append("of cognitive load. Standard instruments such as the NASA Task Load Index")
    lines.append("(NASA-TLX) were not available for the population of GitHub developers studied.")
    lines.append("")
    lines.append("Note: This study uses proxy metrics for cognitive load. Self-report measures")
    lines.append("(e.g., NASA-TLX) were not available.")
    lines.append("")
    lines.append("Consequently, our findings should be interpreted as indicators of behavioral")
    lines.append("complexity rather than direct measures of mental effort or cognitive strain.")
    lines.append("")
    
    # Statistical Findings
    lines.append("## Statistical Findings")
    lines.append("")
    lines.append("We applied Mixed-Effects Models (GLMM) with random intercepts for repositories")
    lines.append("to account for hierarchical data structure. For zero-inflated outcomes (reverts,")
    lines.append("iterations), we utilized Zero-Inflated Negative Binomial (ZINB) or Hurdle models.")
    lines.append("")
    
    # Null Hypothesis Testing
    lines.append("### Hypothesis Testing Results")
    lines.append("")
    
    for proxy, data in models.items():
        coef = data.get('coefficient', 0)
        p_val = data.get('pvalue', 1.0)
        adj_p = bonferroni_results.get(proxy, {}).get('adjusted_pvalue', p_val)
        se = data.get('std_err', 0)
        ci_low = coef - 1.96 * se
        ci_high = coef + 1.96 * se
        
        # Determine rejection status
        alpha = 0.05
        if adj_p < alpha:
            status = "REJECTED"
            significance = "**"
        else:
            status = "FAILED TO REJECT"
            significance = ""
        
        lines.append(f"**{proxy.replace('_', ' ').title()}**: {significance}")
        lines.append(f"  - Coefficient: {coef:.4f} (SE: {se:.4f})")
        lines.append(f"  - 95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
        lines.append(f"  - Raw p-value: {p_val:.4f}")
        lines.append(f"  - Bonferroni-adjusted p-value: {adj_p:.4f}")
        lines.append(f"  - Null Hypothesis (H0: β = 0): {status}")
        lines.append("")
    
    # Sensitivity Analysis
    lines.append("## Sensitivity Analysis")
    lines.append("")
    lines.append("To assess the robustness of our findings, we performed a sensitivity analysis")
    lines.append("by varying the iteration count threshold across a range of low integer values.")
    lines.append("")
    
    thresholds = sensitivity_results.get('thresholds', [])
    effects = sensitivity_results.get('effect_sizes', [])
    
    if thresholds and effects:
        lines.append(f"**Threshold Sweep Results**:")
        lines.append(f"  - Thresholds tested: {thresholds}")
        lines.append(f"  - Effect sizes: {[f'{e:.4f}' for e in effects]}")
        lines.append("")
        
        # Check for stability
        effect_range = max(effects) - min(effects) if effects else 0
        if effect_range < 0.1:
            lines.append("The effect sizes remain stable across threshold variations, suggesting")
            lines.append("robustness of the primary findings.")
        else:
            lines.append("The effect sizes show moderate variation across thresholds, indicating")
            lines.append("that the choice of iteration threshold may influence the magnitude of")
            lines.append("the observed association.")
        lines.append("")
    
    # Conclusion
    lines.append("## Conclusion")
    lines.append("")
    lines.append("This observational study provides associational evidence regarding the impact of")
    lines.append("LLM-based code completion on developer cognitive load proxies. The findings")
    lines.append("should be interpreted within the context of the distributed cognition framework")
    lines.append("and the limitations imposed by the use of proxy metrics.")
    lines.append("")
    lines.append("Future research should aim to incorporate direct self-report measures (e.g.,")
    lines.append("NASA-TLX) and physiological proxies to triangulate cognitive load assessments.")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    # Write to file
    report_text = "\n".join(lines)
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Report text generated and saved to {report_path}")

def run_report_pipeline(
    results_path: Path,
    sensitivity_path: Path,
    output_dir: Path
) -> None:
    """Execute the full report generation pipeline."""
    ensure_directories(output_dir)
    
    # Load data
    analysis_results = load_analysis_results(results_path)
    sensitivity_results = load_sensitivity_results(sensitivity_path)
    
    # Generate visualizations
    forest_plot_path = output_dir / 'figures' / 'forest_plot.png'
    generate_forest_plot(analysis_results, forest_plot_path)
    
    sensitivity_plot_path = output_dir / 'figures' / 'sensitivity_analysis.png'
    generate_sensitivity_plot(sensitivity_results, sensitivity_plot_path)
    
    # Generate report text
    report_text_path = output_dir / 'final_report.md'
    generate_report_text(analysis_results, sensitivity_results, report_text_path)
    
    logger.info("Report generation pipeline completed successfully.")

def main():
    """Main entry point for report generation."""
    # Default paths
    project_root = Path(__file__).parent.parent
    results_path = project_root / 'data' / 'derived' / 'analysis_results.json'
    sensitivity_path = project_root / 'data' / 'derived' / 'sensitivity_analysis.json'
    output_dir = project_root / 'docs' / 'output'
    
    # Run pipeline
    run_report_pipeline(results_path, sensitivity_path, output_dir)

if __name__ == "__main__":
    main()