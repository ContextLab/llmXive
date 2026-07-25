"""
Generate a Markdown summary report interpreting the sensitivity analysis results.

This script reads the sensitivity thresholds CSV (T026a) and the stability metric
(T028b) to produce a human-readable Markdown report (T026b) that interprets
the robustness of the "reasoning cliff" finding across different threshold definitions.

It also incorporates any limitations (merged bins, deferred tests) from the
threshold detection phase (T021) if available.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sensitivity_results(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the sensitivity thresholds CSV file.

    Args:
        csv_path: Path to the sensitivity_thresholds.csv file.

    Returns:
        List of dictionaries, each representing a threshold row.
    """
    import csv
    results = []
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row['threshold_hop'] = int(row['threshold_hop'])
                row['p_value'] = float(row['p_value'])
                row['effect_size'] = float(row['effect_size'])
                row['is_significant'] = row['is_significant'].lower() == 'true'
                results.append(row)
    except FileNotFoundError:
        logger.error(f"Sensitivity results file not found: {csv_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading sensitivity results: {e}")
        raise
    return results


def load_stability_metric(json_path: Path) -> Dict[str, Any]:
    """
    Load the stability metric JSON file.

    Args:
        json_path: Path to the stability_metric.json file.

    Returns:
        Dictionary containing stability metrics.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Stability metric file not found: {json_path}. Proceeding without robustness status.")
        return {}
    except Exception as e:
        logger.error(f"Error reading stability metric: {e}")
        return {}


def load_limitations_info(json_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load limitations info from threshold_results.json if available.

    Args:
        json_path: Path to the threshold_results.json file.

    Returns:
        Dictionary containing limitations info, or None if not found.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Check if there are limitations (e.g., merged bins, deferred tests)
            if data.get('status') == 'deferred' or data.get('bin_status') in ['merged', 'deferred']:
                return {
                    'bin_status': data.get('bin_status'),
                    'reason': data.get('reason'),
                    'merged_bin_definition': data.get('merged_bin_definition', [])
                }
            return None
    except FileNotFoundError:
        logger.debug("Threshold results file not found. No limitations to report.")
        return None
    except Exception as e:
        logger.warning(f"Could not read threshold results for limitations: {e}")
        return None


def generate_markdown_report(
    sensitivity_results: List[Dict[str, Any]],
    stability_metric: Dict[str, Any],
    limitations: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a Markdown summary report interpreting the sensitivity analysis.

    Args:
        sensitivity_results: List of threshold analysis results.
        stability_metric: Stability metric data (robustness status).
        limitations: Optional limitations info from threshold detection.

    Returns:
        Markdown formatted string report.
    """
    lines = []

    # Header
    lines.append("# Sensitivity Analysis Summary Report")
    lines.append("")
    lines.append("This report interprets the results of the sensitivity analysis on the 'reasoning cliff' threshold.")
    lines.append("The analysis tests whether the non-linear drop in accuracy (the 'cliff') remains statistically significant")
    lines.append("across different definitions of the reasoning threshold (2-hop, 3-hop, and 4-hop).")
    lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("- **Data Source**: `data/processed/annotated_videokr.csv` (exact integer chain lengths).")
    lines.append("- **Thresholds Tested**: 2-hop, 3-hop, and 4-hop.")
    lines.append("- **Statistical Test**: Permutation test (n=1000) with Bonferroni correction.")
    lines.append("- **Significance Level**: α = 0.05.")
    lines.append("- **Robustness Criterion**: The cliff is considered 'Robust' if ≥2 of the 3 thresholds yield a significant result (p < 0.05).")
    lines.append("")

    # Results Table
    lines.append("## Results")
    lines.append("")
    lines.append("| Threshold (Hops) | P-Value | Effect Size | Significant (p < 0.05) |")
    lines.append("| :---: | :---: | :---: | :---: |")

    for row in sensitivity_results:
        sig_str = "Yes" if row['is_significant'] else "No"
        lines.append(f"| {row['threshold_hop']} | {row['p_value']:.4f} | {row['effect_size']:.4f} | {sig_str} |")

    lines.append("")

    # Robustness Conclusion
    robustness_status = stability_metric.get('robustness_status', 'Unknown')
    significant_count = sum(1 for r in sensitivity_results if r['is_significant'])
    total_tests = len(sensitivity_results)

    lines.append("## Robustness Conclusion")
    lines.append("")
    lines.append(f"**Significant Thresholds**: {significant_count} out of {total_tests}")
    lines.append("")

    if robustness_status == 'PASS':
        lines.append("### ✅ Robust")
        lines.append("")
        lines.append("The 'reasoning cliff' finding is **robust**. The non-linear drop in accuracy remains statistically significant")
        lines.append("across multiple threshold definitions (≥2 out of 3 tests). This suggests the observed performance degradation")
        lines.append("is a genuine property of the reasoning complexity in the VideoKR-SFT dataset, not an artifact of a specific")
        lines.append("threshold choice.")
    elif robustness_status == 'FAIL':
        lines.append("### ❌ Not Robust")
        lines.append("")
        lines.append("The 'reasoning cliff' finding is **not robust**. The statistical significance of the performance drop")
        lines.append("varies depending on the threshold definition, with fewer than 2 out of 3 tests yielding significant results.")
        lines.append("This suggests the observed effect may be sensitive to how 'complex reasoning' is defined, or that the signal")
        lines.append("is weaker than initially detected.")
    else:
        lines.append("### ⚠️ Inconclusive")
        lines.append("")
        lines.append("Robustness status could not be determined from the provided metrics.")

    lines.append("")

    # Limitations Section
    if limitations:
        lines.append("## Limitations")
        lines.append("")
        lines.append("The following limitations were identified during the threshold detection phase and apply to this analysis:")
        lines.append("")

        if limitations.get('bin_status') == 'merged':
            merged_def = limitations.get('merged_bin_definition', [])
            lines.append(f"- **Merged Bins**: The statistical test required merging bins due to insufficient sample size.")
            lines.append(f"  - **Merged Definition**: {', '.join(map(str, merged_def))}")
            lines.append(f"  - **Reason**: {limitations.get('reason', 'Insufficient power in original bins')}")
            lines.append("")
            lines.append("  *Note: The sensitivity analysis was performed on the merged bin configuration.*")

        if limitations.get('bin_status') == 'deferred' or limitations.get('reason') == 'insufficient_power':
            lines.append(f"- **Deferred Test**: The statistical test was deferred for some comparisons due to insufficient sample size.")
            lines.append(f"  - **Reason**: {limitations.get('reason', 'Insufficient power')}")
            lines.append("")
            lines.append("  *Note: This may affect the robustness conclusion if the deferred comparisons were critical.*")

        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by `code/analysis/generate_sensitivity_summary.py`*")

    return "\n".join(lines)


def main():
    """Main entry point for the sensitivity summary generation."""
    project_root = get_project_root()
    data_dir = get_path(project_root, "data/processed")

    # Define paths
    sensitivity_csv = data_dir / "sensitivity_thresholds.csv"
    stability_json = data_dir / "stability_metric.json"
    threshold_results_json = data_dir / "threshold_results.json"
    output_md = data_dir / "sensitivity_summary.md"

    # Ensure output directory exists
    ensure_dir(output_md.parent)

    logger.info(f"Loading sensitivity results from {sensitivity_csv}")
    sensitivity_results = load_sensitivity_results(sensitivity_csv)

    logger.info(f"Loading stability metric from {stability_json}")
    stability_metric = load_stability_metric(stability_json)

    logger.info(f"Checking for limitations in {threshold_results_json}")
    limitations = load_limitations_info(threshold_results_json)

    logger.info("Generating Markdown report...")
    report_content = generate_markdown_report(sensitivity_results, stability_metric, limitations)

    logger.info(f"Writing report to {output_md}")
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info("Sensitivity summary report generated successfully.")


if __name__ == "__main__":
    main()