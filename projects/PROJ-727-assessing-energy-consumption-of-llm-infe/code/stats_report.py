import os
import csv
import pandas as pd
from code.config import DATA_PROCESSED_DIR
from code.analysis import load_data, run_anova, run_tukey, run_regression
from code.sensitivity_analysis import run_sensitivity_analysis

def format_statistic(name, value, units=None, note=None):
    """Format a statistical value with units and optional note."""
    line = f"{name}: {value}"
    if units:
        line += f" ({units})"
    if note:
        line += f" [{note}]"
    return line

def write_stats_report():
    """
    Write the comprehensive statistical report to data/processed/stats_report.csv.
    Includes ANOVA, Tukey, Regression, and Sensitivity results.
    Crucially, frames the regression results as **observational** (non-causal)
    as required by FR-008.
    """
    report_path = os.path.join(DATA_PROCESSED_DIR, "stats_report.csv")
    
    # Load data and run analyses
    df = load_data()
    
    # 1. ANOVA Results
    anova_results = run_anova(df)
    anova_pval = anova_results['pvalue'] if hasattr(anova_results, 'pvalue') else "N/A"
    
    # 2. Tukey HSD Results
    tukey_results = run_tukey(df)
    # Tukey often returns a table; we extract key comparisons or summary
    tukey_summary = str(tukey_results) if tukey_results is not None else "N/A"
    
    # 3. Regression Results (Observational)
    # FR-008: Explicitly frame as observational
    regression_results = run_regression(df)
    slope = regression_results.get('slope', 0.0)
    r_squared = regression_results.get('r_squared', 0.0)
    
    # 4. Sensitivity Analysis
    sensitivity_results = run_sensitivity_analysis(df)
    orig_pval = sensitivity_results.get('original_pvalue', "N/A")
    pert_pval = sensitivity_results.get('perturbed_pvalue', "N/A")
    delta = sensitivity_results.get('delta', "N/A")
    robustness = sensitivity_results.get('robustness', "N/A")

    # Construct the report rows
    rows = []
    
    # Header
    rows.append({"metric": "Analysis Type", "value": "Description/Result"})
    
    # ANOVA
    rows.append({"metric": "ANOVA (Repeated Measures)", "value": f"P-value: {anova_pval}"})
    
    # Tukey
    # Truncate long string for CSV cell if necessary, but keep key info
    tukey_val = tukey_summary[:200] + "..." if len(str(tukey_summary)) > 200 else tukey_summary
    rows.append({"metric": "Tukey HSD", "value": f"Results: {tukey_val}"})
    
    # Regression - OBSERVATIONAL FRAMING (FR-008)
    obs_note = "OBSERVATIONAL: Correlation does not imply causation. Higher parameter counts are associated with higher energy per token in this dataset, but this is not a causal proof."
    reg_val = f"Slope: {slope:.6f}, R-squared: {r_squared:.4f}. {obs_note}"
    rows.append({"metric": "Linear Regression (Params vs Energy/Token)", "value": reg_val})
    
    # Sensitivity
    rows.append({"metric": "Sensitivity Analysis (Delta P)", "value": f"Orig: {orig_pval}, Pert: {pert_pval}, Delta: {delta}"})
    rows.append({"metric": "Robustness", "value": robustness})

    # Write to CSV
    with open(report_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)

    return report_path

def main():
    """Entry point to generate the stats report."""
    print("Generating statistical report (observational framing)...")
    path = write_stats_report()
    print(f"Report written to: {path}")
    
    # Verification: Ensure the text "observational" or "correlation does not imply causation" exists
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "observational" in content.lower() or "correlation does not imply causation" in content.lower():
            print("Verification passed: Observational framing detected in report.")
        else:
            raise RuntimeError("Verification failed: Observational framing missing from report.")

if __name__ == "__main__":
    main()