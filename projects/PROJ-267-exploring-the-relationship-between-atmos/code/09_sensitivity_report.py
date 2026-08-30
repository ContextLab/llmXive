import re
import pandas as pd
import os
import numpy as np
import sys

def calculate_stability_metrics(df, thresholds):
    """
    Calculate stability metrics for different correlation thresholds.
    
    Args:
        df: DataFrame with correlation results
        thresholds: List of threshold values to sweep
        
    Returns:
        Dictionary of metrics per threshold
    """
    results = {}
    
    for t in thresholds:
        # Filter results above threshold
        subset = df[df['correlation_coefficient'] > t]
        
        # Stability: variance of correlation coefficients
        if len(subset) > 1:
            stability = np.var(subset['correlation_coefficient'])
        else:
            stability = 0.0
        
        # CI Overlap: check overlap with mean CI
        if len(df) > 0 and 'confidence_interval_lower' in df.columns and 'confidence_interval_upper' in df.columns:
            mean_ci_lower = df['confidence_interval_lower'].mean()
            mean_ci_upper = df['confidence_interval_upper'].mean()
            
            overlaps = 0
            for _, row in df.iterrows():
                if (row['confidence_interval_lower'] <= mean_ci_upper and 
                    row['confidence_interval_upper'] >= mean_ci_lower):
                    overlaps += 1
            overlap_ratio = overlaps / len(df)
        else:
            overlap_ratio = 0.0
        
        results[t] = {
            'count': len(subset),
            'stability': stability,
            'overlap_ratio': overlap_ratio
        }
    
    return results

def generate_report(results, output_path):
    """
    Generate the sensitivity analysis report.
    
    Args:
        results: Dictionary of stability metrics per threshold
        output_path: Path to write the report
    """
    report_content = "# Sensitivity Analysis Report\n\n"
    report_content += "## Overview\n\n"
    report_content += "This report evaluates the stability of correlation results across different significance thresholds. "
    report_content += "The analysis focuses on the variance of correlation coefficients and confidence interval overlap ratios.\n\n"
    
    report_content += "## Threshold Sweep Results\n\n"
    report_content += "| Threshold | Count (> Threshold) | Stability (Variance) | CI Overlap Ratio |\n"
    report_content += "| :--- | :--- | :--- | :--- |\n"
    
    for t, data in sorted(results.items()):
        report_content += f"| {t:.2f} | {data['count']} | {data['stability']:.6f} | {data['overlap_ratio']:.2f} |\n"
    
    report_content += "\n## Interpretation\n\n"
    report_content += "Lower stability values indicate more consistent correlation coefficients across the selected subset. "
    report_content += "Higher CI overlap ratios suggest that the confidence intervals are concentrated around a central value.\n\n"
    
    report_content += "## Frame of Reference and Limitations\n\n"
    report_content += "The correlation results presented in this report are based on the perturbation in gravitational potential "
    report_content += "at the GRACE-FO satellite altitude, not the geoid height at the Earth's surface. This is a "
    report_content += "coordinate-dependent quantity derived from spherical harmonic coefficients in the satellite's reference frame.\n\n"
    report_content += "It is important to note that \"static\" anomalies in this context are coordinate artifacts within a dynamic "
    report_content += "gravitational field. The analysis assumes a static, non-rotating frame for the duration of the monthly "
    report_content += "aggregation. All findings are framed strictly as associational, and no causal inferences are drawn.\n\n"
    
    report_content += "## Methodological Notes\n\n"
    report_content += "The threshold sweep was performed to assess the robustness of the observed associations. "
    report_content += "The stability metric (variance) and CI overlap ratio provide continuous measures of result consistency "
    report_content += "without relying on pre-specified binary significance thresholds.\n"
    
    # Final safety check for causal language
    causal_keywords = r'causes|effect|impact|driven by|leads to|triggers|causal'
    if re.search(causal_keywords, report_content, re.IGNORECASE):
        raise ValueError(f"Causal language detected in report! Violates FR-007. Content: {report_content[:200]}...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    print(f"Generated sensitivity report: {output_path}")

def main():
    """Main entry point for the sensitivity analysis script."""
    input_path = 'data/processed/correlation_results.csv'
    output_path = 'output/sensitivity_report.md'
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        print("Please run the correlation analysis (T020) first to generate correlation_results.csv.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Define thresholds for sweep (including 0.5 and 0.6 as representative values)
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
    
    # Filter out rows with NaN in correlation_coefficient if present
    if 'correlation_coefficient' in df.columns:
        df = df.dropna(subset=['correlation_coefficient'])
    
    if len(df) == 0:
        print("Warning: No valid data rows found after cleaning. Generating empty report.")
        # Still generate a report to indicate the state
        results = {t: {'count': 0, 'stability': 0.0, 'overlap_ratio': 0.0} for t in thresholds}
    else:
        results = calculate_stability_metrics(df, thresholds)
    
    generate_report(results, output_path)
    print("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()
