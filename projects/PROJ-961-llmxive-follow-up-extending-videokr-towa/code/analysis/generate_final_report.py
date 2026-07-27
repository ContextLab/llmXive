"""
Final Report Aggregation for llmXive VideoKR Follow-up Project.

This script aggregates all outputs from User Story 1 (Data Ingestion),
User Story 2 (Accuracy Stratification), User Story 3 (Sensitivity Analysis),
and the infrastructure logs (Runtime, Memory, Methodology Override) into a
single, comprehensive Markdown report.

Output: data/processed/final_report.md
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import utilities from the project structure
from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if it doesn't exist or is invalid."""
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return None


def load_markdown_file(file_path: Path) -> Optional[str]:
    """Safely load a Markdown file content."""
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return None


def format_table_row(headers: List[str], values: List[Any]) -> str:
    """Format a row for a Markdown table."""
    return "| " + " | ".join(str(v) for v in values) + " |"


def generate_final_report() -> str:
    """
    Aggregate all data sources into a single Markdown report string.
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"

    # --- Section 1: Title and Introduction ---
    report_lines = [
        "# Final Report: VideoKR Reasoning Threshold Analysis",
        "",
        "**Project**: llmXive Follow-up: Extending VideoKR",
        "**Date**: " + str(Path(__file__).stat().st_mtime),
        "**Status**: Complete",
        "",
        "This report aggregates the findings from the automated science pipeline, "
        "analyzing the relationship between structural chain length (hops) and "
        "reasoning accuracy in the VideoKR-SFT dataset.",
        "",
        "---",
        ""
    ]

    # --- Section 2: Methodology Override (T034) ---
    logger.info("Loading Methodology Override...")
    method_override_path = processed_dir / "methodology_override.md"
    method_content = load_markdown_file(method_override_path)
    
    if method_content:
        report_lines.append("## Methodology Note")
        report_lines.append("")
        report_lines.append(method_content.strip())
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
    else:
        logger.warning("Methodology override file missing. Skipping section.")

    # --- Section 3: Data Ingestion Summary (US1 - T013b, T016) ---
    logger.info("Loading Data Ingestion Coverage...")
    coverage_path = processed_dir / "annotation_coverage.json"
    coverage_data = load_json_file(coverage_path)
    
    if coverage_data:
        report_lines.append("## Data Ingestion & Annotation Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Input Records**: {coverage_data.get('total_input_records', 'N/A')}")
        report_lines.append(f"- **Unresolvable Records**: {coverage_data.get('unresolvable_count', 'N/A')}")
        report_lines.append(f"- **Successfully Annotated**: {coverage_data.get('annotated_count', 'N/A')}")
        report_lines.append(f"- **Annotation Coverage**: {coverage_data.get('proportion', 'N/A'):.2%}")
        report_lines.append("")
        
        # Check for state file hash (T016)
        state_path = project_root / "state" / "projects" / "PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml"
        if state_path.exists():
            report_lines.append(f"- **Data Artifact Hash**: See `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`")
            report_lines.append("")
    else:
        report_lines.append("## Data Ingestion & Annotation Summary")
        report_lines.append("")
        report_lines.append("*Coverage data unavailable.*")
        report_lines.append("")

    # --- Section 4: Accuracy Stratification & Threshold Detection (US2 - T023, T022b, T022c) ---
    logger.info("Loading Threshold Detection Results...")
    threshold_path = processed_dir / "threshold_results.json"
    threshold_data = load_json_file(threshold_path)
    
    report_lines.append("## Accuracy Stratification & Threshold Detection")
    report_lines.append("")
    
    if threshold_data:
        report_lines.append("### Change-Point Analysis (Permutation Test)")
        report_lines.append("")
        report_lines.append(f"- **Optimal Knot Location (Hop)**: {threshold_data.get('optimal_knot', 'N/A')}")
        report_lines.append(f"- **Raw P-Value**: {threshold_data.get('p_value', 'N/A')}")
        report_lines.append(f"- **Bonferroni Corrected P-Value**: {threshold_data.get('p_corrected', 'N/A')}")
        report_lines.append(f"- **Alpha Threshold**: {threshold_data.get('alpha', 0.05)}")
        report_lines.append(f"- **Statistically Significant**: {threshold_data.get('is_significant', 'N/A')}")
        report_lines.append(f"- **Conclusion**: {threshold_data.get('conclusion', 'N/A')}")
        report_lines.append("")
        
        if threshold_data.get('effect_size'):
            report_lines.append(f"- **Effect Size (Accuracy Drop)**: {threshold_data['effect_size']:.4f}")
            report_lines.append("")
    else:
        report_lines.append("*Threshold detection results unavailable.*")
        report_lines.append("")

    # --- Section 5: Sensitivity Analysis (US3 - T028a, T028b) ---
    logger.info("Loading Sensitivity Analysis Results...")
    sensitivity_path = processed_dir / "sensitivity_report.md"
    sensitivity_content = load_markdown_file(sensitivity_path)
    
    stability_path = processed_dir / "stability_metric.json"
    stability_data = load_json_file(stability_path)

    report_lines.append("## Sensitivity Analysis of Threshold Definition")
    report_lines.append("")
    
    if sensitivity_content:
        report_lines.append(sensitivity_content.strip())
        report_lines.append("")
    
    if stability_data:
        report_lines.append("### Robustness Metric")
        report_lines.append("")
        report_lines.append(f"- **Significant Thresholds Count**: {stability_data.get('significant_count', 'N/A')}")
        report_lines.append(f"- **Robustness Status**: {stability_data.get('robustness_status', 'N/A')}")
        report_lines.append("")
    else:
        report_lines.append("*Sensitivity analysis results unavailable.*")
        report_lines.append("")

    # --- Section 6: Infrastructure & Performance (T035, T036) ---
    logger.info("Loading Runtime and Memory Logs...")
    runtime_path = processed_dir / "runtime_log.json"
    runtime_data = load_json_file(runtime_path)
    
    memory_path = processed_dir / "memory_log.json"
    memory_data = load_json_file(memory_path)

    report_lines.append("## Infrastructure & Performance Metrics")
    report_lines.append("")
    
    if runtime_data:
        report_lines.append(f"- **Total Pipeline Runtime**: {runtime_data.get('total_runtime_seconds', 'N/A'):.2f} seconds")
        if 'limit_exceeded' in runtime_data:
            status = "EXCEEDED" if runtime_data['limit_exceeded'] else "OK"
            report_lines.append(f"- **CI Time Limit Status**: {status}")
        report_lines.append("")
    
    if memory_data:
        report_lines.append(f"- **Peak Memory Usage**: {memory_data.get('peak_memory_gb', 'N/A'):.2f} GB")
        if 'limit_exceeded' in memory_data:
            status = "EXCEEDED" if memory_data['limit_exceeded'] else "OK"
            report_lines.append(f"- **7GB Memory Limit Status**: {status}")
        report_lines.append("")

    # --- Section 7: Visual Artifacts ---
    report_lines.append("## Generated Visual Artifacts")
    report_lines.append("")
    report_lines.append("The following plots were generated and saved to `data/processed/`:")
    report_lines.append("")
    report_lines.append("- `accuracy_vs_hop_raw.png`: Continuous scatter plot with LOESS trend.")
    report_lines.append("- `accuracy_binned.png`: Bar plot of accuracy by hop bin.")
    report_lines.append("- `sensitivity_overlay.png`: Overlay of accuracy curves for different thresholds.")
    report_lines.append("")

    # --- Footer ---
    report_lines.append("---")
    report_lines.append("*Report generated automatically by `code/analysis/generate_final_report.py`.*")

    return "\n".join(report_lines)


def main():
    """Main entry point for the Final Report Aggregation."""
    logger.info("Starting Final Report Aggregation (T037)...")
    
    try:
        # Generate the report content
        report_content = generate_final_report()
        
        # Define output path
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "final_report.md"
        
        ensure_dir(output_path.parent)
        
        # Write the report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Final report successfully written to: {output_path}")
        print(f"Success: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate final report: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()