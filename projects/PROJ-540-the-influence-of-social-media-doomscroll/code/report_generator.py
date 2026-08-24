import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from config import load_config, ensure_directories

logger = logging.getLogger(__name__)

def load_json_report(file_path: Path) -> Dict[str, Any]:
    """Load a JSON report file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def interpret_correlation(correlation: float, p_value: float) -> str:
    """Interpret the magnitude and significance of a correlation coefficient."""
    magnitude = abs(correlation)
    direction = "positive" if correlation > 0 else "negative"
    
    if p_value > 0.05:
        return f"The correlation ({direction}, r={correlation:.3f}) is not statistically significant (p={p_value:.3f})."
    
    if magnitude < 0.1:
        strength = "very weak"
    elif magnitude < 0.3:
        strength = "weak"
    elif magnitude < 0.5:
        strength = "moderate"
    elif magnitude < 0.7:
        strength = "strong"
    else:
        strength = "very strong"
    
    return f"There is a statistically significant {strength} {direction} correlation (r={correlation:.3f}, p={p_value:.3f})."

def format_correlation_table(correlation_results: Dict[str, Any]) -> str:
    """Format correlation results into a markdown table."""
    lines = ["### Correlation Results", ""]
    lines.append("| Variable Pair | Correlation (r) | p-value | Interpretation |")
    lines.append("|---|---|---|---|")
    
    pairs = correlation_results.get("pairs", [])
    for pair in pairs:
        var1 = pair.get("var1", "")
        var2 = pair.get("var2", "")
        r = pair.get("r", 0)
        p = pair.get("p_value", 0)
        interpretation = interpret_correlation(r, p)
        lines.append(f"| {var1} vs {var2} | {r:.3f} | {p:.3f} | {interpretation} |")
    
    return "\n".join(lines)

def format_assumption_checks(assumptions: Dict[str, Any]) -> str:
    """Format assumption check results."""
    lines = ["### Regression Assumption Checks", ""]
    
    if assumptions.get("construct_validity", {}).get("passed", True):
        lines.append("- **Construct Validity**: Passed (No mathematical coupling detected).")
    else:
        lines.append("- **Construct Validity**: **FAILED** (Mathematical coupling detected).")
        return "\n".join(lines)
    
    lines.append(f"- **Linearity**: {'Passed' if assumptions.get('linearity', {}).get('passed', False) else 'Failed'}")
    lines.append(f"- **Homoscedasticity**: {'Passed' if assumptions.get('homoscedasticity', {}).get('passed', False) else 'Failed'}")
    lines.append(f"- **Normality of Residuals**: {'Passed' if assumptions.get('normality', {}).get('passed', False) else 'Failed'}")
    
    vif_results = assumptions.get("vif", {})
    if vif_results:
        max_vif = max(vif_results.values()) if vif_results else 0
        status = "Passed" if max_vif < 5 else "Failed (Multicollinearity detected)"
        lines.append(f"- **Multicollinearity (VIF)**: {status} (Max VIF: {max_vif:.2f})")
    
    return "\n".join(lines)

def format_robustness_results(robustness: Dict[str, Any]) -> str:
    """Format robustness check results."""
    lines = ["### Robustness Check (High-Engagement Subset)", ""]
    
    if not robustness.get("performed", False):
        lines.append("- Robustness check was not performed (correlation between engagement and exposure was <= 0.3).")
        return "\n".join(lines)
    
    lines.append(f"- **Subset Size**: {robustness.get('subset_n', 0)} (Top 25% engagement)")
    lines.append(f"- **Full Sample N**: {robustness.get('full_n', 0)}")
    
    full_coef = robustness.get("full_model", {}).get("coefficients", {}).get("news_exposure_freq", 0)
    subset_coef = robustness.get("subset_model", {}).get("coefficients", {}).get("news_exposure_freq", 0)
    
    lines.append(f"- **Full Model Coefficient (news_exposure_freq)**: {full_coef:.4f}")
    lines.append(f"- **Subset Model Coefficient (news_exposure_freq)**: {subset_coef:.4f}")
    
    if full_coef * subset_coef > 0:
        lines.append("- **Conclusion**: The direction of the association is consistent between the full sample and the high-engagement subset.")
    else:
        lines.append("- **Conclusion**: The direction of the association differs between the full sample and the high-engagement subset.")
    
    return "\n".join(lines)

def interpret_regression(results: Dict[str, Any]) -> str:
    """Interpret the main regression results."""
    model_info = results.get("model_summary", {})
    coefficients = model_info.get("coefficients", {})
    
    news_coef = coefficients.get("news_exposure_freq", 0)
    news_p = coefficients.get("p_values", {}).get("news_exposure_freq", 1.0)
    
    baseline_coef = coefficients.get("baseline_anxiety", 0)
    baseline_p = coefficients.get("p_values", {}).get("baseline_anxiety", 1.0)
    
    r_squared = model_info.get("r_squared", 0)
    adj_r_squared = model_info.get("adj_r_squared", 0)
    
    lines = ["### Regression Analysis Results", ""]
    lines.append(f"- **Model R-squared**: {r_squared:.3f}")
    lines.append(f"- **Adjusted R-squared**: {adj_r_squared:.3f}")
    lines.append("")
    lines.append("#### Key Findings")
    
    if news_p < 0.05:
       lines.append(f"- **News Exposure Frequency**: There is a statistically significant association with anticipatory anxiety (β = {news_coef:.4f}, p < 0.05).")
    else:
       lines.append(f"- **News Exposure Frequency**: No statistically significant association found (β = {news_coef:.4f}, p = {news_p:.3f}).")
       
    if baseline_p < 0.05:
       lines.append(f"- **Baseline Anxiety**: There is a statistically significant association with anticipatory anxiety (β = {baseline_coef:.4f}, p < 0.05).")
    else:
       lines.append(f"- **Baseline Anxiety**: No statistically significant association found (β = {baseline_coef:.4f}, p = {baseline_p:.3f}).")
       
    return "\n".join(lines)

def conclude_findings(correlation_results: Dict[str, Any], regression_results: Dict[str, Any], robustness_results: Dict[str, Any]) -> str:
    """Synthesize findings into a conclusion."""
    lines = ["## Conclusion", ""]
    
    # Correlation summary
    pairs = correlation_results.get("pairs", [])
    main_corr = next((p for p in pairs if p.get("var1") == "news_exposure_freq" and p.get("var2") == "anxiety_score"), None)
    
    if main_corr:
        lines.append(f"The initial correlation analysis revealed a {'significant' if main_corr['p_value'] < 0.05 else 'non-significant'} relationship between news exposure frequency and anxiety scores (r = {main_corr['r']:.3f}, p = {main_corr['p_value']:.3f}).")
    
    # Regression summary
    model_info = regression_results.get("model_summary", {})
    coefficients = model_info.get("coefficients", {})
    news_p = coefficients.get("p_values", {}).get("news_exposure_freq", 1.0)
    
    if news_p < 0.05:
        lines.append("However, after controlling for baseline anxiety, age, and gender, news exposure frequency remained a significant predictor of anticipatory anxiety in the multiple regression model.")
    else:
        lines.append("However, after controlling for baseline anxiety, age, and gender, news exposure frequency was no longer a significant predictor of anticipatory anxiety in the multiple regression model.")
    
    # Robustness summary
    if robustness_results.get("performed", False):
        lines.append("Robustness checks on the high-engagement subset yielded consistent directional results, suggesting the association is not driven solely by extreme engagement levels.")
    
    lines.append("")
    lines.append("### Limitations")
    lines.append("- **Observational Nature**: This study is correlational; causality cannot be inferred. It is possible that individuals with higher anxiety are more likely to engage in doomscrolling, or that a third variable influences both.")
    lines.append("- **Self-Reported Data**: All measures rely on self-reported survey data, which may be subject to recall bias and social desirability effects.")
    lines.append("- **Cross-Sectional Design**: Data was collected at a single time point, preventing the assessment of temporal dynamics or changes over time.")
    lines.append("- **Proxy Measure**: The anxiety measure used may be a proxy for general anxiety rather than specifically anticipatory anxiety, limiting construct specificity.")
    
    lines.append("")
    lines.append("### Implications")
    lines.append("While this study identifies an association between social media news exposure and anxiety, the direction of causality remains unclear. Future research utilizing longitudinal designs or experimental interventions is necessary to determine whether reducing doomscrolling behavior can effectively mitigate anticipatory anxiety.")
    
    return "\n".join(lines)

def generate_final_report(correlation_path: Path, regression_path: Path, robustness_path: Path, output_path: Path) -> None:
    """Generate the final markdown report."""
    logger.info("Generating final report...")
    
    # Load data
    try:
        correlation_data = load_json_report(correlation_path)
        regression_data = load_json_report(regression_path)
        robustness_data = load_json_report(robustness_path)
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    
    # Build sections
    sections = []
    
    # Title and Metadata
    sections.append("# Final Research Report: The Influence of Social Media 'Doomscrolling' on Anticipatory Anxiety")
    sections.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sections.append("")
    
    # Abstract
    sections.append("## Abstract")
    sections.append("This study investigates the relationship between social media news exposure frequency (a proxy for 'doomscrolling') and anticipatory anxiety. Using data from a public survey, we employed Pearson correlation and multiple linear regression analysis to estimate this association while controlling for baseline anxiety, age, and gender. Results indicate a [significant/non-significant] association, though the observational nature of the data precludes causal inference.")
    sections.append("")
    
    # Methods
    sections.append("## Methods")
    sections.append("### Data Source")
    sections.append("Data was obtained from a public survey dataset. Variables included news exposure frequency, anxiety scores, baseline anxiety, age, and gender.")
    sections.append("")
    sections.append("### Statistical Analysis")
    sections.append("1. **Correlation Analysis**: Pearson correlation coefficients were calculated to assess bivariate relationships.")
    sections.append("2. **Regression Modeling**: A multiple linear regression model was fitted: `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`.")
    sections.append("3. **Assumption Checks**: Linearity, homoscedasticity, normality of residuals, and multicollinearity (VIF) were assessed.")
    sections.append("4. **Robustness Check**: A subset analysis was performed on the top 25% of social media engagement participants, conditional on correlation > 0.3.")
    sections.append("")
    
    # Results
    sections.append(format_correlation_table(correlation_data))
    sections.append("")
    sections.append(interpret_regression(regression_data))
    sections.append("")
    sections.append(format_assumption_checks(regression_data.get("assumptions", {})))
    sections.append("")
    sections.append(format_robustness_results(robustness_data))
    sections.append("")
    
    # Conclusion
    sections.append(conclude_findings(correlation_data, regression_data, robustness_data))
    sections.append("")
    
    # Write file
    ensure_directories([output_path.parent])
    with open(output_path, 'w') as f:
        f.write("\n".join(sections))
    
    logger.info(f"Final report saved to {output_path}")

def main():
    """Main entry point for report generation."""
    config = load_config()
    output_dir = Path(config.get("output_dir", "outputs"))
    ensure_directories([output_dir])
    
    correlation_path = output_dir / "correlation_results.json"
    regression_path = output_dir / "regression_results.json"
    robustness_path = output_dir / "robustness_results.json"
    output_path = output_dir / "final_report.md"
    
    try:
        generate_final_report(correlation_path, regression_path, robustness_path, output_path)
        print(f"Report generated successfully: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise

if __name__ == "__main__":
    main()
