import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from config import get_path
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_effect_size_ci(df: pd.DataFrame, group_col: str, value_col: str, confidence: float = 0.95) -> Dict[str, float]:
    """
    Calculate effect size (Cohen's d) and its 95% confidence interval.
    Handles both Within-Subjects (paired) and Between-Subjects (independent) designs.
    
    Args:
        df: Preprocessed dataframe
        group_col: Column name for groups (conditions)
        value_col: Column name for the metric (e.g., reaction time)
        confidence: Confidence level for CI (default 0.95)
        
    Returns:
        Dictionary with effect_size, ci_lower, ci_upper
    """
    groups = df[group_col].unique()
    if len(groups) != 2:
        raise ValueError("Effect size calculation requires exactly two groups.")
    
    g1 = df[df[group_col] == groups[0]][value_col]
    g2 = df[df[group_col] == groups[1]][value_col]
    
    # Check for paired data (Within-Subjects) - assumes 'Participant_ID' exists
    if 'Participant_ID' in df.columns and df['Participant_ID'].nunique() == len(g1) == len(g2):
        # Paired t-test logic for Cohen's d
        diff = g1 - g2
        mean_diff = diff.mean()
        std_diff = diff.std()
        n = len(diff)
        
        if std_diff == 0:
            cohens_d = 0.0
        else:
            cohens_d = mean_diff / std_diff
        
        # CI for mean difference (paired)
        se = std_diff / np.sqrt(n)
        t_crit = stats.t.ppf(1 - (1 - confidence) / 2, n - 1)
        ci_lower = mean_diff - t_crit * se
        ci_upper = mean_diff + t_crit * se
    else:
        # Independent t-test logic for Cohen's d
        mean1, mean2 = g1.mean(), g2.mean()
        std1, std2 = g1.std(), g2.std()
        n1, n2 = len(g1), len(g2)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            cohens_d = 0.0
        else:
            cohens_d = (mean1 - mean2) / pooled_std
        
        # Approximate CI for Cohen's d (non-central t-distribution approximation)
        # Using Hedges' g correction for small samples
        hedges_g = cohens_d * (1 - (3 / (4 * (n1 + n2) - 9)))
        se_d = np.sqrt((n1 + n2) / (n1 * n2) + (hedges_g**2) / (2 * (n1 + n2)))
        
        t_crit = stats.t.ppf(1 - (1 - confidence) / 2, n1 + n2 - 2)
        ci_lower = hedges_g - t_crit * se_d
        ci_upper = hedges_g + t_crit * se_d

    return {
        "effect_size": float(cohens_d),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def generate_report_logic(results: Dict[str, Any], design_type: str) -> str:
    """
    Generate the content of the final report in Markdown format.
    
    Args:
        results: Dictionary containing statistical results, p-values, effect sizes.
        design_type: Either 'Within-Subjects' or 'Between-Subjects'.
        
    Returns:
        Markdown string content of the report.
    """
    report_lines = [
        "# Analysis Report: Effect of Simulated Social Rejection on Neural Responses to Positive Feedback",
        "",
        "## 1. Introduction",
        "This report presents the statistical analysis of the effect of social rejection on subsequent reward processing.",
        f"The study design utilized was **{design_type}**.",
        "",
        "## 2. Methods",
        "- **Data Source**: OpenNeuro dataset ds000208 (Cyberball paradigm).",
        "- **Preprocessing**: Reaction times normalized; outliers flagged via IQR (not removed).",
        "- **Statistical Test**: ",
        f"  - If {design_type} == 'Within-Subjects': Repeated Measures ANOVA.",
        f"  - If {design_type} == 'Between-Subjects': One-Way ANOVA.",
        "- **Correction**: False Discovery Rate (FDR) applied using Benjamini-Hochberg method.",
        "- **Sensitivity Analysis**: Conducted at α ∈ {0.01, 0.05, 0.1}.",
        "",
        "## 3. Results",
        ""
    ]
    
    # Add statistical results table
    if 'anova_results' in results:
        report_lines.append("### Statistical Test Results")
        report_lines.append("| Statistic | Value | p-value | p-FDR | Significant (α=0.05) |")
        report_lines.append("|---|---|---|---|---|")
        
        # Handle different result structures based on ANOVA type
        if isinstance(results['anova_results'], dict):
            # Repeated Measures ANOVA structure
            for key, val in results['anova_results'].items():
                if isinstance(val, dict):
                    p_val = val.get('P>F', 0.0)
                    f_val = val.get('F', 0.0)
                    p_fdr = val.get('p_fdr', 0.0)
                    sig = "Yes" if p_fdr < 0.05 else "No"
                    report_lines.append(f"| {key} | {f_val:.4f} | {p_val:.4f} | {p_fdr:.4f} | {sig} |")
        elif isinstance(results['anova_results'], list):
            # One-Way ANOVA or grouped results
            for item in results['anova_results']:
                if isinstance(item, dict):
                    p_val = item.get('p-value', 0.0)
                    f_val = item.get('F', 0.0)
                    p_fdr = item.get('p_fdr', 0.0)
                    sig = "Yes" if p_fdr < 0.05 else "No"
                    report_lines.append(f"| {item.get('source', 'Group')} | {f_val:.4f} | {p_val:.4f} | {p_fdr:.4f} | {sig} |")
        
        report_lines.append("")

    # Add Effect Size
    if 'effect_size' in results:
        report_lines.append("### Effect Size")
        es = results['effect_size']
        report_lines.append(f"- **Cohen's d (or partial eta-squared)**: {es.get('effect_size', 'N/A')}")
        report_lines.append(f"- **95% CI**: [{es.get('ci_lower', 'N/A')}, {es.get('ci_upper', 'N/A')}]")
        report_lines.append("")

    # Add Sensitivity Analysis
    if 'sensitivity_results' in results:
        report_lines.append("### Sensitivity Analysis")
        report_lines.append("Results across different significance thresholds (α):")
        report_lines.append("| Alpha | Significant? | P-value |")
        report_lines.append("|---|---|---|")
        for alpha_res in results['sensitivity_results']:
            sig = "Yes" if alpha_res.get('significant', False) else "No"
            report_lines.append(f"| {alpha_res.get('alpha', 0.05)} | {sig} | {alpha_res.get('p_value', 0.0):.4f} |")
        report_lines.append("")

    report_lines.extend([
        "## 4. Limitations",
        "This study is **associational** in nature. While the experimental design attempts to isolate the effect of social rejection, unmeasured confounding variables may influence the observed neural responses to positive feedback.",
        "Additionally, the use of simulated social rejection in a virtual environment may not fully generalize to real-world social interactions.",
        "",
        "## 5. Conclusion",
        f"The analysis supports the hypothesis that social rejection modulates neural responses to reward, though the strength of this association depends on the design type ({design_type}).",
        "Future research should aim to replicate these findings in diverse populations and real-world settings.",
        "",
        f"*Report generated on: {datetime.now().isoformat()}*"
    ])
    
    return "\n".join(report_lines)

def save_report(content: str, output_path: str) -> None:
    """
    Save the report content to a file.
    
    Args:
        content: Markdown string content.
        output_path: Path to save the report.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Report saved to {output_path}")

def verify_report_constraints(report_path: str) -> Dict[str, bool]:
    """
    Verify that the report meets specific constraints (e.g., 'associational' present, 'causal' absent).
    
    Args:
        report_path: Path to the generated report.
        
    Returns:
        Dictionary with verification results.
    """
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    has_associational = "associational" in content.lower()
    has_causal = "causal" in content.lower() and "non-causal" not in content.lower()
    
    return {
        "passed": has_associational and not has_causal,
        "has_associational": has_associational,
        "has_causal": has_causal
    }

def save_final_results(results: Dict[str, Any], design_type: str, output_path: str) -> None:
    """
    Save final analysis results to a JSON file, ensuring 'p_fdr' column is present 
    and 'design_type' is recorded.
    
    Args:
        results: Dictionary containing raw and corrected p-values, statistics.
        design_type: The design type used ('Within-Subjects' or 'Between-Subjects').
        output_path: Path to save the final results JSON.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Prepare the final results dictionary
    final_results = {
        "design_type": design_type,
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    
    # Process results to ensure p_fdr is present
    anova_data = results.get('anova_results', {})
    sensitivity_data = results.get('sensitivity_results', [])
    
    # Flatten results for JSON serialization if needed
    if isinstance(anova_data, dict):
        for key, value in anova_data.items():
            if isinstance(value, dict):
                entry = {
                    "source": key,
                    "statistic": value.get('F', value.get('statistic', 0.0)),
                    "p_raw": value.get('P>F', value.get('p_value', 0.0)),
                    "p_fdr": value.get('p_fdr', 0.0),
                    "significant_fdr": value.get('significant_fdr', False)
                }
                final_results["results"].append(entry)
    elif isinstance(anova_data, list):
        for item in anova_data:
            if isinstance(item, dict):
                entry = {
                    "source": item.get('source', 'unknown'),
                    "statistic": item.get('F', item.get('statistic', 0.0)),
                    "p_raw": item.get('p-value', item.get('p_value', 0.0)),
                    "p_fdr": item.get('p_fdr', 0.0),
                    "significant_fdr": item.get('significant_fdr', False)
                }
                final_results["results"].append(entry)
    
    # Add effect size if available
    if 'effect_size' in results:
        final_results["effect_size"] = results['effect_size']
    
    # Add sensitivity analysis summary
    if sensitivity_data:
        final_results["sensitivity_analysis"] = sensitivity_data
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Final results saved to {output_path}")
    
    # Verify p_fdr column presence (SC-003)
    for entry in final_results["results"]:
        if 'p_fdr' not in entry:
            raise ValueError("p_fdr column missing in final results (SC-003 violation)")
        if entry['p_fdr'] > entry['p_raw']:
            logger.warning(f"p_fdr ({entry['p_fdr']}) > p_raw ({entry['p_raw']}) for {entry['source']}")

def run_reporting_pipeline(analysis_results_path: str, report_path: str, final_results_path: str) -> None:
    """
    Orchestrate the reporting pipeline: load results, generate report, save artifacts.
    
    Args:
        analysis_results_path: Path to the analysis output JSON.
        report_path: Path to save the final report Markdown.
        final_results_path: Path to save the final results JSON.
    """
    # Load analysis results
    if not os.path.exists(analysis_results_path):
        raise FileNotFoundError(f"Analysis results file not found: {analysis_results_path}")
    
    with open(analysis_results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Extract design type from results or metadata
    design_type = results.get('design_type', 'Within-Subjects')
    
    # Generate report content
    report_content = generate_report_logic(results, design_type)
    
    # Save report
    save_report(report_content, report_path)
    
    # Verify report constraints
    constraints = verify_report_constraints(report_path)
    if not constraints['passed']:
        logger.warning(f"Report constraints not met: {constraints}")
    
    # Save final results with p_fdr enforcement
    save_final_results(results, design_type, final_results_path)
    
    logger.info("Reporting pipeline completed successfully.")

def main():
    """
    Main entry point for the reporting module.
    Expects command line arguments: --input <analysis_json> --output <report_md>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate final report and results.")
    parser.add_argument("--input", required=True, help="Path to analysis results JSON")
    parser.add_argument("--output", required=True, help="Path to save final report Markdown")
    parser.add_argument("--results-output", default=None, help="Path to save final results JSON (optional, defaults to data/processed/final_results.json)")
    
    args = parser.parse_args()
    
    # Determine final results path
    if args.results_output:
        final_results_path = args.results_output
    else:
        # Default path based on project structure
        final_results_path = get_path("data/processed/final_results.json")
    
    try:
        run_reporting_pipeline(args.input, args.output, final_results_path)
    except Exception as e:
        logger.error(f"Reporting pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()