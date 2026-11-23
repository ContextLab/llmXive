import json
import logging
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_sensitivity_json(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Load sensitivity results from JSON or CSV.
    T026a specifies CSV, but the API surface mentions JSON.
    This function handles both to ensure robustness.
    """
    if file_path.suffix == '.json':
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('results', []) if isinstance(data, dict) else data
        except Exception as e:
            logger.error(f"Error loading JSON {file_path}: {e}")
            return None
    elif file_path.suffix == '.csv':
        if not file_path.exists():
            return None
        try:
            results = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append({
                        'threshold_hop': int(row['threshold_hop']),
                        'p_value': float(row['p_value']),
                        'effect_size': float(row['effect_size']),
                        'is_significant': row['is_significant'].lower() == 'true'
                    })
            return results
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
            return None
    else:
        logger.error(f"Unsupported file format: {file_path.suffix}")
        return None

def load_stability_metric(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load stability metric JSON."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading stability metric {file_path}: {e}")
        return None

def load_limitations_info(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load bin configuration for limitations info."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading bin config {file_path}: {e}")
        return None

def generate_markdown_report(
    sensitivity_results: List[Dict[str, Any]],
    stability_metric: Optional[Dict[str, Any]],
    bin_config: Optional[Dict[str, Any]],
    output_path: Path
) -> bool:
    """
    Generate the sensitivity report Markdown file.
    """
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        "This report summarizes the robustness of the detected 'reasoning cliff' across different threshold definitions.",
        ""
    ]

    if not sensitivity_results:
        report_lines.append("## Data Availability")
        report_lines.append("")
        report_lines.append("No sensitivity results were found to generate the report.")
        report_lines.append("")
    else:
        # 1. Generate Table
        report_lines.extend([
            "## Threshold Sweep Results",
            "",
            "| Threshold (Hops) | P-Value | Effect Size | Significant (p < 0.05) |",
            "|------------------|---------|-------------|------------------------|"
        ])

        significant_count = 0
        for row in sensitivity_results:
            threshold = row.get('threshold_hop', 0)
            p_val = row.get('p_value', 0.0)
            eff_size = row.get('effect_size', 0.0)
            is_sig = row.get('is_significant', False)
            if is_sig:
                significant_count += 1
            
            sig_str = "Yes" if is_sig else "No"
            report_lines.append(f"| {threshold} | {p_val:.4f} | {eff_size:.4f} | {sig_str} |")

        # 2. Robustness Conclusion
        robust_status = "Robust" if significant_count >= 2 else "Not Robust"
        report_lines.extend([
            "",
            "## Robustness Conclusion",
            "",
            f"**Status**: {robust_status}",
            "",
            f"**Reasoning**: The 'reasoning cliff' is considered {'Robust' if robust_status == 'Robust' else 'Not Robust'} because the number of significant thresholds (p < 0.05) is {significant_count}.",
            "Per the specification (SC-003), a threshold count >= 2 indicates robustness."
        ])

    # 3. Limitations Section (Check T020a status)
    if bin_config:
        strategy = bin_config.get('strategy', '')
        bins = bin_config.get('bins', [])
        if strategy in ['merged', 'deferred']:
            report_lines.extend([
                "",
                "## Limitations",
                "",
                f"The statistical analysis was performed with the following bin configuration adjustments:",
                f"- **Strategy**: {strategy}",
                f"- **Final Bins**: {bins}",
                "",
                "If the strategy was 'merged', adjacent bins were combined due to insufficient sample size (< 50).",
                "If the strategy was 'deferred', the statistical test could not be performed for specific comparisons due to power constraints."
            ])

    # Ensure directory exists and write
    ensure_dir(output_path.parent)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        logger.info(f"Report successfully written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write report to {output_path}: {e}")
        return False

def main():
    project_root = get_project_root()
    processed_dir = get_path(project_root, 'data/processed')

    # Input paths
    # T026a produces CSV, T028b produces JSON, T020a produces JSON
    sensitivity_results_path = processed_dir / 'sensitivity_thresholds.csv'
    stability_metric_path = processed_dir / 'stability_metric.json'
    bin_config_path = processed_dir / 'bin_config.json'
    output_path = processed_dir / 'sensitivity_report.md'

    sensitivity_results = load_sensitivity_json(sensitivity_results_path)
    stability_metric = load_stability_metric(stability_metric_path)
    bin_config = load_limitations_info(bin_config_path)

    success = generate_markdown_report(
        sensitivity_results or [],
        stability_metric,
        bin_config,
        output_path
    )

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())