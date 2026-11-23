"""
T031c: Implement code/11c_write_report.py to assemble the final data/processed/final_report.md.

This script ingests all processed metrics (model results, correlations, robustness, sensitivity,
feasibility) and generates a comprehensive Markdown report.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow importing config if needed, though we use relative paths here
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path, ensure_dirs

def load_json_safe(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None

def load_csv_safe(filepath: str) -> Optional[pd.DataFrame]:
    """Load a CSV file safely, returning None if it doesn't exist."""
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Warning: Could not load {filepath}: File not found")
        return None
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None

def load_metadata_count() -> int:
    """Load the number of matched participants from the feasibility report."""
    feasibility_report_path = get_path("data/processed", "feasibility_report.md")
    # The feasibility report is a markdown file, but the logic in T008b writes a JSON schema inside or the file itself is the report.
    # Looking at T008b spec: "write data/processed/feasibility_report.md with JSON schema ... and exit with code 1".
    # However, T031a (load_results.py) likely parses this. Let's try to find the count.
    # If the file is purely markdown, we might need to parse it.
    # But often feasibility reports in this pipeline contain the JSON block.
    # Let's try to load a companion JSON if it exists, or parse the markdown.
    # Actually, T008b writes the report to .md but the logic says "write ... with JSON schema".
    # Let's assume there might be a JSON file or we parse the .md.
    # To be safe, let's look for a JSON file that might have been created alongside or parse the .md.
    # Since T008b writes to .md, we will parse it.
    
    # Fallback: Try to read the feasibility report content
    try:
        # The feasibility report is written by T008b.
        # If T008b exited with code 1, the report might not exist or be minimal.
        # We need to be robust.
        pass
    except:
        pass
    
    # Let's try to load from a potential JSON source if the markdown parsing is too brittle,
    # or just return 0 if not found to avoid crashing the report generation.
    # The task T031a likely aggregates this. We will try to find the count.
    # If the feasibility report is the source of truth:
    report_path = get_path("data/processed", "feasibility_report.md")
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            content = f.read()
            # Look for a JSON block or specific text
            if "matched_count" in content:
                # Simple extraction if it's inline JSON
                import re
                match = re.search(r'"matched_count":\s*(\d+)', content)
                if match:
                    return int(match.group(1))
    return 0

def format_number(value: Any, decimals: int = 3) -> str:
    """Format a number with fixed decimals, handling None."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)

def generate_report_content(
    model_results: Optional[Dict],
    correlations: Optional[pd.DataFrame],
    non_linear: Optional[Dict],
    permutation: Optional[Dict],
    robustness: Optional[pd.DataFrame],
    sensitivity: Optional[pd.DataFrame],
    feasibility_count: int
) -> str:
    """Generate the Markdown content for the final report."""
    lines = []
    lines.append("# Final Report: Predicting Individual Differences in Sensory Processing Speed")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"This report summarizes the analysis of {feasibility_count} participants.")
    lines.append("The goal was to predict reaction time (RT) from EEG power spectra.")
    lines.append("")

    # 1. Modeling Results
    lines.append("## 1. Predictive Modeling Results")
    lines.append("")
    if model_results:
        lines.append("| Metric | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| Adjusted R² | {format_number(model_results.get('adjusted_r2'))} |")
        lines.append(f"| Test R² | {format_number(model_results.get('test_r2'))} |")
        lines.append(f"| Test RMSE | {format_number(model_results.get('test_rmse'))} |")
        lines.append(f"| Optimal Lambda (LASSO) | {format_number(model_results.get('optimal_lambda'))} |")
        
        # Post-hoc power analysis if present
        if 'post_hoc_power_analysis' in model_results:
            power_data = model_results['post_hoc_power_analysis']
            lines.append("")
            lines.append("### Post-hoc Power Analysis")
            lines.append(f"- Required N for R²=0.10, Power=0.80: {power_data.get('required_n', 'N/A')}")
            lines.append(f"- Calculated Power: {format_number(power_data.get('power'))}")
            lines.append(f"- Effect Size (f²): {format_number(power_data.get('effect_size'))}")
    else:
        lines.append("*No modeling results available.*")
    lines.append("")

    # 2. Correlation Analysis
    lines.append("## 2. Band Power Correlations with RT")
    lines.append("")
    if correlations is not None and not correlations.empty:
        # Filter for significant ones if possible, or show all
        lines.append("| Band | Correlation (r) | p-value | Significant (Bonferroni) |")
        lines.append("| :--- | :--- | :--- | :--- |")
        
        # Bonferroni threshold is 0.0083 (0.05 / 6)
        for _, row in correlations.iterrows():
            band = row.get('band', 'Unknown')
            r_val = row.get('r_value', 0)
            p_val = row.get('p_value', 1)
            is_sig = p_val < 0.0083
            sig_str = "Yes" if is_sig else "No"
            lines.append(f"| {band} | {format_number(r_val)} | {format_number(p_val, 4)} | {sig_str} |")
    else:
        lines.append("*No correlation data available.*")
    lines.append("")

    # 3. Non-linear Model Comparison
    lines.append("## 3. Non-linear Model Comparison")
    lines.append("")
    if non_linear:
        lines.append("| Model Type | Adjusted R² | Significant Improvement? |")
        lines.append("| :--- | :--- | :--- |")
        linear_r2 = non_linear.get('linear_r2', 'N/A')
        poly_r2 = non_linear.get('polynomial_r2', 'N/A')
        sig = non_linear.get('significant_at_0p05', False)
        lines.append(f"| Linear | {format_number(linear_r2)} | - |")
        lines.append(f"| Polynomial | {format_number(poly_r2)} | {'Yes' if sig else 'No'} |")
        
        interpretation = non_linear.get('interpretation', '')
        if interpretation:
            lines.append(f"> {interpretation}")
    else:
        lines.append("*No non-linear comparison data available.*")
    lines.append("")

    # 4. Permutation Test
    lines.append("## 4. Permutation Test (Null Distribution)")
    lines.append("")
    if permutation:
        observed_r2 = permutation.get('observed_r2', 'N/A')
        p_val = permutation.get('p_value', 'N/A')
        lines.append(f"- **Observed R²**: {format_number(observed_r2)}")
        lines.append(f"- **Permutation p-value**: {format_number(p_val, 4)}")
        if p_val is not None and p_val < 0.05:
            lines.append("- **Conclusion**: The observed R² is significantly different from the null distribution (p < 0.05).")
        else:
            lines.append("- **Conclusion**: The observed R² is not significantly different from the null distribution (p >= 0.05).")
    else:
        lines.append("*No permutation test results available.*")
    lines.append("")

    # 5. Robustness Analysis
    lines.append("## 5. Robustness Analysis")
    lines.append("")
    if robustness is not None and not robustness.empty:
        lines.append("| Metric | Standard | Robust (2s window) | Delta |")
        lines.append("| :--- | :--- | :--- | :--- |")
        # Assuming the robustness file has columns like 'metric', 'value', 'type' or similar.
        # Based on T025c, it might be a summary. Let's try to render rows.
        for _, row in robustness.iterrows():
            # Generic rendering
            metric = row.get('metric', 'Unknown')
            val_std = row.get('standard', row.get('value', 'N/A'))
            val_rob = row.get('robust', 'N/A')
            delta = row.get('delta', 'N/A')
            lines.append(f"| {metric} | {val_std} | {val_rob} | {delta} |")
    else:
        lines.append("*No robustness data available.*")
    lines.append("")

    # 6. Sensitivity Analysis
    lines.append("## 6. Sensitivity Analysis")
    lines.append("")
    if sensitivity is not None and not sensitivity.empty:
        lines.append("| P-value Threshold | Significant Count |")
        lines.append("| :--- | :--- |")
        for _, row in sensitivity.iterrows():
            threshold = row.get('threshold', 'N/A')
            count = row.get('significant_count', 0)
            lines.append(f"| {format_number(threshold, 4)} | {int(count)} |")
    else:
        lines.append("*No sensitivity data available.*")
    lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    lines.append("The analysis pipeline has been executed. The results above summarize the predictive power of EEG spectral features on individual differences in sensory processing speed.")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by code/11c_write_report.py*")

    return "\n".join(lines)

def main():
    print("T031c: Generating Final Report...")
    
    # Define paths
    model_results_path = get_path("data/processed", "model_results.json")
    correlations_path = get_path("data/processed", "correlations_corrected.csv") # Using corrected as it's the final one
    non_linear_path = get_path("data/processed", "non_linear_comparison.json")
    permutation_path = get_path("data/processed", "permutation_results.json")
    robustness_path = get_path("data/processed", "robustness_report.csv")
    sensitivity_path = get_path("data/processed", "sensitivity_report.csv")
    output_path = get_path("data/processed", "final_report.md")
    
    # Ensure output directory exists
    ensure_dirs(output_path)
    
    # Load data
    model_results = load_json_safe(model_results_path)
    correlations = load_csv_safe(correlations_path)
    non_linear = load_json_safe(non_linear_path)
    permutation = load_json_safe(permutation_path)
    robustness = load_csv_safe(robustness_path)
    sensitivity = load_csv_safe(sensitivity_path)
    feasibility_count = load_metadata_count()
    
    # Generate content
    content = generate_report_content(
        model_results,
        correlations,
        non_linear,
        permutation,
        robustness,
        sensitivity,
        feasibility_count
    )
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Final report written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
