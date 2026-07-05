import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np

def load_config(config_path="code/config.yaml"):
    """Load pipeline configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_report(analysis_results_path, sensitivity_path, output_path):
    """
    Generate the final research report.
    
    Reads correlation analysis results and sensitivity tables, computes effect sizes,
    and writes a structured report discussing adaptive vs degenerative complexity changes.
    """
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load results
    try:
        correlations = pd.read_csv(analysis_results_path)
    except FileNotFoundError:
        print(f"Error: Analysis results not found at {analysis_results_path}")
        print("Please run code/analysis.py first to generate correlation data.")
        sys.exit(1)
    
    try:
        sensitivity = pd.read_csv(sensitivity_path)
    except FileNotFoundError:
        print(f"Error: Sensitivity table not found at {sensitivity_path}")
        sys.exit(1)

    # Compute Effect Sizes (Cohen's r from correlation coefficient)
    # r = sqrt(t^2 / (t^2 + df)) approximates to correlation itself for large N
    # We use the correlation coefficient directly as the effect size measure for r
    correlations['effect_size_r'] = correlations['correlation_coefficient'].abs()
    
    # Classify effect sizes (Cohen's guidelines)
    def classify_effect(r):
        if r < 0.1: return "Negligible"
        elif r < 0.3: return "Small"
        elif r < 0.5: return "Medium"
        else: return "Large"
    
    correlations['effect_size_category'] = correlations['effect_size_r'].apply(classify_effect)

    # Generate Report Content
    report_lines = []
    report_lines.append("# Final Report: Cognitive Fatigue and EEG Complexity")
    report_lines.append("")
    report_lines.append("## 1. Executive Summary")
    report_lines.append("")
    report_lines.append("This report analyzes the relationship between changes in EEG complexity (Lempel-Ziv Complexity and Permutation Entropy)")
    report_lines.append("and self-reported cognitive fatigue scores. The analysis distinguishes between adaptive simplification (reduced complexity)")
    report_lines.append("and degenerative noise (increased complexity) as potential mechanisms of fatigue.")
    report_lines.append("")
    
    # Statistical Significance Section
    report_lines.append("## 2. Statistical Significance")
    report_lines.append("")
    significant_results = correlations[correlations['p_value'] <= 0.05]
    report_lines.append(f"Out of {len(correlations)} tested electrode-metric pairs, {len(significant_results)} showed statistically significant correlations (p ≤ 0.05).")
    report_lines.append("")
    
    if len(significant_results) > 0:
        report_lines.append("### Significant Findings")
        report_lines.append("")
        report_lines.append("| Channel | Metric | Correlation (r) | p-value | Effect Size |")
        report_lines.append("|---|---|---|---|---|")
        for _, row in significant_results.iterrows():
            report_lines.append(f"| {row['channel']} | {row['metric_type']} | {row['correlation_coefficient']:.3f} | {row['p_value']:.4f} | {row['effect_size_category']} |")
        report_lines.append("")
    else:
        report_lines.append("No statistically significant correlations were found after Benjamini-Hochberg correction.")
        report_lines.append("")

    # Sensitivity Analysis Section
    report_lines.append("## 3. Sensitivity Analysis")
    report_lines.append("")
    report_lines.append("The analysis was tested at two significance thresholds (p ≤ 0.05 and p ≤ 0.01) to assess robustness.")
    report_lines.append("")
    report_lines.append(f"Threshold p≤0.05: {sensitivity[sensitivity['threshold'] == 0.05]['significant_count'].values[0] if len(sensitivity[sensitivity['threshold'] == 0.05]) > 0 else 0} significant results.")
    report_lines.append(f"Threshold p≤0.01: {sensitivity[sensitivity['threshold'] == 0.01]['significant_count'].values[0] if len(sensitivity[sensitivity['threshold'] == 0.01]) > 0 else 0} significant results.")
    report_lines.append("")

    # Interpretation: Adaptive vs Degenerative
    report_lines.append("## 4. Interpretation: Adaptive Simplification vs. Degenerative Noise")
    report_lines.append("")
    report_lines.append("The direction of the correlation coefficient provides insight into the underlying mechanism of fatigue:")
    report_lines.append("")
    report_lines.append("- **Adaptive Simplification**: A *negative* correlation (r < 0) between complexity and fatigue suggests that as fatigue increases, the brain's signal becomes more regular/ordered. This is consistent with a resource-conservation strategy where the system reduces search space.")
    report_lines.append("- **Degenerative Noise**: A *positive* correlation (r > 0) suggests that fatigue is associated with increased irregularity or 'noisiness' in the signal, potentially indicating a loss of signal integrity or chaotic dynamics.")
    report_lines.append("")
    
    # Analyze significant results for directionality
    adaptive_count = len(significant_results[significant_results['correlation_coefficient'] < 0])
    degenerative_count = len(significant_results[significant_results['correlation_coefficient'] > 0])
    
    report_lines.append(f"Among significant findings ({len(significant_results)}):")
    report_lines.append(f"- {adaptive_count} indicate **Adaptive Simplification** (negative correlation).")
    report_lines.append(f"- {degenerative_count} indicate **Degenerative Noise** (positive correlation).")
    report_lines.append("")

    # Limitations
    report_lines.append("## 5. Limitations")
    report_lines.append("")
    report_lines.append("- **Dataset Constraints**: Analysis relies on the Sleep-EDF dataset, which may not fully represent all fatigue states (e.g., acute vs. chronic).")
    report_lines.append("- **Signal-to-Noise Ratio**: Despite artifact rejection, residual noise may influence complexity metrics, particularly in high-frequency bands.")
    report_lines.append("- **Single Metric Proxy**: Lempel-Ziv Complexity and Permutation Entropy are proxies for system state; they do not capture the full topological complexity of neural dynamics.")
    report_lines.append("- **Cross-Sectional vs. Paired**: If paired data was insufficient, cross-sectional analysis limits causal inference regarding individual fatigue trajectories.")
    report_lines.append("")
    
    report_lines.append("---")
    report_lines.append(f"Report generated: {pd.Timestamp.now().isoformat()}")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Report successfully generated at: {output_path}")
    return output_path

def main():
    """Main entry point for report generation."""
    config = load_config()
    
    # Define paths relative to project root
    base_dir = Path(__file__).parent.parent
    analysis_results_path = base_dir / "data" / "analysis" / "correlation_results.csv"
    sensitivity_path = base_dir / "data" / "analysis" / "sensitivity_table.csv"
    output_path = base_dir / "data" / "analysis" / "final_report.md"
    
    generate_report(
        analysis_results_path=str(analysis_results_path),
        sensitivity_path=str(sensitivity_path),
        output_path=str(output_path)
    )

if __name__ == "__main__":
    main()