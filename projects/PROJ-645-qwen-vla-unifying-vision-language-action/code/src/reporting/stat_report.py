"""
Statistical Report Generator for Cross-Embodiment Transfer Study.

Generates `stat_report.md` containing p-values, corrected decisions,
and absolute improvement metrics based on Wilcoxon signed-rank test results.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logging_config import get_logger, setup_logging

# Constants
EVAL_RESULTS_PATH = "data/eval_results.json"
STAT_RESULTS_PATH = "data/stat_results.json"
OUTPUT_REPORT_PATH = "data/stat_report.md"

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    path = Path(file_path)
    if not path.exists():
        logging.error(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {path}: {e}")
        return None

def extract_metrics(eval_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract success rate metrics for within-embodiment and cross-embodiment from eval data.
    
    Expected structure in eval_data:
    {
        "within-embodiment": {"success_rate": [list of floats]},
        "cross-embodiment": {"success_rate": [list of floats]}
    }
    """
    metrics = {}
    for key in ["within-embodiment", "cross-embodiment"]:
        if key in eval_data and "success_rate" in eval_data[key]:
            metrics[key] = {
                "success_rates": eval_data[key]["success_rate"],
                "mean": sum(eval_data[key]["success_rate"]) / len(eval_data[key]["success_rate"]) if eval_data[key]["success_rate"] else 0.0
            }
        else:
            logging.warning(f"Missing or invalid data for key: {key}")
            metrics[key] = {"success_rates": [], "mean": 0.0}
    return metrics

def generate_markdown_report(
    stat_results: Dict[str, Any],
    eval_metrics: Dict[str, Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate the statistical report in Markdown format.
    
    Args:
        stat_results: Results from wilcoxon_test.py (p_value, is_significant, etc.)
        eval_metrics: Extracted metrics from eval_results.json
        output_path: Path to save the markdown report
    """
    lines = []
    lines.append("# Cross-Embodiment Transfer Statistical Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("This report summarizes the statistical comparison between the cross-embodiment model")
    lines.append("(trained on multi-platform Open X-Embodiment data) and the single-embodiment baseline")
    lines.append("(trained on Franka-only data) using the Wilcoxon signed-rank test with Holm-Bonferroni correction.")
    lines.append("")
    
    # Statistical Results Section
    lines.append("## Statistical Test Results")
    lines.append("")
    lines.append(f"- **Test Method**: {stat_results.get('method', 'Wilcoxon Signed-Rank')}")
    lines.append(f"- **Statistic**: {stat_results.get('statistic', 'N/A')}")
    lines.append(f"- **Raw p-value**: {stat_results.get('p_value', 'N/A'):.6f}")
    lines.append(f"- **Holm-Bonferroni Corrected Decision**: {'Significant' if stat_results.get('is_significant', False) else 'Not Significant'}")
    lines.append("")
    
    # Performance Metrics Section
    lines.append("## Performance Metrics")
    lines.append("")
    lines.append("| Embodiment Type | Mean Success Rate | Standard Deviation |")
    lines.append("| :--- | :--- | :--- |")
    
    within_rates = eval_metrics.get("within-embodiment", {}).get("success_rates", [])
    cross_rates = eval_metrics.get("cross-embodiment", {}).get("success_rates", [])
    
    within_mean = eval_metrics.get("within-embodiment", {}).get("mean", 0.0)
    cross_mean = eval_metrics.get("cross-embodiment", {}).get("mean", 0.0)
    
    # Calculate std dev manually or approximate if list is empty
    def calc_std(vals):
        if len(vals) < 2:
            return 0.0
        mean = sum(vals) / len(vals)
        variance = sum((x - mean) ** 2 for x in vals) / len(vals)
        return variance ** 0.5

    within_std = calc_std(within_rates)
    cross_std = calc_std(cross_rates)

    lines.append(f"| Within-Embodiment (Franka) | {within_mean:.4f} | {within_std:.4f} |")
    lines.append(f"| Cross-Embodiment (UR/Franka Mix) | {cross_mean:.4f} | {cross_std:.4f} |")
    lines.append("")
    
    # Absolute Improvement Section
    lines.append("## Absolute Improvement Analysis")
    lines.append("")
    abs_improvement = cross_mean - within_mean
    rel_improvement = (abs_improvement / within_mean * 100) if within_mean != 0 else 0.0
    
    lines.append(f"- **Absolute Difference (Cross - Within)**: {abs_improvement:.4f}")
    lines.append(f"- **Relative Improvement**: {rel_improvement:.2f}%")
    lines.append("")
    
    if abs_improvement > 0:
        lines.append("*Conclusion*: The cross-embodiment model shows an absolute improvement of "
                   f"{abs_improvement:.4f} in success rate over the single-embodiment baseline.")
    elif abs_improvement < 0:
        lines.append("*Conclusion*: The cross-embodiment model shows a decrease in performance compared to "
                   f"the single-embodiment baseline by {abs_improvement:.4f}.")
    else:
        lines.append("*Conclusion*: No difference in mean success rate observed.")
        
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by `src/reporting/stat_report.py`.*")
    
    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logging.info(f"Statistical report generated at: {output_file}")

def main():
    """Main entry point for the statistical report generator."""
    setup_logging(level=logging.INFO)
    logger = get_logger(__name__)
    
    logger.info("Starting statistical report generation...")
    
    # Load evaluation results
    eval_data = load_json_file(EVAL_RESULTS_PATH)
    if not eval_data:
        logger.error("Failed to load evaluation results. Exiting.")
        sys.exit(1)
        
    # Load statistical test results
    stat_data = load_json_file(STAT_RESULTS_PATH)
    if not stat_data:
        logger.error("Failed to load statistical test results. Exiting.")
        sys.exit(1)
    
    # Extract metrics
    eval_metrics = extract_metrics(eval_data)
    
    # Generate report
    generate_markdown_report(stat_data, eval_metrics, OUTPUT_REPORT_PATH)
    
    logger.info("Report generation completed successfully.")

if __name__ == "__main__":
    main()