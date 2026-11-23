"""
Report generation module for the Doomscrolling Anxiety Analysis Pipeline.
Generates final markdown report summarizing findings.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from config import load_config

logger = logging.getLogger(__name__)

def load_json_report(path: Path) -> Dict[str, Any]:
    """Load a JSON report file."""
    with open(path, 'r') as f:
        return json.load(f)

def interpret_correlation(correlation_results: Dict[str, Any]) -> str:
    """Interpret correlation results for the report."""
    text = []
    
    if 'news_exposure_anxiety' in correlation_results:
        corr = correlation_results['news_exposure_anxiety']
        r = corr.get('pearson', {}).get('r', 0)
        p = corr.get('pearson', {}).get('p_value', 1)
        
        direction = "positive" if r > 0 else "negative" if r < 0 else "no"
        strength = "strong" if abs(r) > 0.5 else "moderate" if abs(r) > 0.3 else "weak"
        
        significance = "statistically significant" if p < 0.05 else "not statistically significant"
        
        text.append(f"The Pearson correlation between news exposure frequency and anxiety score is {r:.3f}, indicating a {direction} {strength} relationship. This result is {significance} (p = {p:.4f}).")
    
    return "\n".join(text)

def format_correlation_table(correlation_results: Dict[str, Any]) -> str:
    """Format correlation results as a markdown table."""
    lines = ["| Variable Pair | Pearson r | p-value | Spearman r | p-value |",
             "|-------------|-----------|---------|------------|---------|"]
    
    for pair, results in correlation_results.items():
        pearson = results.get('pearson', {})
        spearman = results.get('spearman', {})
        r_p = pearson.get('r', 'N/A')
        p_p = pearson.get('p_value', 'N/A')
        r_s = spearman.get('r', 'N/A')
        p_s = spearman.get('p_value', 'N/A')
        lines.append(f"| {pair} | {r_p:.3f} | {p_p:.4f} | {r_s:.3f} | {p_s:.4f} |")
    
    return "\n".join(lines)

def format_assumption_checks(assumptions: Dict[str, Any]) -> str:
    """Format assumption check results."""
    lines = ["### Assumption Checks", ""]
    
    if 'linearity' in assumptions:
        linearity = assumptions['linearity']
        status = "✓ Passed" if linearity.get('passed', False) else "✗ Failed"
        lines.append(f"- **Linearity**: {status} (r = {linearity.get('correlation', 'N/A'):.3f}, p = {linearity.get('p_value', 'N/A'):.4f})")
    
    if 'homoscedasticity' in assumptions:
        homo = assumptions['homoscedasticity']
        status = "✓ Passed" if homo.get('passed', False) else "✗ Failed"
        lines.append(f"- **Homoscedasticity (Breusch-Pagan)**: {status} (p = {homo.get('p_value', 'N/A'):.4f})")
    
    if 'normality' in assumptions:
        norm = assumptions['normality']
        status = "✓ Passed" if norm.get('passed', False) else "✗ Failed"
        lines.append(f"- **Normality (Shapiro-Wilk)**: {status} (p = {norm.get('p_value', 'N/A'):.4f})")
    
    return "\n".join(lines)

def format_robustness_results(robustness_results: Dict[str, Any]) -> str:
    """Format robustness check results."""
    lines = ["### Robustness Check", ""]
    
    status = robustness_results.get('status', 'unknown')
    
    if status == 'skipped':
        reason = robustness_results.get('reason', 'Unknown reason')
        lines.append(f"**Status**: Skipped\n")
        lines.append(f"**Reason**: {reason}\n")
    elif status == 'run':
        lines.append(f"**Status**: Run\n")
        subset_n = robustness_results.get('subset', {}).get('n', 0)
        lines.append(f"**Subset Size**: {subset_n}\n")
        
        comparison = robustness_results.get('comparison', {})
        if comparison:
            lines.append("#### Coefficient Comparison")
            lines.append("| Variable | Full Sample | Subset | Change |")
            lines.append("|----------|-------------|--------|--------|")
            
            changes = comparison.get('coefficient_changes', {})
            for var, vals in changes.items():
                lines.append(f"| {var} | {vals.get('full', 'N/A'):.3f} | {vals.get('subset', 'N/A'):.3f} | {vals.get('change', 'N/A'):.3f} |")
    else:
        lines.append(f"**Status**: Error - {robustness_results.get('reason', 'Unknown')}")
    
    return "\n".join(lines)

def interpret_regression(regression_results: Dict[str, Any]) -> str:
    """Interpret regression results for the report."""
    lines = []
    
    r_squared = regression_results.get('rsquared', 0)
    f_p = regression_results.get('f_pvalue', 1)
    
    lines.append(f"The regression model explains {r_squared*100:.1f}% of the variance in anxiety scores (R² = {r_squared:.3f}). The overall model is {'statistically significant' if f_p < 0.05 else 'not statistically significant'} (F-statistic p = {f_p:.4f}).")
    
    lines.append("\n#### Model Coefficients")
    lines.append("| Variable | Coefficient | p-value |")
    lines.append("|----------|-------------|---------|")
    
    coeffs = regression_results.get('coefficients', {})
    p_vals = regression_results.get('p_values', {})
    
    for var, coef in coeffs.items():
        p = p_vals.get(var, 1)
        sig = "*" if p < 0.05 else ""
        lines.append(f"| {var} | {coef:.4f} | {p:.4f}{sig} |")
    
    # VIF
    vif = regression_results.get('vif', {})
    if vif:
        lines.append("\n#### Multicollinearity (VIF)")
        lines.append("| Variable | VIF |")
        lines.append("|----------|-----|")
        for var, val in vif.items():
            flag = " ⚠️ High" if val > 10 else ""
            lines.append(f"| {var} | {val:.2f}{flag} |")
    
    return "\n".join(lines)

def conclude_findings(correlation_results: Dict[str, Any], regression_results: Dict[str, Any], robustness_results: Dict[str, Any]) -> str:
    """Generate conclusion section."""
    lines = []
    
    # Correlation conclusion
    if 'news_exposure_anxiety' in correlation_results:
        r = correlation_results['news_exposure_anxiety'].get('pearson', {}).get('r', 0)
        p = correlation_results['news_exposure_anxiety'].get('pearson', {}).get('p_value', 1)
        if p < 0.05:
            lines.append(f"There is a statistically significant {'positive' if r > 0 else 'negative'} association between news exposure frequency and anxiety scores (r = {r:.3f}, p < 0.05).")
        else:
            lines.append(f"There is no statistically significant association between news exposure frequency and anxiety scores (r = {r:.3f}, p = {p:.4f}).")
    
    # Regression conclusion
    f_p = regression_results.get('f_pvalue', 1)
    if f_p < 0.05:
        lines.append("The multiple regression model significantly predicts anxiety scores from news exposure frequency, controlling for age and gender.")
    else:
        lines.append("The multiple regression model does not significantly predict anxiety scores.")
    
    # Robustness
    if robustness_results.get('status') == 'run':
        lines.append("The robustness check on the high-engagement subset was performed. Coefficients should be compared to assess stability.")
    else:
        lines.append(f"The robustness check was skipped: {robustness_results.get('reason', 'Unknown reason')}.")
    
    # Limitations
    lines.append("\n#### Limitations")
    lines.append("- This analysis is correlational; causality cannot be inferred.")
    lines.append("- Self-reported measures may be subject to bias.")
    lines.append("- Potential confounding variables not included in the model.")
    
    if regression_results.get('flags'):
        lines.append(f"- Flags: {', '.join(regression_results.get('flags', []))}")
    
    return "\n".join(lines)

def generate_final_report(correlation_results: Dict[str, Any], robustness_results: Dict[str, Any]):
    """
    Generate the final markdown report.
    Saves to outputs/final_report.md
    """
    logger.info("Generating final report...")
    
    # Load regression results
    reg_path = Path("outputs/regression_results.json")
    if not reg_path.exists():
        logger.error("Regression results not found.")
        return
    
    with open(reg_path, 'r') as f:
        regression_results = json.load(f)
    
    # Build report
    report_lines = []
    
    # Title
    report_lines.append("# The Influence of Social Media 'Doomscrolling' on Anticipatory Anxiety")
    report_lines.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("This analysis investigates the relationship between social media news exposure frequency and anxiety scores using survey data. A multiple linear regression model was fitted to assess the association while controlling for age and gender. Robustness checks were performed on a high-engagement subset where applicable.")
    report_lines.append("")
    
    # Methods
    report_lines.append("## Methods")
    report_lines.append("### Data Source")
    report_lines.append("Data was obtained from the NHANES 2017-2018 dataset (or fallback sources: GSS, Pew, YouGov) as per the data ingestion pipeline.")
    report_lines.append("")
    report_lines.append("### Statistical Analysis")
    report_lines.append("- **Correlation**: Pearson and Spearman correlations calculated between news exposure frequency and anxiety scores.")
    report_lines.append("- **Regression**: Multiple linear regression with formula: `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`")
    report_lines.append("- **Assumptions**: Linearity, Homoscedasticity (Breusch-Pagan), Normality (Shapiro-Wilk)")
    report_lines.append("- **Multicollinearity**: Variance Inflation Factor (VIF) calculated for all predictors.")
    report_lines.append("- **Robustness**: Re-fitting model on top 25th percentile of social media engagement (if r > 0.3).")
    report_lines.append("")
    
    # Results
    report_lines.append("## Results")
    
    report_lines.append("### Correlation Analysis")
    report_lines.append(interpret_correlation(correlation_results))
    report_lines.append("")
    report_lines.append(format_correlation_table(correlation_results))
    report_lines.append("")
    
    report_lines.append("### Regression Analysis")
    report_lines.append(interpret_regression(regression_results))
    report_lines.append("")
    
    if regression_results.get('assumptions'):
        report_lines.append(format_assumption_checks(regression_results['assumptions']))
        report_lines.append("")
    
    # Robustness Check
    report_lines.append("### Robustness Check")
    report_lines.append(format_robustness_results(robustness_results))
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append(conclude_findings(correlation_results, regression_results, robustness_results))
    report_lines.append("")
    
    # References to output files
    report_lines.append("## Output Files")
    report_lines.append("- `outputs/regression_results.json`: Full regression model results")
    report_lines.append("- `outputs/correlation_results.json`: Correlation analysis results")
    report_lines.append("- `outputs/robustness_results.json`: Robustness check results")
    report_lines.append("- `outputs/plot.png`: Scatter plot with regression line")
    report_lines.append("- `outputs/diagnostics_residuals.png`: Residuals vs Fitted plot")
    report_lines.append("- `outputs/diagnostics_qq.png`: Q-Q plot of residuals")
    report_lines.append("- `outputs/robustness_comparison.png`: Robustness comparison plot (if run)")
    report_lines.append("")
    
    # Write report
    output_path = Path("outputs/final_report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("\n".join(report_lines))
    
    logger.info(f"Final report generated: {output_path}")

def main():
    """CLI entry point for report generation."""
    try:
        # Load results
        corr_path = Path("outputs/correlation_results.json")
        robust_path = Path("outputs/robustness_results.json")
        
        if not corr_path.exists():
            logger.error("Correlation results not found.")
            return 1
        
        with open(corr_path, 'r') as f:
            correlation_results = json.load(f)
        
        if robust_path.exists():
            with open(robust_path, 'r') as f:
                robustness_results = json.load(f)
        else:
            robustness_results = {"status": "skipped", "reason": "File not found"}
        
        generate_final_report(correlation_results, robustness_results)
        return 0
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
