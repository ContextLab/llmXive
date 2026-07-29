"""
Generate a Markdown summary report interpreting the sensitivity analysis results.

This script reads the sensitivity thresholds table (T026a) and the stability metric (T028b),
optionally incorporating limitations from T020a (bin merging/deferral), to produce a
human-readable summary report at `data/processed/sensitivity_summary.md`.

The report includes:
1. A table of thresholds, p-values, and effect sizes.
2. A conclusion on robustness (PASS/FAIL based on count >= 2).
3. A limitations section if bin merging or deferral occurred.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from utils
from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_sensitivity_results(csv_path: Path) -> List[Dict[str, Any]]:
    """Load sensitivity threshold results from CSV."""
    import csv
    results = []
    if not csv_path.exists():
        logger.error(f"Sensitivity results file not found: {csv_path}")
        return results
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'threshold_hop': int(row['threshold_hop']),
                'p_value': float(row['p_value']),
                'effect_size': float(row['effect_size']),
                'is_significant': row['is_significant'].lower() == 'true'
            })
    return results


def load_stability_metric(json_path: Path) -> Optional[Dict[str, Any]]:
    """Load stability metric from JSON."""
    if not json_path.exists():
        logger.warning(f"Stability metric file not found: {json_path}")
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_limitations_info(json_path: Path) -> Optional[Dict[str, Any]]:
    """Load bin config/limitations info from T020a output."""
    if not json_path.exists():
        logger.debug(f"Bin config file not found: {json_path}")
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_markdown_report(
    sensitivity_results: List[Dict[str, Any]],
    stability_metric: Optional[Dict[str, Any]],
    limitations_info: Optional[Dict[str, Any]]
) -> str:
    """Generate the Markdown report content."""
    lines = []
    
    # Header
    lines.append("# Sensitivity Analysis Summary Report")
    lines.append("")
    lines.append("**Project**: llmXive follow-up: extending VideoKR")
    lines.append("**Task**: T026b - Summary Report")
    lines.append("")
    
    # Introduction
    lines.append("## Overview")
    lines.append("")
    lines.append("This report summarizes the sensitivity analysis of the 'reasoning cliff' threshold.")
    lines.append("We evaluated the statistical significance (p-value) and effect size (accuracy drop)")
    lines.append("across multiple threshold definitions (2, 3, 4, 5 hops) to determine the robustness")
    lines.append("of the non-linear performance degradation observed in video reasoning tasks.")
    lines.append("")
    
    # Threshold Comparison Table
    lines.append("## Threshold Comparison")
    lines.append("")
    lines.append("The following table shows the results of the permutation test for each threshold definition:")
    lines.append("")
    lines.append("| Threshold (Hops) | P-Value | Effect Size | Significant (p < 0.05) |")
    lines.append("|------------------|---------|-------------|------------------------|")
    
    if not sensitivity_results:
        lines.append("| *No data available* | - | - | - |")
    else:
        for res in sensitivity_results:
            sig_str = "Yes" if res['is_significant'] else "No"
            lines.append(
                f"| {res['threshold_hop']} | {res['p_value']:.4f} | {res['effect_size']:.4f} | {sig_str} |"
            )
    lines.append("")
    
    # Robustness Conclusion
    lines.append("## Robustness Conclusion")
    lines.append("")
    
    if stability_metric:
        robustness_status = stability_metric.get('robustness_status', 'UNKNOWN')
        significant_count = stability_metric.get('significant_count', 0)
        total_count = stability_metric.get('total_thresholds', 0)
        
        lines.append(f"**Status**: **{robustness_status}**")
        lines.append("")
        lines.append(f"- **Significant Thresholds**: {significant_count} out of {total_count}")
        lines.append(f"- **Criteria**: A threshold is considered robust if the count of significant results is >= 2.")
        lines.append("")
        
        if robustness_status == 'PASS':
            lines.append("### Interpretation")
            lines.append("The 'reasoning cliff' phenomenon is **robust** across different threshold definitions.")
            lines.append("Multiple hop-count thresholds (>= 2) yielded statistically significant drops in accuracy,")
            lines.append("suggesting a genuine non-linear degradation in model performance as reasoning complexity increases.")
        else:
            lines.append("### Interpretation")
            lines.append("The 'reasoning cliff' phenomenon is **not robust** across different threshold definitions.")
            lines.append("Fewer than 2 thresholds yielded statistically significant results, indicating that")
            lines.append("the observed non-linearity may be sensitive to the specific binning strategy or insufficient data.")
    else:
        lines.append("**Status**: **UNKNOWN**")
        lines.append("")
        lines.append("Stability metric file was missing. Unable to determine robustness.")
    
    lines.append("")
    
    # Limitations Section
    if limitations_info:
        strategy = limitations_info.get('strategy', 'unknown')
        status = limitations_info.get('status', 'unknown')
        
        if strategy == 'merged' or status == 'deferred':
            lines.append("## Limitations")
            lines.append("")
            lines.append("The statistical analysis was affected by bin size constraints:")
            lines.append("")
            
            if strategy == 'merged':
                lines.append("- **Bin Merging**: Due to low sample counts in the highest hop bin, adjacent bins were merged.")
                lines.append(f"  - **Strategy**: {strategy}")
                lines.append("  - **Impact**: This may smooth out sharp transitions and affect the precision of the threshold detection.")
            elif status == 'deferred':
                lines.append("- **Deferral**: Some bin comparisons were deferred due to insufficient statistical power (< 50 samples).")
                lines.append("  - **Reason**: `insufficient_power`")
                lines.append("  - **Impact**: The analysis could not be performed for all potential thresholds, potentially biasing the robustness count.")
            
            lines.append("")
            lines.append("These limitations should be considered when interpreting the robustness conclusion.")
            lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("*Generated by code/analysis/generate_sensitivity_summary.py (Task T026b)*")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    project_root = get_project_root()
    
    # Define paths
    sensitivity_csv_path = project_root / "data" / "processed" / "sensitivity_thresholds.csv"
    stability_json_path = project_root / "data" / "processed" / "stability_metric.json"
    bin_config_path = project_root / "data" / "processed" / "bin_config.json"
    output_path = project_root / "data" / "processed" / "sensitivity_summary.md"
    
    ensure_dir(output_path.parent)
    
    # Load inputs
    logger.info(f"Loading sensitivity results from {sensitivity_csv_path}...")
    sensitivity_results = load_sensitivity_results(sensitivity_csv_path)
    
    logger.info(f"Loading stability metric from {stability_json_path}...")
    stability_metric = load_stability_metric(stability_json_path)
    
    logger.info(f"Loading bin config/limitations from {bin_config_path}...")
    limitations_info = load_limitations_info(bin_config_path)
    
    # Generate report
    logger.info("Generating Markdown report...")
    report_content = generate_markdown_report(sensitivity_results, stability_metric, limitations_info)
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Successfully wrote report to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())