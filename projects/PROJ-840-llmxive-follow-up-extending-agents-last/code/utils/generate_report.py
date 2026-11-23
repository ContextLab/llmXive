import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file from the specified path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def generate_markdown_report(stats: Dict[str, Any], sensitivity: Dict[str, Any], output_path: str):
    """Generate a markdown report from stats and sensitivity analysis."""
    report_lines = [
        "# LLMXive Analysis Report",
        "",
        "## Statistical Analysis",
        "",
    ]

    # Handle stats values that might be missing or non-numeric
    baseline_rate = stats.get('baseline_pass_rate')
    intervention_rate = stats.get('intervention_pass_rate')
    p_value = stats.get('p_value')
    is_significant = stats.get('is_significant')

    if baseline_rate is not None:
        report_lines.append(f"- **Baseline Pass Rate**: {baseline_rate:.2%}")
    else:
        report_lines.append("- **Baseline Pass Rate**: N/A")

    if intervention_rate is not None:
        report_lines.append(f"- **Intervention Pass Rate**: {intervention_rate:.2%}")
    else:
        report_lines.append("- **Intervention Pass Rate**: N/A")

    if p_value is not None:
        report_lines.append(f"- **P-Value**: {p_value}")
    else:
        report_lines.append("- **P-Value**: N/A")

    if is_significant is not None:
        report_lines.append(f"- **Significant**: {is_significant}")
    else:
        report_lines.append("- **Significant**: N/A")

    report_lines.extend([
        "",
        "## Sensitivity Analysis",
        "",
        "| Checkpoint Interval | Pass Rate | Delta |",
        "|---------------------|-----------|-------|",
    ])

    sensitivity_data = sensitivity.get("results", [])
    if not sensitivity_data:
        report_lines.append("| N/A | N/A | N/A |")
    
    for item in sensitivity_data:
        interval = item.get("interval", "N/A")
        rate = item.get("pass_rate")
        delta = item.get("delta")
        
        if rate is not None:
            rate_str = f"{rate:.2%}"
        else:
            rate_str = "N/A"
        
        if delta is not None:
            delta_str = f"{delta:+.2%}"
        else:
            delta_str = "N/A"
        
        report_lines.append(f"| {interval} | {rate_str} | {delta_str} |")

    report_lines.extend([
        "",
        "## Conclusion",
        "",
        "This report summarizes the effectiveness of the context-checkpointing intervention.",
        "Statistical significance was determined using McNemar's test."
    ])

    report_content = "\n".join(report_lines)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Report generated at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate final markdown report")
    parser.add_argument("--stats", type=str, required=True, help="Stats JSON file path")
    parser.add_argument("--sensitivity", type=str, required=True, help="Sensitivity JSON file path")
    parser.add_argument("--output", type=str, required=True, help="Output markdown file path")
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not os.path.exists(args.stats):
        logger.error(f"Stats file not found: {args.stats}")
        sys.exit(1)
    if not os.path.exists(args.sensitivity):
        logger.error(f"Sensitivity file not found: {args.sensitivity}")
        sys.exit(1)

    try:
        stats = load_json(args.stats)
        sensitivity = load_json(args.sensitivity)
        
        generate_markdown_report(stats, sensitivity, args.output)
        logger.info("Report generation completed successfully.")
        sys.exit(0)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input files: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()