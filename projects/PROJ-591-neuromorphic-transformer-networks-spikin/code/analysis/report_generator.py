import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

# Import from existing API surface
from analysis.statistical_tests import load_metrics_data, prepare_paired_data, run_paired_ttest, apply_bonferroni_correction
from analysis.sensitivity_analysis import run_sensitivity_sweep

def load_temporal_metrics() -> Optional[pd.DataFrame]:
    """
    Load temporal coding metrics from the spiking model results.
    Attempts to parse the 'temporal_coding_metrics' JSON column if present,
    or loads from a dedicated file if available.
    """
    csv_path = "data/processed/spiking_metrics.csv"
    if not os.path.exists(csv_path):
        return None

    df = pd.read_csv(csv_path)
    
    # If the column exists and contains JSON strings
    if 'temporal_coding_metrics' in df.columns:
        metrics_list = []
        for _, row in df.iterrows():
            try:
                if pd.notna(row['temporal_coding_metrics']):
                  metrics = json.loads(row['temporal_coding_metrics'])
                  metrics['seed'] = row['seed']
                  metrics_list.append(metrics)
            except (json.JSONDecodeError, TypeError):
                continue
        
        if metrics_list:
            return pd.DataFrame(metrics_list)
    
    # Fallback: check for a dedicated temporal metrics file
    temp_path = "data/processed/temporal_coding_metrics.csv"
    if os.path.exists(temp_path):
        return pd.read_csv(temp_path)
        
    return None

def generate_report(
    baseline_df: pd.DataFrame,
    spiking_df: pd.DataFrame,
    ttest_results: Dict[str, Any],
    sensitivity_results: pd.DataFrame,
    temporal_metrics: Optional[pd.DataFrame],
    output_path: str
) -> None:
    """
    Generates the markdown comparison report including statistical analysis
    and temporal coding comparisons.
    """
    report_lines = []
    
    # Header
    report_lines.append("# Statistical Analysis Report: Baseline vs. Spiking Transformer")
    report_lines.append("")
    report_lines.append("## 1. Executive Summary")
    report_lines.append("")
    report_lines.append("This report compares the performance and energy efficiency of a standard Transformer baseline")
    report_lines.append("against a Neuromorphic Spiking Transformer using paired t-tests and sensitivity analysis.")
    report_lines.append("")
    
    # 2. Statistical Analysis
    report_lines.append("## 2. Statistical Analysis (Paired t-tests)")
    report_lines.append("")
    report_lines.append("### 2.1 Methodology")
    report_lines.append("- **Test Type**: Paired t-test (matching random seeds for Baseline and Spiking models)")
    report_lines.append("- **Correction**: Bonferroni/Holm-Bonferroni applied for multiple comparisons (Perplexity, Energy)")
    report_lines.append("- **Significance Level**: $\alpha = 0.05$")
    report_lines.append("")
    
    report_lines.append("### 2.2 Results")
    report_lines.append("")
    report_lines.append("| Metric | t-statistic | p-value (raw) | p-value (corrected) | Significant? |")
    report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for metric_name, result in ttest_results.items():
        stat = result.get('t_statistic', 0.0)
        p_raw = result.get('p_value', 1.0)
        p_corr = result.get('p_corrected', 1.0)
        sig = "Yes" if p_corr < 0.05 else "No"
        report_lines.append(f"| {metric_name} | {stat:.4f} | {p_raw:.4e} | {p_corr:.4e} | {sig} |")
    
    report_lines.append("")
    
    # 3. Sensitivity Analysis
    report_lines.append("## 3. Sensitivity Analysis")
    report_lines.append("")
    report_lines.append("Analysis of performance across energy reduction thresholds {0.20, 0.25, 0.30, 0.35}.")
    report_lines.append("Ground truth assumed: $\ge 30\%$ energy reduction.")
    report_lines.append("")
    
    if not sensitivity_results.empty:
        report_lines.append("| Threshold | True Positives | False Positives | True Negatives | False Negatives |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for _, row in sensitivity_results.iterrows():
            report_lines.append(
                f"| {row['threshold']:.2f} | {row.get('tp', 0)} | {row.get('fp', 0)} | {row.get('tn', 0)} | {row.get('fn', 0)} |"
            )
    else:
        report_lines.append("*Sensitivity analysis results not available.*")
    
    report_lines.append("")
    
    # 4. Temporal Coding Comparison
    report_lines.append("## 4. Temporal Coding Characteristics")
    report_lines.append("")
    
    if temporal_metrics is not None and not temporal_metrics.empty:
        report_lines.append("### 4.1 Spike Train Statistics")
        report_lines.append("")
        
        # Aggregate stats
        avg_isi = temporal_metrics.get('isi_variance', temporal_metrics.get('isi_variance_mean', 0.0)).mean()
        avg_bits = temporal_metrics.get('bits_per_spike', temporal_metrics.get('bits_per_spike_mean', 0.0)).mean()
        avg_sync = temporal_metrics.get('synchrony', temporal_metrics.get('synchrony_mean', 0.0)).mean()
        
        report_lines.append(f"- **Mean ISI Variance**: {avg_isi:.6f}")
        report_lines.append(f"- **Mean Bits per Spike**: {avg_bits:.4f}")
        report_lines.append(f"- **Mean Spike Train Synchrony**: {avg_sync:.4f}")
        report_lines.append("")
        
        report_lines.append("### 4.2 Per-Seed Breakdown")
        report_lines.append("")
        report_lines.append("| Seed | ISI Variance | Bits/Spike | Synchrony |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        
        for _, row in temporal_metrics.iterrows():
            isi = row.get('isi_variance', row.get('isi_variance_mean', 'N/A'))
            bits = row.get('bits_per_spike', row.get('bits_per_spike_mean', 'N/A'))
            sync = row.get('synchrony', row.get('synchrony_mean', 'N/A'))
            report_lines.append(f"| {row['seed']} | {isi} | {bits} | {sync} |")
    else:
        report_lines.append("*No temporal coding metrics available. Ensure `data/processed/spiking_metrics.csv` contains valid JSON in `temporal_coding_metrics` column.*")
    
    report_lines.append("")
    
    # 5. Conclusion
    report_lines.append("## 5. Conclusion")
    report_lines.append("")
    report_lines.append("Based on the paired t-tests and sensitivity analysis, the spiking transformer demonstrates")
    report_lines.append("the following trade-offs compared to the baseline:")
    report_lines.append("")
    
    # Determine conclusion based on stats
    p_energy = ttest_results.get('energy_per_token_kWh', {}).get('p_corrected', 1.0)
    if p_energy < 0.05:
        report_lines.append("- **Energy Efficiency**: Statistically significant reduction in energy consumption observed.")
    else:
        report_lines.append("- **Energy Efficiency**: No statistically significant difference in energy consumption observed.")
        
    p_perp = ttest_results.get('perplexity', {}).get('p_corrected', 1.0)
    if p_perp < 0.05:
        report_lines.append("- **Performance (Perplexity)**: Statistically significant difference in perplexity observed.")
    else:
        report_lines.append("- **Performance (Perplexity)**: No statistically significant difference in perplexity observed.")
        
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Report generated by `code/analysis/report_generator.py`*")
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """
    Main entry point to generate the statistical analysis report.
    """
    print("Generating Statistical Analysis Report...")
    
    # Paths
    baseline_csv = "data/processed/baseline_metrics.csv"
    spiking_csv = "data/processed/spiking_metrics.csv"
    sensitivity_csv = "data/results/sensitivity_analysis.csv"
    output_md = "data/results/statistical_analysis_report.md"
    
    # Load Data
    try:
        baseline_df = load_metrics_data(baseline_csv)
        spiking_df = load_metrics_data(spiking_csv)
    except Exception as e:
        print(f"Error loading metrics data: {e}")
        sys.exit(1)
    
    # Prepare Paired Data
    try:
        paired_data = prepare_paired_data(baseline_df, spiking_df)
    except Exception as e:
        print(f"Error preparing paired data: {e}")
        sys.exit(1)
    
    # Run T-Tests
    ttest_results = {}
    metrics_to_test = ['perplexity', 'energy_per_token_kWh']
    
    for metric in metrics_to_test:
        if metric in paired_data.columns:
            baseline_vals = paired_data[f'baseline_{metric}']
            spiking_vals = paired_data[f'spiking_{metric}']
            
            stat, p_raw = run_paired_ttest(baseline_vals, spiking_vals)
            
            # Apply correction later, store raw here
            ttest_results[metric] = {
                't_statistic': stat,
                'p_value': p_raw,
                'p_corrected': 0.0 # Placeholder
            }
    
    # Apply Correction
    p_values = [ttest_results[m]['p_value'] for m in metrics_to_test]
    corrected_p_values = apply_bonferroni_correction(p_values)
    
    for i, metric in enumerate(metrics_to_test):
        ttest_results[metric]['p_corrected'] = corrected_p_values[i]
    
    # Load Sensitivity Data
    sensitivity_df = pd.DataFrame()
    if os.path.exists(sensitivity_csv):
        sensitivity_df = pd.read_csv(sensitivity_csv)
    
    # Load Temporal Metrics
    temporal_df = load_temporal_metrics()
    
    # Generate Report
    generate_report(
        baseline_df,
        spiking_df,
        ttest_results,
        sensitivity_df,
        temporal_df,
        output_md
    )
    
    print(f"Report successfully generated at: {output_md}")

if __name__ == "__main__":
    main()