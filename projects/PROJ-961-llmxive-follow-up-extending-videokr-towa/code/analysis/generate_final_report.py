"""
Final report generation module.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_markdown_file(file_path: Path) -> str:
    """Load markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def format_table_row(headers: List[str], values: List[str]) -> str:
    """Format a table row."""
    return "| " + " | ".join(str(v) for v in values) + " |"

def generate_final_report(
    coverage_data: Dict[str, Any],
    threshold_results: Dict[str, Any],
    sensitivity_results: List[Dict[str, Any]],
    stability_metric: Dict[str, Any]
) -> str:
    """Generate final report markdown."""
    report = []
    report.append("# Final Report: VideoKR Threshold Analysis")
    report.append("")
    report.append("## 1. Annotation Coverage")
    report.append(f"- Total records: {coverage_data.get('total_input_records', 'N/A')}")
    report.append(f"- Annotated: {coverage_data.get('annotated_count', 'N/A')}")
    report.append(f"- Proportion: {coverage_data.get('proportion', 0):.2%}")
    report.append("")

    report.append("## 2. Threshold Detection")
    report.append(f"- Optimal knot: {threshold_results.get('optimal_knot', 'N/A')}")
    report.append(f"- P-value: {threshold_results.get('p_value', 'N/A')}")
    report.append(f"- Significant: {threshold_results.get('is_significant', 'N/A')}")
    report.append(f"- Conclusion: {threshold_results.get('conclusion', 'N/A')}")
    report.append("")

    report.append("## 3. Sensitivity Analysis")
    report.append("| Threshold | P-value | Effect Size | Significant |")
    report.append("|-----------|---------|-------------|-------------|")
    for result in sensitivity_results:
        report.append(format_table_row(
            ["Threshold", "P-value", "Effect Size", "Significant"],
            [
                str(result.get("threshold_hop")),
                f"{result.get('p_value', 0):.4f}",
                f"{result.get('effect_size', 0):.4f}",
                str(result.get("is_significant", False))
            ]
        ))
    report.append("")

    report.append("## 4. Stability Metric")
    report.append(f"- Significant thresholds: {stability_metric.get('significant_count', 0)}")
    report.append(f"- Robustness status: {stability_metric.get('robustness_status', 'N/A')}")
    report.append("")

    report.append("## 5. Conclusion")
    if stability_metric.get("robustness_status") == "PASS":
        report.append("The threshold detection is robust across multiple threshold definitions.")
    else:
        report.append("The threshold detection shows limited robustness across threshold definitions.")

    return "\n".join(report)

def main():
    """Main entry point for final report generation."""
    project_root = get_project_root()
    processed_dir = get_path(project_root, "processed_data")

    coverage_path = processed_dir / "annotation_coverage.json"
    threshold_path = processed_dir / "threshold_results.json"
    sensitivity_path = processed_dir / "sensitivity_intermediate.json"
    stability_path = processed_dir / "stability_metric.json"
    output_path = processed_dir / "final_report.md"

    if not coverage_path.exists():
        logger.error(f"Coverage file not found: {coverage_path}")
        sys.exit(1)

    coverage_data = load_json_file(coverage_path)
    threshold_results = load_json_file(threshold_path) if threshold_path.exists() else {}
    sensitivity_results = load_json_file(sensitivity_path) if sensitivity_path.exists() else []
    stability_metric = load_json_file(stability_path) if stability_path.exists() else {}

    report = generate_final_report(coverage_data, threshold_results, sensitivity_results, stability_metric)

    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    logger.info(f"Final report written to {output_path}")

if __name__ == "__main__":
    main()