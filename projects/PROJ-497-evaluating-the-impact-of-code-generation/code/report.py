import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from config import get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_csv_file(file_path: Path) -> pd.DataFrame:
    """Load a CSV file and return its contents as a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    return pd.read_csv(file_path)

def extract_key_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract key statistics from the aggregated analysis dataset.
    Reads exclusively from data/processed/aggregated_analysis_dataset.csv.
    """
    if df.empty:
        return {}

    stats = {}
    
    # Overall vulnerability counts
    stats['total_vulnerabilities'] = int(df['vulnerability_count'].sum())
    stats['mean_vulnerabilities'] = float(df['vulnerability_count'].mean())
    stats['std_vulnerabilities'] = float(df['vulnerability_count'].std()) if len(df) > 1 else 0.0

    # Group by source type
    source_stats = df.groupby('source_type')['vulnerability_count'].agg(['mean', 'std', 'count']).to_dict('index')
    stats['by_source_type'] = source_stats

    # Group by benchmark
    benchmark_stats = df.groupby('benchmark')['vulnerability_count'].agg(['mean', 'std', 'count']).to_dict('index')
    stats['by_benchmark'] = benchmark_stats

    # ZINB results if available
    if 'p_value' in df.columns and 'ci_lower' in df.columns and 'ci_upper' in df.columns:
        zinb_row = df.dropna(subset=['p_value']).iloc[0] if not df.dropna(subset=['p_value']).empty else None
        if zinb_row is not None:
            stats['zinb_p_value'] = float(zinb_row['p_value'])
            stats['zinb_ci_lower'] = float(zinb_row['ci_lower'])
            stats['zinb_ci_upper'] = float(zinb_row['ci_upper'])
            stats['zinb_convergence'] = zinb_row.get('convergence_status', 'Unknown')
            stats['test_type'] = zinb_row.get('test_type', 'Unknown')

    return stats

def extract_fpr_metrics(json_path: Path) -> Dict[str, Any]:
    """
    Extract FPR metrics from data/processed/fpr_metrics.json.
    Reads exclusively from data/processed.
    """
    if not json_path.exists():
        logger.warning(f"FPR metrics file not found: {json_path}. Skipping FPR section.")
        return {}
    
    try:
        data = load_json_file(json_path)
        return data
    except Exception as e:
        logger.error(f"Error reading FPR metrics: {e}")
        return {}

def extract_zinb_results(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Extract detailed ZINB results if available in the dataset.
    Reads exclusively from data/processed/aggregated_analysis_dataset.csv.
    """
    required_cols = ['p_value', 'ci_lower', 'ci_upper', 'convergence_status', 'test_type']
    if not all(col in df.columns for col in required_cols):
        logger.warning("ZINB result columns not found in dataset.")
        return None

    zinb_data = df.dropna(subset=['p_value']).iloc[0] if not df.dropna(subset=['p_value']).empty else None
    
    if zinb_data is None:
        return None

    return {
        'p_value': float(zinb_data['p_value']),
        'ci_lower': float(zinb_data['ci_lower']),
        'ci_upper': float(zinb_data['ci_upper']),
        'convergence_status': str(zinb_data['convergence_status']),
        'test_type': str(zinb_data['test_type']),
        'effect_size_irr': float(zinb_data.get('irr', 0.0)) if 'irr' in zinb_data else None
    }

def generate_summary_markdown(
    key_stats: Dict[str, Any],
    fpr_metrics: Dict[str, Any],
    zinb_results: Optional[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate the summary report in Markdown format.
    Reads exclusively from data/processed artifacts passed in via parameters.
    """
    lines = []
    lines.append("# Vulnerability Density Analysis Summary Report")
    lines.append("")
    lines.append("## Overview")
    lines.append(f"- **Total Vulnerabilities Found**: {key_stats.get('total_vulnerabilities', 'N/A')}")
    lines.append(f"- **Mean Vulnerabilities per Sample**: {key_stats.get('mean_vulnerabilities', 'N/A'):.2f}")
    lines.append(f"- **Standard Deviation**: {key_stats.get('std_vulnerabilities', 'N/A'):.2f}")
    lines.append("")

    # Source Type Breakdown
    lines.append("## Vulnerability Density by Source Type")
    lines.append("| Source Type | Mean Vulns | Std Dev | Sample Count |")
    lines.append("| :--- | :--- | :--- | :--- |")
    by_source = key_stats.get('by_source_type', {})
    for source, stats in by_source.items():
        lines.append(f"| {source} | {stats.get('mean', 0):.2f} | {stats.get('std', 0):.2f} | {stats.get('count', 0)} |")
    lines.append("")

    # Benchmark Breakdown
    lines.append("## Vulnerability Density by Benchmark")
    lines.append("| Benchmark | Mean Vulns | Std Dev | Sample Count |")
    lines.append("| :--- | :--- | :--- | :--- |")
    by_bench = key_stats.get('by_benchmark', {})
    for bench, stats in by_bench.items():
        lines.append(f"| {bench} | {stats.get('mean', 0):.2f} | {stats.get('std', 0):.2f} | {stats.get('count', 0)} |")
    lines.append("")

    # Statistical Analysis
    lines.append("## Statistical Analysis (ZINB / Permutation)")
    if zinb_results:
        lines.append(f"- **Test Type**: {zinb_results.get('test_type', 'N/A')}")
        lines.append(f"- **P-value**: {zinb_results.get('p_value', 'N/A'):.4e}")
        lines.append(f"- **95% Confidence Interval**: [{zinb_results.get('ci_lower', 'N/A'):.4f}, {zinb_results.get('ci_upper', 'N/A'):.4f}]")
        lines.append(f"- **Convergence Status**: {zinb_results.get('convergence_status', 'N/A')}")
        if zinb_results.get('effect_size_irr') is not None:
            lines.append(f"- **Incidence Rate Ratio (IRR)**: {zinb_results.get('effect_size_irr'):.4f}")
    else:
        lines.append("*Statistical analysis results not available in the processed dataset.*")
    lines.append("")

    # FPR Sensitivity
    lines.append("## False Positive Rate (FPR) Sensitivity Analysis")
    if fpr_metrics:
        lines.append("### Group-Specific FPR")
        lines.append("| Group | False Positive Rate |")
        lines.append("| :--- | :--- |")
        # Assuming fpr_metrics structure from T023
        if isinstance(fpr_metrics, dict):
            for group, rate in fpr_metrics.items():
                lines.append(f"| {group} | {rate:.4f} |")
        else:
            lines.append("*FPR metrics format unrecognized.*")
    else:
        lines.append("*FPR metrics not available. Report generated without FPR adjustment.*")
    lines.append("")

    # Visualization References
    lines.append("## Visualizations")
    lines.append("The following visualizations were generated and are available in the `results/` directory:")
    lines.append("- `results/boxplot_vulnerability_distribution.png` - Comparison of vulnerability counts by source type")
    lines.append("- `results/bar_chart_top_vulnerabilities.png` - Frequency of top vulnerability types")
    lines.append("")

    lines.append("---")
    lines.append("*Report generated by llmXive pipeline.*")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Summary report generated: {output_path}")

def main():
    """
    Main entry point for report generation.
    Reads exclusively from data/processed to satisfy Single Source of Truth.
    """
    paths = get_paths()
    processed_dir = paths['processed']
    results_dir = paths['results']
    
    # Define input paths (Single Source of Truth: data/processed)
    aggregated_csv_path = processed_dir / 'aggregated_analysis_dataset.csv'
    fpr_json_path = processed_dir / 'fpr_metrics.json'
    output_md_path = results_dir / 'summary.md'

    logger.info(f"Starting report generation. Reading from: {processed_dir}")

    try:
        # 1. Load Aggregated Analysis Dataset
        df = load_csv_file(aggregated_csv_path)
        logger.info(f"Loaded aggregated dataset: {len(df)} rows")

        # 2. Extract Key Statistics
        key_stats = extract_key_stats(df)

        # 3. Extract FPR Metrics
        fpr_metrics = extract_fpr_metrics(fpr_json_path)

        # 4. Extract ZINB Results
        zinb_results = extract_zinb_results(df)

        # 5. Generate Markdown Report
        generate_summary_markdown(key_stats, fpr_metrics, zinb_results, output_md_path)

        logger.info("Report generation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Required data file missing: {e}")
        logger.error("Ensure the pipeline has completed phases 1-2 and generated data/processed artifacts.")
        raise
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        raise

if __name__ == '__main__':
    main()