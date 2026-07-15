import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# Import from existing API surface
# Note: analysis.py provides run_correlation_analysis which returns the results dict
# We assume the results are saved to a file or we load them from memory if run in sequence
# For this script, we expect the analysis to have been run and results saved, or we load from the analysis module's output.
# Since analysis.py exports run_correlation_analysis, we will import it to ensure we have the logic,
# but primarily we will load the saved artifacts (sensitivity_table.csv, etc.) if they exist,
# or run the analysis if not (to ensure data exists).
# However, to keep this task focused on REPORTING, we assume the data artifacts exist.
# We will read the sensitivity table and the correlation results.

# To handle the "load_analysis_results" function mentioned in the API surface,
# we must ensure it exists or implement the loading logic here if it's missing from analysis.py.
# Given the API surface says `from analysis import ... load_analysis_results` is NOT listed,
# but `from report import ... load_analysis_results` IS listed in the public names for report.py,
# we must define `load_analysis_results` in THIS file (report.py) as per the API contract.

def load_config(config_path='code/config.yaml'):
    """Load pipeline configuration."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(results_dir='data/analysis'):
    """
    Load analysis results from the data/analysis directory.
    Returns a dictionary containing correlation results and sensitivity table.
    """
    results = {}
    
    # Load correlation results (assuming saved as correlation_results.json or similar by analysis.py)
    # Since analysis.py is not fully implemented in the provided context for saving,
    # we assume the standard output files exist as per T021 and T019.
    
    # Check for sensitivity table (T021)
    sensitivity_path = os.path.join(results_dir, 'sensitivity_table.csv')
    if os.path.exists(sensitivity_path):
        results['sensitivity_table'] = pd.read_csv(sensitivity_path)
    else:
        # If not found, we might need to run the analysis or return empty
        # For a robust report, we expect this file to exist if analysis ran.
        results['sensitivity_table'] = None

    # Check for correlation results (T019)
    # We assume analysis.py saves a 'correlation_results.csv' or 'correlation_results.json'
    corr_csv = os.path.join(results_dir, 'correlation_results.csv')
    if os.path.exists(corr_csv):
        results['correlations'] = pd.read_csv(corr_csv)
    else:
        results['correlations'] = None

    # Check for effect sizes if saved separately, otherwise we calculate them
    results['effect_sizes'] = None

    return results

def calculate_effect_size(r_value, n):
    """
    Calculate Cohen's q or similar effect size from correlation coefficient.
    For correlation, we can use r itself as the effect size, or Fisher's z.
    Here we return r and a simple interpretation.
    """
    if r_value is None or n is None:
        return None
    
    # Cohen's guidelines for r: 0.1 small, 0.3 medium, 0.5 large
    magnitude = "negligible"
    if abs(r_value) >= 0.5:
        magnitude = "large"
    elif abs(r_value) >= 0.3:
        magnitude = "medium"
    elif abs(r_value) >= 0.1:
        magnitude = "small"
        
    return {
        'r': r_value,
        'magnitude': magnitude,
        'n': n
    }

def generate_report(results, output_path='data/analysis/final_report.md'):
    """
    Generate the final report with statistical significance, effect sizes,
    and limitations, explicitly discussing adaptive vs degenerative complexity.
    """
    if not results:
        return "No results found to generate report."

    correlations = results.get('correlations')
    sensitivity = results.get('sensitivity_table')

    report_lines = []
    report_lines.append("# Final Report: Predicting Cognitive Fatigue from Resting-State EEG Complexity")
    report_lines.append("")
    report_lines.append("## 1. Executive Summary")
    report_lines.append("")
    report_lines.append("This report presents the findings from the analysis of the relationship between")
    report_lines.append("EEG complexity metrics (Lempel-Ziv Complexity and Permutation Entropy) and")
    report_lines.append("cognitive fatigue scores. The analysis aimed to distinguish between adaptive")
    report_lines.append("simplification (reduced complexity as a regulatory mechanism) and degenerative")
    report_lines.append("noise (increased complexity due to loss of control).")
    report_lines.append("")

    # Statistical Significance Section
    report_lines.append("## 2. Statistical Significance and Correlation Analysis")
    report_lines.append("")
    
    if correlations is not None and not correlations.empty:
        report_lines.append("### 2.1 Correlation Results")
        report_lines.append("")
        report_lines.append("| Channel | Metric | Correlation (r) | P-value | Adjusted P-value | Significance (p<=0.05) |")
        report_lines.append("|---|---|---|---|---|---|")
        
        significant_count = 0
        for _, row in correlations.iterrows():
            r = row.get('correlation', 0)
            p = row.get('p_value', 1)
            adj_p = row.get('adj_p_value', 1)
            sig = "Yes" if adj_p <= 0.05 else "No"
            if sig == "Yes":
                significant_count += 1
            report_lines.append(f"| {row.get('channel', 'N/A')} | {row.get('metric', 'N/A')} | {r:.4f} | {p:.4f} | {adj_p:.4f} | {sig} |")
        
        report_lines.append("")
        report_lines.append(f"**Summary**: {significant_count} out of {len(correlations)} tests showed statistically significant correlations after Benjamini-Hochberg correction.")
        report_lines.append("")

        # Effect Sizes
        report_lines.append("### 2.2 Effect Sizes")
        report_lines.append("")
        report_lines.append("Effect sizes (magnitude of correlation) were interpreted using Cohen's guidelines:")
        report_lines.append("- Small: |r| >= 0.1")
        report_lines.append("- Medium: |r| >= 0.3")
        report_lines.append("- Large: |r| >= 0.5")
        report_lines.append("")
        
        for _, row in correlations.iterrows():
            r = row.get('correlation', 0)
            magnitude = "negligible"
            if abs(r) >= 0.5:
                magnitude = "large"
            elif abs(r) >= 0.3:
                magnitude = "medium"
            elif abs(r) >= 0.1:
                magnitude = "small"
            report_lines.append(f"- **{row.get('channel', 'N/A')} ({row.get('metric', 'N/A')})**: r={r:.3f} ({magnitude})")
        report_lines.append("")

    else:
        report_lines.append("No correlation data available. Ensure `code/analysis.py` has been executed successfully.")
        report_lines.append("")

    # Adaptive vs Degenerative Discussion
    report_lines.append("## 3. Interpretation: Adaptive vs. Degenerative Complexity")
    report_lines.append("")
    report_lines.append("The core hypothesis of this study rests on the distinction between two potential")
    report_lines.append("mechanisms of fatigue-related complexity changes:")
    report_lines.append("")
    report_lines.append("1.  **Adaptive Simplification**: A reduction in EEG complexity (lower LZC/PE)")
    report_lines.append("    indicating the brain is adopting a more efficient, stereotyped strategy to")
    report_lines.append("    conserve energy under fatigue. This would manifest as a **negative correlation**")
    report_lines.append("    between fatigue scores and complexity metrics.")
    report_lines.append("")
    report_lines.append("2.  **Degenerative Noise**: An increase in EEG complexity (higher LZC/PE)")
    report_lines.append("    indicating a loss of structured control and the emergence of random, inefficient")
    report_lines.append("    neural firing. This would manifest as a **positive correlation**.")
    report_lines.append("")
    
    if correlations is not None and not correlations.empty:
        # Analyze direction of significant correlations
        pos_sig = correlations[(correlations['adj_p_value'] <= 0.05) & (correlations['correlation'] > 0)]
        neg_sig = correlations[(correlations['adj_p_value'] <= 0.05) & (correlations['correlation'] < 0)]
        
        if len(pos_sig) > 0 and len(neg_sig) == 0:
            report_lines.append("**Finding**: Significant positive correlations were observed, supporting the **Degenerative Noise** hypothesis.")
            report_lines.append("Fatigue appears to be associated with a breakdown in the structured organization of neural activity.")
        elif len(neg_sig) > 0 and len(pos_sig) == 0:
            report_lines.append("**Finding**: Significant negative correlations were observed, supporting the **Adaptive Simplification** hypothesis.")
            report_lines.append("Fatigue appears to drive the brain towards more efficient, lower-dimensional states.")
        elif len(pos_sig) > 0 and len(neg_sig) > 0:
            report_lines.append("**Finding**: Mixed results were observed. Some channels/metrics suggest adaptive simplification,")
            report_lines.append("while others suggest degenerative noise. This may indicate a complex, spatially heterogeneous")
            report_lines.append("response to fatigue, or that different frequency bands/channels reflect different mechanisms.")
        else:
            report_lines.append("**Finding**: No statistically significant correlations were found to support either hypothesis definitively.")
    else:
        report_lines.append("No data available to interpret the mechanism.")
    report_lines.append("")

    # Sensitivity Analysis
    if sensitivity is not None and not sensitivity.empty:
        report_lines.append("## 4. Sensitivity Analysis")
        report_lines.append("")
        report_lines.append("The robustness of the findings was tested at different significance thresholds.")
        report_lines.append("")
        report_lines.append(sensitivity.to_markdown(index=False))
        report_lines.append("")

    # Limitations
    report_lines.append("## 5. Limitations")
    report_lines.append("")
    report_lines.append("- **Dataset Constraints**: The analysis is limited to the specific characteristics of the")
    report_lines.append("  Sleep-EDF or SHHS dataset (e.g., age range, health status), which may limit generalizability")
    report_lines.append("  to other populations (e.g., clinical sleep disorders, extreme fatigue states).")
    report_lines.append("- **Complexity Metrics**: Lempel-Ziv Complexity and Permutation Entropy are sensitive to")
    report_lines.append("  signal length and noise. While artifact rejection was applied, residual artifacts may")
    report_lines.append("  influence the complexity estimates.")
    report_lines.append("- **Causality**: This study is correlational. We cannot infer that changes in complexity")
    report_lines.append("  cause fatigue, or vice versa, without experimental manipulation.")
    report_lines.append("- **Single Subject/Group Level**: Depending on the analysis mode (paired vs cross-sectional),")
    report_lines.append("  the power to detect individual differences may be limited.")
    report_lines.append("")

    report_lines.append("## 6. Conclusion")
    report_lines.append("")
    report_lines.append("This analysis provides initial evidence regarding the relationship between EEG complexity")
    report_lines.append("and cognitive fatigue. The results suggest [Insert specific conclusion based on findings above].")
    report_lines.append("Future work should focus on validating these findings in controlled experimental settings")
    report_lines.append("with specific fatigue induction protocols.")
    report_lines.append("")

    full_report = "\n".join(report_lines)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(full_report)
    
    print(f"Report generated successfully: {output_path}")
    return full_report

def main():
    """Main entry point for report generation."""
    try:
        config = load_config()
        results = load_analysis_results()
        
        if not results or (results.get('correlations') is None and results.get('sensitivity_table') is None):
            print("Warning: No analysis results found. Ensure analysis.py has been run.")
            # Optionally, we could run analysis here, but for this task we focus on reporting.
            # If we must ensure the report exists, we might generate a "No Data" report,
            # but the task implies real data exists.
        
        generate_report(results)
        
    except Exception as e:
        print(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()