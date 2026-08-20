import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load a JSON report from file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def interpret_correlation(corr_val: float, p_val: float) -> str:
    """Interpret correlation coefficient and p-value."""
    magnitude = "weak"
    if abs(corr_val) > 0.5:
        magnitude = "strong"
    elif abs(corr_val) > 0.3:
        magnitude = "moderate"
    
    significance = "not significant"
    if p_val < 0.05:
        significance = "statistically significant"
    
    direction = "positive" if corr_val > 0 else "negative"
    
    return f"A {magnitude} {direction} correlation ({corr_val:.3f}, p={p_val:.3f}) which is {significance}."

def format_correlation_table(correlations: Dict[str, Any]) -> str:
    """Format correlation results into a markdown table."""
    lines = ["### Correlation Results\n"]
    lines.append("| Variable Pair | Correlation (r) | P-value | Interpretation |")
    lines.append("|---|---|---|---|")
    
    for pair, data in correlations.items():
        r = data.get('correlation', 0)
        p = data.get('p_value', 1)
        interp = interpret_correlation(r, p)
        lines.append(f"| {pair} | {r:.4f} | {p:.4f} | {interp} |")
    
    return "\n".join(lines)

def format_assumption_checks(assumptions: Dict[str, Any]) -> str:
    """Format assumption check results."""
    lines = ["### Model Assumption Checks\n"]
    
    # Linearity
    if 'linearity_check' in assumptions:
        l = assumptions['linearity_check']
        status = "Passed" if l.get('passed') else "Failed"
        lines.append(f"- **Linearity**: {status} (r={l.get('correlation', 0):.4f}, p={l.get('p_value', 0):.4f})")
    
    # Homoscedasticity
    if 'homoscedasticity' in assumptions:
        h = assumptions['homoscedasticity']
        status = "Passed" if h.get('passed') else "Failed"
        lines.append(f"- **Homoscedasticity**: {status} (p={h.get('p_value', 0):.4f})")
    
    # Normality
    if 'normality' in assumptions:
        n = assumptions['normality']
        status = "Passed" if n.get('passed') else "Failed"
        lines.append(f"- **Normality of Residuals**: {status} (p={n.get('p_value', 0):.4f})")
    
    # VIF
    if 'vif' in assumptions:
        vifs = assumptions['vif']
        vif_str = ", ".join([f"{k}: {v:.2f}" for k, v in vifs.items() if not (isinstance(v, float) and np.isnan(v))])
        lines.append(f"- **Multicollinearity (VIF)**: {vif_str}")
    
    return "\n".join(lines)

def format_robustness_results(robustness: Dict[str, Any]) -> str:
    """Format robustness check results."""
    lines = ["### Robustness Check\n"]
    
    if not robustness.get('check_performed'):
        lines.append("Robustness check was not performed (correlation <= 0.3 or data missing).")
        return "\n".join(lines)
    
    lines.append(f"Engagement Correlation: {robustness.get('engagement_correlation', 0):.4f}")
    
    comp = robustness.get('comparison', {})
    if comp:
        lines.append(f"- Full Sample Coefficient: {comp.get('full_coef', 0):.4f}")
        lines.append(f"- High-Engagement Subset Coefficient: {comp.get('subset_coef', 0):.4f}")
        lines.append(f"- Sign Match: {'Yes' if comp.get('sign_match') else 'No'}")
    
    return "\n".join(lines)

def interpret_regression(regression: Dict[str, Any]) -> str:
    """Interpret regression results."""
    r_sq = regression.get('rsquared', 0)
    p_val = regression.get('f_pvalue', 1)
    
    interp = f"The model explains {r_sq:.2%} of the variance in anxiety scores. Overall model significance: {'significant' if p_val < 0.05 else 'not significant'} (p={p_val:.4f})."
    return interp

def conclude_findings(correlations: Dict[str, Any], regression: Dict[str, Any]) -> str:
    """Generate a concluding summary."""
    lines = ["## Conclusion\n"]
    lines.append("This analysis explored the associational relationship between social media news exposure and anticipatory anxiety.")
    lines.append("Results should be interpreted with caution as this is an observational study.")
    
    if 'news_exposure_anxiety' in correlations:
        c = correlations['news_exposure_anxiety']
        lines.append(f"The primary analysis found a {interpret_correlation(c['correlation'], c['p_value'])} relationship.")
    
    return "\n".join(lines)

def generate_final_report(correlations: Dict[str, Any], regression: Dict[str, Any], 
                          assumptions: Dict[str, Any], robustness: Dict[str, Any], 
                          output_path: Path) -> None:
    """Generate the final markdown report."""
    logger.info(f"Generating final report at {output_path}")
    ensure_directories(output_path)
    
    report = []
    report.append("# The Influence of Social Media Doomscrolling on Anticipatory Anxiety")
    report.append(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
    
    report.append("## Executive Summary")
    report.append(interpret_regression(regression))
    report.append("")
    
    report.append("## Statistical Results")
    report.append(format_correlation_table(correlations))
    report.append("")
    
    report.append(format_assumption_checks(assumptions))
    report.append("")
    
    report.append(format_robustness_results(robustness))
    report.append("")
    
    report.append(conclude_findings(correlations, regression))
    
    with open(output_path, 'w') as f:
        f.write("\n".join(report))
    
    logger.info("Final report generated successfully.")

def main() -> None:
    """Main entry point for report generation."""
    config = load_config()
    corr_path = Path(config['paths']['correlation_results'])
    reg_path = Path(config['paths']['regression_results'])
    robust_path = Path(config['paths']['robustness_results'])
    output_path = Path(config['paths']['final_report'])
    
    try:
        correlations = load_json_report(corr_path)
        regression = load_json_report(reg_path)
        robustness = load_json_report(robust_path)
        
        # Assumptions are usually inside regression_results or separate. 
        # Assuming they were saved in regression_results for this task's context or we load from a separate file if T019 saved them.
        # For T032 cleanup, we assume the structure is stable.
        # If assumptions are not in reg_path, we might need to handle missing keys gracefully.
        assumptions = regression.get('assumptions', {})
        
        generate_final_report(correlations, regression, assumptions, robustness, output_path)
    except FileNotFoundError as e:
        logger.error(f"Missing report input file: {e}")
    except Exception as e:
        logger.critical(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
