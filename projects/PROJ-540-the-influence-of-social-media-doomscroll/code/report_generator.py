import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"REPORT: {message}")

def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load a JSON report file."""
    _log_step(f"Loading report from {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def interpret_correlation(correlation: float) -> str:
    """Interpret correlation strength."""
    if abs(correlation) < 0.1:
        return "Negligible"
    elif abs(correlation) < 0.3:
        return "Weak"
    elif abs(correlation) < 0.5:
        return "Moderate"
    else:
        return "Strong"

def format_correlation_table(correlations: Dict[str, Any]) -> str:
    """Format correlation results into a markdown table."""
    _log_step("Formatting correlation table")
    table = "| Variable | Correlation | P-value | Interpretation |\n"
    table += "|---|---|---|---|\n"
    
    for var, data in correlations.items():
        corr = data.get("correlation", 0)
        p_val = data.get("p_value", 1)
        interp = interpret_correlation(corr)
        table += f"| {var} | {corr:.3f} | {p_val:.3f} | {interp} |\n"
    
    return table

def format_assumption_checks(assumptions: Dict[str, Any]) -> str:
    """Format assumption checks into a markdown section."""
    _log_step("Formatting assumption checks")
    text = "### Assumption Checks\n\n"
    
    for check_name, result in assumptions.items():
        passed = result.get("pass", False)
        status = "✓ Pass" if passed else "✗ Fail"
        text += f"- **{check_name}**: {status}\n"
        for metric, value in result.items():
            if metric != "pass":
                text += f"  - {metric}: {value:.3f}\n"
    
    return text

def format_robustness_results(robustness: Dict[str, Any]) -> str:
    """Format robustness check results."""
    _log_step("Formatting robustness results")
    text = "### Robustness Check\n\n"
    
    status = robustness.get("status", "unknown")
    text += f"- **Status**: {status}\n"
    text += f"- **Plan Override**: {robustness.get('plan_override', False)}\n"
    
    if robustness.get("full_sample"):
        text += "\n#### Full Sample\n"
        text += f"- R²: {robustness['full_sample'].get('r_squared', 0):.3f}\n"
        text += f"- F-statistic: {robustness['full_sample'].get('f_statistic', 0):.3f}\n"
    
    if robustness.get("high_engagement_subset"):
        text += "\n#### High Engagement Subset\n"
        text += f"- R²: {robustness['high_engagement_subset'].get('r_squared', 0):.3f}\n"
        text += f"- F-statistic: {robustness['high_engagement_subset'].get('f_statistic', 0):.3f}\n"
    
    return text

def interpret_regression(regression: Dict[str, Any]) -> str:
    """Interpret regression results."""
    _log_step("Interpreting regression results")
    text = "### Regression Results\n\n"
    text += f"- **R²**: {regression.get('r_squared', 0):.3f}\n"
    text += f"- **Adjusted R²**: {regression.get('adj_r_squared', 0):.3f}\n"
    text += f"- **F-statistic**: {regression.get('f_statistic', 0):.3f} (p={regression.get('f_pvalue', 1):.3f})\n\n"
    
    text += "#### Coefficients\n"
    for var, coef in regression.get("coefficients", {}).items():
        p_val = regression.get("p_values", {}).get(var, 1)
        sig = "*" if p_val < 0.05 else ""
        text += f"- {var}: {coef:.3f} {sig} (p={p_val:.3f})\n"
    
    return text

def conclude_findings(correlations: Dict[str, Any], regression: Dict[str, Any], 
                     robustness: Dict[str, Any]) -> str:
    """Conclude findings based on results."""
    _log_step("Concluding findings")
    text = "### Conclusion\n\n"
    
    # Simplified conclusion logic
    if correlations:
        first_corr = list(correlations.values())[0]
        corr_val = first_corr.get("correlation", 0)
        text += f"The analysis found a {interpret_correlation(corr_val)} correlation (r={corr_val:.3f}) between news exposure and anxiety.\n\n"
    
    text += "This study highlights the associational nature of the findings and the importance of considering confounding variables like baseline anxiety.\n"
    return text

def generate_final_report(correlations: Dict[str, Any], regression: Dict[str, Any],
                         robustness: Dict[str, Any], assumptions: Dict[str, Any],
                         output_path: Path) -> None:
    """Generate the final markdown report."""
    _log_step("Generating final report")
    
    report = "# Final Report: The Influence of Social Media Doomscrolling on Anticipatory Anxiety\n\n"
    report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    report += "## Executive Summary\n\n"
    report += "This report presents the findings of an analysis examining the relationship between social media news exposure and anxiety levels.\n\n"
    
    report += "## Methods\n\n"
    report += "Data was cleaned using listwise deletion. A multiple linear regression model was fitted with anxiety_score as the outcome and news_exposure_freq, baseline_anxiety, age, and gender as predictors.\n\n"
    
    report += "## Results\n\n"
    report += format_correlation_table(correlations)
    report += "\n"
    report += interpret_regression(regression)
    report += "\n"
    report += format_assumption_checks(assumptions)
    report += "\n"
    report += format_robustness_results(robustness)
    report += "\n"
    
    report += "## Limitations\n\n"
    report += "- Observational study design limits causal inference.\n"
    report += "- Potential for unmeasured confounding variables.\n"
    report += "- Sample size constraints (refer to power analysis).\n\n"
    
    report += conclude_findings(correlations, regression, robustness)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    
    _log_step(f"Final report saved to {output_path}")

def main() -> None:
    """Main entry point for report generator script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    # Load results (simplified for this task)
    corr_path = Path("outputs/correlation_results.json")
    reg_path = Path("outputs/regression_results.json")
    robust_path = Path("outputs/robustness_results.json")
    
    try:
        correlations = load_json_report(corr_path) if corr_path.exists() else {}
        regression = load_json_report(reg_path) if reg_path.exists() else {}
        robustness = load_json_report(robust_path) if robust_path.exists() else {}
        assumptions = regression.get("assumptions", {})
        
        output_path = Path("outputs/final_report.md")
        generate_final_report(correlations, regression, robustness, assumptions, output_path)
        logger.info("Report generation completed")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
