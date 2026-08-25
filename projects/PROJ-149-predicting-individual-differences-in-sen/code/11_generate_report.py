"""
T031: Generate Final Report
Compiles all metrics (adjusted R², Bonferroni-corrected p-values, robustness deltas,
sensitivity thresholds, feasibility logs) into data/processed/final_report.md.
"""
import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import shared config utilities
# We use a robust get_path that handles various call signatures as per contract
from config import get_path, ensure_dirs, get_band_freqs, get_all_band_names

def load_json_safe(path: str) -> dict:
    """Load a JSON file, returning empty dict if missing or invalid."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def load_csv_safe(path: str) -> pd.DataFrame:
    """Load a CSV file, returning empty DataFrame if missing."""
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def load_metadata_count(path: str) -> int:
    """Load participant count from joined metadata or manifest."""
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return len(df)
        except Exception:
            pass
    return 0

def format_number(val, decimals=4):
    """Format a number safely."""
    if val is None or (isinstance(val, float) and (val != val)): # check NaN
        return "N/A"
    return f"{val:.{decimals}f}"

def generate_report_content():
    """Generate the content of the final report as a string."""
    
    # --- 1. Load Data Sources ---
    # Model Results
    model_results_path = get_path("data/processed/model_results.json")
    model_results = load_json_safe(model_results_path)
    
    # Correlations (Corrected)
    corr_path = get_path("data/processed/correlations_corrected.csv")
    # Fallback to raw if corrected missing, but task T021 says corrected exists
    if corr_path and not os.path.exists(corr_path):
        # Try raw path as fallback for robustness in report gen
        corr_path = get_path("data/interim/correlations_raw.csv")
        if not os.path.exists(corr_path):
            corr_path = None
    
    corr_df = load_csv_safe(corr_path) if corr_path else pd.DataFrame()
    
    # Robustness Report
    robust_path = get_path("data/processed/robustness_report.csv")
    robust_df = load_csv_safe(robust_path)
    
    # Sensitivity Report
    sens_path = get_path("data/processed/sensitivity_report.csv")
    sens_df = load_csv_safe(sens_path)
    
    # Feasibility / Join Logs
    join_log_path = get_path("data/interim/feasibility_exclusion_log.csv")
    join_log_df = load_csv_safe(join_log_path)
    
    exclusion_log_path = get_path("data/interim/exclusion_log.csv")
    exclusion_df = load_csv_safe(exclusion_log_path)
    
    behavioral_exclusion_path = get_path("data/interim/behavioral_exclusion_log.csv")
    behavioral_exclusion_df = load_csv_safe(behavioral_exclusion_path)

    # --- 2. Extract Key Metrics ---
    adj_r2 = model_results.get('adjusted_r2', 'N/A')
    test_r2 = model_results.get('test_r2', 'N/A')
    optimal_lambda = model_results.get('optimal_lambda', 'N/A')
    rmse = model_results.get('rmse', 'N/A')
    test_rmse = model_results.get('test_rmse', 'N/A')
    
    # Post-hoc power analysis (from T023)
    power_analysis = model_results.get('post_hoc_power_analysis', {})
    required_n = power_analysis.get('required_n', 'N/A')
    power = power_analysis.get('power', 'N/A')
    effect_size = power_analysis.get('effect_size', 'N/A')

    # Bonferroni Threshold
    # From config or hardcode if missing (0.05 / 6 bands)
    bonf_thresh = 0.008333
    
    # Significant Bands
    significant_bands = []
    if not corr_df.empty:
        # Check for 'significant' column or compute from p_value
        if 'significant' in corr_df.columns:
            sig_rows = corr_df[corr_df['significant'] == True]
            significant_bands = sig_rows['band'].tolist()
        elif 'p_value' in corr_df.columns:
            sig_rows = corr_df[corr_df['p_value'] < bonf_thresh]
            significant_bands = sig_rows['band'].tolist()

    # Robustness Summary
    robust_summary = []
    if not robust_df.empty:
        for _, row in robust_df.iterrows():
            condition = row.get('condition', 'unknown')
            r2 = row.get('r2', 'N/A')
            delta = row.get('delta_r2', 'N/A')
            robust_summary.append(f"- **{condition}**: R²={format_number(r2)}, Δ={format_number(delta)}")

    # Sensitivity Summary
    sens_summary = []
    if not sens_df.empty:
        # Find critical threshold (where count drops)
        # Simple heuristic: first threshold where count < max_count
        max_count = sens_df['significant_count'].max() if not sens_df.empty else 0
        critical = "N/A"
        if not sens_df.empty:
            for _, row in sens_df.iterrows():
                if row['significant_count'] < max_count and max_count > 0:
                    critical = row['threshold']
                    break
        sens_summary.append(f"- Critical p-threshold: {critical}")

    # Participant Counts
    total_participants = load_metadata_count(get_path("data/interim/joined_metadata.csv"))
    excluded_eeg = len(exclusion_df) if not exclusion_df.empty else 0
    excluded_behavioral = len(behavioral_exclusion_df) if not behavioral_exclusion_df.empty else 0
    excluded_join = len(join_log_df) if not join_log_df.empty else 0

    # --- 3. Construct Markdown ---
    report = []
    report.append("# Final Report: Predicting Individual Differences in Sensory Processing Speed")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## 1. Executive Summary")
    report.append(f"This report summarizes the analysis of the PhysioNet EEG Motor Movement/Imagery dataset.")
    report.append(f"Total participants processed: {total_participants}.")
    report.append(f"Exclusions: {excluded_join} (join), {excluded_eeg} (EEG preprocessing), {excluded_behavioral} (behavioral).")
    report.append("")
    
    report.append("## 2. Predictive Modeling Results")
    report.append("The study employed Multiple Linear Regression and LASSO to predict median Reaction Time (RT) from EEG band power features (CLR transformed).")
    report.append("")
    report.append("### Key Metrics")
    report.append("| Metric | Value |")
    report.append("| :--- | :--- |")
    report.append(f"| Adjusted R² | {format_number(adj_r2)} |")
    report.append(f"| Test R² | {format_number(test_r2)} |")
    report.append(f"| RMSE (Train) | {format_number(rmse)} |")
    report.append(f"| RMSE (Test) | {format_number(test_rmse)} |")
    report.append(f"| Optimal Lambda (LASSO) | {format_number(optimal_lambda)} |")
    report.append("")
    
    if power_analysis:
        report.append("### Post-Hoc Power Analysis")
        report.append(f"- **Effect Size (f²)**: {format_number(effect_size)}")
        report.append(f"- **Required N for 80% Power**: {required_n}")
        report.append(f"- **Achieved Power**: {format_number(power)}")
        report.append("")

    report.append("## 3. Feature Correlations (Bonferroni Corrected)")
    report.append(f"Significance threshold (α): {bonf_thresh} (0.05 / 6 bands).")
    report.append("")
    if not corr_df.empty:
        report.append("| Band | r-value | p-value | Significant? |")
        report.append("| :--- | :--- | :--- | :--- |")
        for _, row in corr_df.iterrows():
            band = row.get('band', 'unknown')
            r_val = format_number(row.get('r_value', 0))
            p_val = format_number(row.get('p_value', 1))
            sig = "Yes" if band in significant_bands else "No"
            report.append(f"| {band} | {r_val} | {p_val} | {sig} |")
    else:
        report.append("*No correlation data available.*")
    report.append("")

    report.append("## 4. Robustness Analysis")
    report.append("The pipeline was re-run with alternative preprocessing parameters (no ICA, different window sizes) to assess stability.")
    report.append("")
    if robust_summary:
        report.extend(robust_summary)
    else:
        report.append("*No robustness data available.*")
    report.append("")

    report.append("## 5. Sensitivity Analysis")
    report.append("Analysis of the number of significant correlations across varying p-value thresholds.")
    report.append("")
    if sens_summary:
        report.extend(sens_summary)
    else:
        report.append("*No sensitivity data available.*")
    report.append("")

    report.append("## 6. Data Quality & Exclusions")
    report.append("### Exclusion Logs")
    if not exclusion_df.empty:
        report.append("**EEG Preprocessing Exclusions:**")
        report.append("| Participant ID | Reason | Channels Rejected Ratio |")
        report.append("| :--- | :--- | :--- |")
        for _, row in exclusion_df.iterrows():
            report.append(f"| {row.get('participant_id', 'N/A')} | {row.get('reason', 'N/A')} | {row.get('channels_rejected_ratio', 'N/A')} |")
    else:
        report.append("*No EEG exclusions recorded.*")
    report.append("")

    if not behavioral_exclusion_df.empty:
        report.append("**Behavioral Data Exclusions:**")
        report.append("| Participant ID | Reason |")
        report.append("| :--- | :--- |")
        for _, row in behavioral_exclusion_df.iterrows():
            report.append(f"| {row.get('participant_id', 'N/A')} | {row.get('reason', 'N/A')} |")
    else:
        report.append("*No behavioral exclusions recorded.*")
    report.append("")

    report.append("## 7. Conclusion")
    report.append(f"The analysis {'successfully identified' if significant_bands else 'did not identify'} significant associations between EEG band power and sensory processing speed (RT) after Bonferroni correction.")
    report.append(f"The predictive model achieved an Adjusted R² of {format_number(adj_r2)}, indicating {'moderate' if adj_r2 and adj_r2 > 0.2 else 'low'} explanatory power.")
    report.append("")
    report.append("---")
    report.append("*End of Report*")

    return "\n".join(report)

def main():
    print("Generating Final Report (T031)...")
    
    # Ensure output directory exists
    output_path = get_path("data/processed/final_report.md")
    # Ensure the directory of the output path exists
    ensure_dirs(Path(output_path).parent)
    
    content = generate_report_content()
    
    with open(output_path, 'w') as f:
        f.write(content)
        
    print(f"Report written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
