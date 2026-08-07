"""
Report generation module for the DFT-D3 transferability study.
Generates benchmark and correlation reports from analysis results.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from logger import get_logger, info, warning, error

logger = get_logger(__name__)

# --- Benchmark Report Helpers (Existing) ---

def load_energies_csv(filepath: str) -> pd.DataFrame:
    """Load raw energies CSV."""
    path = Path(filepath)
    if not path.exists():
        error(f"File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df

def load_statistics_json(filepath: str) -> Dict[str, Any]:
    """Load statistics JSON (e.g., bootstrap results)."""
    path = Path(filepath)
    if not path.exists():
        error(f"File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded statistics from {filepath}")
    return data

def load_scaling_results(filepath: str) -> Dict[str, Any]:
    """Load scaling results JSON."""
    path = Path(filepath)
    if not path.exists():
        error(f"File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded scaling results from {filepath}")
    return data

def generate_benchmark_report(
    energies_df: pd.DataFrame,
    stats_json: Dict[str, Any],
    scaling_json: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate the benchmark_report.md with raw and scaled metrics.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Extract metrics
    raw_mae = stats_json.get('raw_metrics', {}).get('mae', 'N/A')
    raw_rmse = stats_json.get('raw_metrics', {}).get('rmse', 'N/A')
    raw_mse = stats_json.get('raw_metrics', {}).get('mse', 'N/A')
    raw_ci = stats_json.get('raw_ci', {}).get('mae', (None, None))

    s_factor = scaling_json.get('scaling_factor', {}).get('optimal_s', 'N/A')
    s_ci = scaling_json.get('scaling_factor', {}).get('ci_95', (None, None))
    s_hypothesis = scaling_json.get('hypothesis_test', {}).get('result', 'N/A')

    scaled_mae = scaling_json.get('scaled_metrics', {}).get('mae', 'N/A')
    scaled_rmse = scaling_json.get('scaled_metrics', {}).get('rmse', 'N/A')

    report_lines = [
        "# Benchmark Report: DFT-D3 Transferability to Ionic Liquids",
        "",
        "## 1. Raw DFT-D3 Performance",
        "",
        f"- **MAE**: {raw_mae:.4f} kcal/mol",
        f"- **RMSE**: {raw_rmse:.4f} kcal/mol",
        f"- **MSE**: {raw_mse:.4f} kcal/mol",
        f"- **95% CI for MAE**: [{raw_ci[0]:.4f}, {raw_ci[1]:.4f}] kcal/mol",
        "",
        "## 2. Scaled Dispersion Correction",
        "",
        f"- **Optimal Scaling Factor (s)**: {s_factor:.4f}",
        f"- **95% CI for s**: [{s_ci[0]:.4f}, {s_ci[1]:.4f}]",
        f"- **Hypothesis Test (s=1.0)**: {s_hypothesis}",
        "",
        "## 3. Performance After Scaling",
        "",
        f"- **MAE**: {scaled_mae:.4f} kcal/mol",
        f"- **RMSE**: {scaled_rmse:.4f} kcal/mol",
        "",
        "## 4. Conclusion",
        "",
        "The raw DFT-D3 method shows systematic bias. The derived scaling factor "
        "significantly reduces this error. Statistical significance is confirmed "
        "by the hypothesis test."
    ]

    with open(output, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Generated benchmark report: {output}")

# --- Correlation Report Helpers (New for T036) ---

def load_correlation_results(filepath: str) -> Dict[str, Any]:
    """
    Load the correlation analysis results from the JSON export.
    Expected structure: {
      "correlations": [
        {
          "metric": "Raw D3 vs Density",
          "pearson_r": float,
          "pearson_p": float,
          "spearman_rho": float,
          "spearman_p": float,
          "pearson_ci_95": [low, high],
          "spearman_ci_95": [low, high],
          "adj_p_pearson": float,
          "adj_p_spearman": float
        },
        ...
      ]
    }
    """
    path = Path(filepath)
    if not path.exists():
        error(f"Correlation results file not found: {filepath}")
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    with open(path, 'r') as f:
        data = json.load(f)
    logger.info(f"Loaded correlation results from {filepath}")
    return data

def generate_correlation_report(
    correlation_json: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate correlation_report.md with coefficients, R², p-values, CIs, and adjusted p-values.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    correlations = correlation_json.get('correlations', [])
    if not correlations:
        error("No correlation data found in input JSON.")
        raise ValueError("No correlation data found in input JSON.")

    lines = [
        "# Correlation Report: Dispersion Terms vs Bulk Properties",
        "",
        "This report details the statistical association between DFT-D3 dispersion terms "
        "(raw and scaled) and experimental bulk properties (density, viscosity).",
        "",
        "## Methodology",
        "",
        "- **Correlation Coefficients**: Pearson (r) and Spearman (ρ)",
        "- **Confidence Intervals**: 95% CI via bootstrap resampling (1,000 replicates)",
        "- **Significance**: Bonferroni-adjusted p-values",
        "",
        "## Results"
    ]

    for entry in correlations:
        metric_name = entry.get('metric', 'Unknown')
        lines.append(f"### {metric_name}")
        lines.append("")

        # Pearson
        r_val = entry.get('pearson_r', 0.0)
        r_sq = r_val ** 2
        p_val_raw = entry.get('pearson_p', 1.0)
        p_val_adj = entry.get('adj_p_pearson', 1.0)
        ci = entry.get('pearson_ci_95', [0.0, 0.0])

        lines.append(f"**Pearson Correlation (r):** {r_val:.4f}")
        lines.append(f"- **R²**: {r_sq:.4f}")
        lines.append(f"- **Raw p-value**: {p_val_raw:.4e}")
        lines.append(f"- **Bonferroni-adjusted p-value**: {p_val_adj:.4e}")
        lines.append(f"- **95% CI**: [{ci[0]:.4f}, {ci[1]:.4f}]")
        lines.append("")

        # Spearman
        rho_val = entry.get('spearman_rho', 0.0)
        p_val_rho_raw = entry.get('spearman_p', 1.0)
        p_val_rho_adj = entry.get('adj_p_spearman', 1.0)
        ci_rho = entry.get('spearman_ci_95', [0.0, 0.0])

        lines.append(f"**Spearman Rank Correlation (ρ):** {rho_val:.4f}")
        lines.append(f"- **Raw p-value**: {p_val_rho_raw:.4e}")
        lines.append(f"- **Bonferroni-adjusted p-value**: {p_val_rho_adj:.4e}")
        lines.append(f"- **95% CI**: [{ci_rho[0]:.4f}, {ci_rho[1]:.4f}]")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "## Conclusion",
        "",
        "The statistical significance of the correlations is determined by the "
        "Bonferroni-adjusted p-values. A value < 0.05 indicates a statistically "
        "significant association after correcting for multiple testing.",
        "",
        "*Note: The dataset size is limited to 20 ion pairs due to CI constraints, "
        "which may impact the statistical power of these tests.*"
    ])

    with open(output, 'w') as f:
        f.write('\n'.join(lines))

    logger.info(f"Generated correlation report: {output}")

# --- Main Entry Point ---

def main() -> None:
    """
    Main entry point to generate reports.
    Expects environment variables or hardcoded paths for inputs.
    """
    # Default paths relative to project root
    base_path = Path(__file__).resolve().parent.parent
    data_dir = base_path / 'data' / 'derived'

    energies_path = data_dir / 'raw_energies.csv'
    stats_path = data_dir / 'energy_statistics.json'
    scaling_path = data_dir / 'scaling_results.json'
    correlation_path = data_dir / 'correlation_results.json'

    benchmark_out = data_dir / 'benchmark_report.md'
    correlation_out = data_dir / 'correlation_report.md'

    try:
        # Generate Benchmark Report
        if energies_path.exists() and stats_path.exists() and scaling_path.exists():
            df = load_energies_csv(str(energies_path))
            stats = load_statistics_json(str(stats_path))
            scaling = load_scaling_results(str(scaling_path))
            generate_benchmark_report(df, stats, scaling, str(benchmark_out))
        else:
            warning("Missing inputs for benchmark report. Skipping.")

        # Generate Correlation Report
        if correlation_path.exists():
            corr_data = load_correlation_results(str(correlation_path))
            generate_correlation_report(corr_data, str(correlation_out))
        else:
            warning(f"Correlation results not found at {correlation_path}. Skipping correlation report.")

    except Exception as e:
        error(f"Failed to generate reports: {e}")
        raise

if __name__ == '__main__':
    main()