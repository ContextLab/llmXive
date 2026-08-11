"""
T031: Generate Final Report (US3)

Aggregates all metrics from previous phases into a comprehensive summary
stored at data/processed/final_report.md.

Inputs (expected from previous tasks):
  - data/processed/model_results.json (from T019/T022/T023)
  - data/processed/correlations.csv (from T025)
  - data/processed/robustness_report.csv (from T030)
  - data/processed/sensitivity_plot.png (from T030)
  - data/processed/verification_log.json (from T032, if available)
  - data/interim/joined_metadata.csv (from T008a, for N count)

Output:
  - data/processed/final_report.md
"""
import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs

def load_json_safe(filepath: str) -> dict:
    """Load JSON file safely, returning empty dict if missing."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Skipping.")
        return {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: {filepath} is not valid JSON. Skipping.")
        return {}

def load_csv_safe(filepath: str) -> pd.DataFrame:
    """Load CSV file safely, returning empty DataFrame if missing."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Skipping.")
        return pd.DataFrame()
    try:
        return pd.read_csv(filepath)
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return pd.DataFrame()

def load_metadata_count(filepath: str) -> int:
    """Get participant count from joined metadata."""
    if not os.path.exists(filepath):
        return 0
    try:
        df = pd.read_csv(filepath)
        # Assume 'participant_id' column exists
        if 'participant_id' in df.columns:
            return df['participant_id'].nunique()
        return len(df)
    except Exception:
        return 0

def format_number(val, decimals=3):
    """Format a number for display."""
    if val is None or (isinstance(val, float) and (val != val)):  # NaN check
        return "N/A"
    if isinstance(val, (int, float)):
        return f"{val:.{decimals}f}"
    return str(val)

def generate_report_content(model_results: dict, correlations: pd.DataFrame,
                            robustness: pd.DataFrame, sensitivity_plot_path: str,
                            verification_log: dict, n_participants: int) -> str:
    """Generate the Markdown content for the final report."""
    
    lines = []
    lines.append("# Final Report: Predicting Individual Differences in Sensory Processing Speed")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"This report aggregates results from the EEG-based prediction pipeline. "
                 f"Analysis was performed on **{n_participants}** participants after "
                 f"preprocessing and quality control.")
    lines.append("")
    
    # Key Metrics Section
    lines.append("## 2. Key Performance Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| :--- | :--- |")
    
    adj_r2 = model_results.get('adjusted_r2', model_results.get('linear_regression', {}).get('adjusted_r2'))
    if adj_r2 is None:
        adj_r2 = "N/A"
    else:
        adj_r2 = format_number(adj_r2)
        
    rmse = model_results.get('rmse', model_results.get('linear_regression', {}).get('rmse'))
    if rmse is None:
        rmse = "N/A"
    else:
        rmse = format_number(rmse)
        
    best_model = model_results.get('best_model', 'Linear Regression')
    if best_model == 'Linear Regression':
        best_r2 = model_results.get('adjusted_r2') or model_results.get('linear_regression', {}).get('adjusted_r2')
    else:
        best_r2 = model_results.get('lasso', {}).get('adjusted_r2')
        
    if best_r2 is None:
        best_r2 = "N/A"
    else:
        best_r2 = format_number(best_r2)
        
    lines.append(f"| Best Model | {best_model} |")
    lines.append(f"| Adjusted R² | {best_r2} |")
    lines.append(f"| RMSE | {rmse} |")
    
    # Significance
    lines.append("")
    lines.append("## 3. Statistical Significance")
    lines.append("")
    
    # Check Bonferroni results in correlations if available
    significant_bands = []
    if not correlations.empty and 'bonferroni_sig' in correlations.columns:
        sig_rows = correlations[correlations['bonferroni_sig'] == True]
        if not sig_rows.empty:
            significant_bands = list(sig_rows['band'].astype(str).unique())
    
    if significant_bands:
        lines.append(f"Significant correlations (Bonferroni-corrected p < 0.0083) found in: "
                     f"{', '.join(significant_bands)} bands.")
    else:
        lines.append("No significant correlations found after Bonferroni correction.")
    lines.append("")
    
    # Permutation Test
    perm_p_val = model_results.get('permutation_p_value')
    if perm_p_val is not None:
        lines.append(f"Permutation test p-value: {format_number(perm_p_val)}")
        if perm_p_val < 0.05:
            lines.append("*Conclusion:* The model's predictive power is significantly better than chance.")
        else:
            lines.append("*Conclusion:* The model's predictive power is not significantly better than chance.")
    lines.append("")
    
    # Power Analysis
    lines.append("## 4. Power Analysis")
    lines.append("")
    power_analysis = model_results.get('power_analysis', {})
    required_n = power_analysis.get('required_n_for_r2_010', "N/A")
    current_n = n_participants
    lines.append(f"| Target R² | 0.10 |")
    lines.append(f"| Current N | {current_n} |")
    lines.append(f"| Required N (Power ≥ 0.80) | {required_n} |")
    lines.append("")
    
    # Robustness
    lines.append("## 5. Robustness Analysis")
    lines.append("")
    if not robustness.empty:
        lines.append("The model was re-run with alternative parameters (no ICA, 2s windows).")
        lines.append("")
        lines.append("| Configuration | R² | % Difference |")
        lines.append("| :--- | :--- | :--- |")
        
        # Assume robustness df has columns: config, r2, alpha_diff
        for _, row in robustness.iterrows():
            config = row.get('config', 'Unknown')
            r2 = row.get('r2', 0)
            diff = row.get('alpha_diff_pct', 0)
            lines.append(f"| {config} | {format_number(r2)} | {format_number(diff, 2)}% |")
    else:
        lines.append("Robustness analysis data not available.")
    lines.append("")
    
    # Sensitivity
    lines.append("## 6. Sensitivity Analysis")
    lines.append("")
    lines.append(f"![Sensitivity Plot]({sensitivity_plot_path})")
    lines.append("")
    lines.append("*Figure 1: Number of significant correlations across p-value thresholds.*")
    lines.append("")
    
    # Verification
    lines.append("## 7. Execution Verification")
    lines.append("")
    if verification_log:
        runtime = verification_log.get('total_duration_seconds', 'N/A')
        max_ram = verification_log.get('max_ram_gb', 'N/A')
        status = verification_log.get('status', 'Unknown')
        lines.append(f"| Metric | Value | Pass? |")
        lines.append(f"| :--- | :--- | :--- |")
        lines.append(f"| Runtime | {runtime} s | {'Yes' if isinstance(runtime, (int, float)) and runtime < 21600 else 'No'} |")
        lines.append(f"| Max RAM | {max_ram} GB | {'Yes' if isinstance(max_ram, (int, float)) and max_ram < 7 else 'No'} |")
        lines.append(f"| Overall Status | {status} | {'Yes' if status == 'PASS' else 'No'} |")
    else:
        lines.append("Verification logs not available.")
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("*End of Report*")
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Generate final aggregated report.")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path for final_report.md")
    args = parser.parse_args()

    # Define paths
    base_dir = Path(__file__).parent.parent
    model_results_path = get_path(base_dir, "data/processed/model_results.json")
    correlations_path = get_path(base_dir, "data/processed/correlations.csv")
    robustness_path = get_path(base_dir, "data/processed/robustness_report.csv")
    sensitivity_plot_path = get_path(base_dir, "data/processed/sensitivity_plot.png")
    verification_path = get_path(base_dir, "data/processed/verification_log.json")
    metadata_path = get_path(base_dir, "data/interim/joined_metadata.csv")
    
    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path(base_dir, "data/processed/final_report.md")
    
    ensure_dirs(output_path.parent)

    # Load data
    model_results = load_json_safe(model_results_path)
    correlations = load_csv_safe(correlations_path)
    robustness = load_csv_safe(robustness_path)
    verification_log = load_json_safe(verification_path)
    n_participants = load_metadata_count(metadata_path)

    # Check if sensitivity plot exists, fallback to path string
    sens_plot_str = str(sensitivity_plot_path.relative_to(base_dir))
    if not sensitivity_plot_path.exists():
        print("Warning: Sensitivity plot not found. Report will reference missing file.")

    # Generate content
    content = generate_report_content(
        model_results,
        correlations,
        robustness,
        sens_plot_str,
        verification_log,
        n_participants
    )

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Final report generated: {output_path}")

if __name__ == "__main__":
    main()
