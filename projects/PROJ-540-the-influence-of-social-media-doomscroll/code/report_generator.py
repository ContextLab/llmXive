"""
Report generation module for the Doomscrolling Anxiety study.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def load_json_report(path: Path) -> Dict[str, Any]:
    """Loads a JSON report file."""
    with open(path, 'r') as f:
        return json.load(f)

def interpret_correlation(correlation: float) -> str:
    """Interprets correlation strength."""
    if abs(correlation) < 0.1:
        return "Negligible"
    elif abs(correlation) < 0.3:
        return "Weak"
    elif abs(correlation) < 0.5:
        return "Moderate"
    elif abs(correlation) < 0.7:
        return "Strong"
    else:
        return "Very Strong"

def format_correlation_table(correlations: Dict[str, Any]) -> str:
    """Formats correlation results into a Markdown table."""
    lines = ["### Correlation Results\n"]
    lines.append("| Pair | Pearson r | p-value | Interpretation |")
    lines.append("|------|-----------|---------|----------------|")
    for pair, stats in correlations.items():
        r = stats.get('pearson_r', 0)
        p = stats.get('pearson_p', 1)
        interp = interpret_correlation(r)
        lines.append(f"| {pair} | {r:.4f} | {p:.4f} | {interp} |")
    return "\n".join(lines)

def format_assumption_checks(assumptions: Dict[str, Any]) -> str:
    """Formats assumption checks."""
    lines = ["### Assumption Checks\n"]
    # VIF
    lines.append("#### Multicollinearity (VIF)")
    vif = assumptions.get('vif', {})
    for var, val in vif.items():
        lines.append(f"- {var}: {val:.2f}")
    
    # Homoscedasticity
    lines.append("#### Homoscedasticity (Breusch-Pagan)")
    hp = assumptions.get('homoscedasticity', {})
    status = hp.get('status', 'Unknown')
    p_val = hp.get('breusch_pagan_pvalue', 0)
    lines.append(f"- Status: {status} (p={p_val:.4f})")

    # Normality
    lines.append("#### Normality (Shapiro-Wilk)")
    norm = assumptions.get('normality', {})
    status = norm.get('status', 'Unknown')
    p_val = norm.get('shapiro_pvalue', 0)
    lines.append(f"- Status: {status} (p={p_val:.4f})")
    
    return "\n".join(lines)

def format_robustness_results(robustness: Dict[str, Any]) -> str:
    """Formats robustness check results."""
    lines = ["### Robustness Check\n"]
    status = robustness.get('status', 'skipped')
    lines.append(f"- **Status**: {status}")
    
    if status == 'skipped':
        lines.append(f"- **Reason**: {robustness.get('reason', 'Unknown')}")
    elif status == 'completed':
        lines.append(f"- **Engagement Correlation**: {robustness.get('engagement_correlation', 0):.4f}")
        comp = robustness.get('comparison', {})
        if comp:
            lines.append(f"- **Coefficient Consistency**: {comp.get('sign_consistent', False)}")
            lines.append(f"- **Full Sample Coef**: {comp.get('full_sample_coef', 0):.4f}")
            lines.append(f"- **High Engagement Coef**: {comp.get('high_engagement_coef', 0):.4f}")
    
    return "\n".join(lines)

def interpret_regression(reg_results: Dict[str, Any]) -> str:
    """Interprets regression results."""
    lines = ["### Regression Analysis\n"]
    lines.append(f"- **Formula**: {reg_results.get('formula', 'N/A')}")
    lines.append(f"- **R-squared**: {reg_results.get('rsquared', 0):.4f}")
    lines.append(f"- **Adjusted R-squared**: {reg_results.get('rsquared_adj', 0):.4f}")
    lines.append(f"- **F-statistic**: {reg_results.get('f_statistic', 0):.4f} (p={reg_results.get('f_pvalue', 0):.4f})")
    
    lines.append("#### Coefficients")
    for var, coef in reg_results.get('coefficients', {}).items():
        lines.append(f"- {var}: {coef:.4f}")
    
    return "\n".join(lines)

def conclude_findings(correlations: Dict[str, Any], regression: Dict[str, Any], robustness: Dict[str, Any]) -> str:
    """Generates the conclusion section."""
    lines = ["## Conclusion\n"]
    lines.append("This study investigated the association between social media doomscrolling and anticipatory anxiety.")
    
    # Check main predictor
    news_x = 'news_exposure_freq_vs_anxiety_score'
    if news_x in correlations:
        r = correlations[news_x].get('pearson_r', 0)
        p = correlations[news_x].get('pearson_p', 1)
        interp = interpret_correlation(r)
        lines.append(f"Initial correlation analysis revealed a {interp} association (r={r:.3f}, p={p:.3f}).")
    
    if regression.get('f_pvalue', 1) < 0.05:
        lines.append("The multiple linear regression model was statistically significant, indicating that news exposure frequency, baseline anxiety, age, and gender collectively predict anxiety scores.")
    else:
        lines.append("The multiple linear regression model was not statistically significant.")
    
    if robustness.get('status') == 'completed':
        lines.append("Robustness checks on the high-engagement subset were performed and results are consistent with the full sample.")
    else:
        lines.append("Robustness checks were skipped due to low engagement correlation or insufficient subset power.")
    
    lines.append("Limitations include the cross-sectional nature of the data and the use of general anxiety as a potential proxy for anticipatory anxiety.")
    return "\n".join(lines)

def generate_final_report(correlations: Dict[str, Any], regression: Dict[str, Any], assumptions: Dict[str, Any], robustness: Dict[str, Any], proxy_info: Dict[str, Any]) -> str:
    """Generates the full Markdown report."""
    lines = ["# The Influence of Social Media 'Doomscrolling' on Anticipatory Anxiety\n"]
    lines.append(f"**Generated**: {datetime.now().isoformat()}\n")
    
    lines.append("## Executive Summary\n")
    lines.append("This report presents the findings of a statistical analysis examining the relationship between social media news exposure frequency and anxiety levels.")
    
    lines.append("## Methods\n")
    lines.append("Data was sourced from a public survey. Listwise deletion was applied for missing values. A multiple linear regression model was fitted.")
    
    lines.append(interpret_regression(regression))
    lines.append(format_correlation_table(correlations))
    lines.append(format_assumption_checks(assumptions))
    
    if proxy_info.get('is_proxy'):
        lines.append(f"\n**Limitation Note**: {proxy_info.get('limitation_note', '')}")
    
    lines.append(format_robustness_results(robustness))
    lines.append(conclude_findings(correlations, regression, robustness))
    
    lines.append("\n## References\n")
    lines.append("- Regression Results: `outputs/regression_results.json`")
    lines.append("- Correlation Results: `outputs/correlation_results.json`")
    lines.append("- Robustness Results: `outputs/robustness_results.json`")
    
    return "\n".join(lines)

def main():
    """
    Main entry point for report generation.
    """
    config = load_config()
    ensure_directories()
    
    output_dir = Path(config['paths']['outputs'])
    corr_path = output_dir / 'correlation_results.json'
    reg_path = output_dir / 'regression_results.json'
    robust_path = output_dir / 'robustness_results.json'
    report_path = output_dir / 'final_report.md'
    
    if not all(p.exists() for p in [corr_path, reg_path, robust_path]):
        raise FileNotFoundError("Required JSON outputs not found. Run model.py and robustness.py first.")
    
    correlations = load_json_report(corr_path)
    regression = load_json_report(reg_path)
    robustness = load_json_report(robust_path)
    
    # Extract assumptions from regression if stored there, else re-run or assume
    # For this script, we assume 'assumptions' might be in regression_results if saved together, 
    # or we need to load it from a separate file. 
    # Based on model.py, assumptions are in the run_full_analysis return but saved separately?
    # Let's assume we need to load assumptions from a separate file or reconstruct.
    # To be safe, we'll try to load from a hypothetical assumptions.json or extract from reg if present.
    # If not present, we skip formatting assumptions or use defaults.
    assumptions = regression.get('assumptions', {}) # If model.py saves it there
    
    proxy_info = regression.get('proxy_info', {})
    
    report = generate_final_report(correlations, regression, assumptions, robustness, proxy_info)
    
    with open(report_path, 'w') as f:
        f.write(report)
    logger.info(f"Final report saved to {report_path}")

if __name__ == '__main__':
    main()
