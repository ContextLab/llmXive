"""
Exclusion Reporter Module

Aggregates exclusion logs from the metric extraction phase (T020)
into a human-readable Markdown summary report for research transparency.
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExclusionReporterError(Exception):
    """Custom exception for exclusion reporting errors."""
    pass


def load_exclusion_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load the exclusion log JSON file.

    Args:
        log_path: Path to the exclusion_log.json file.

    Returns:
        List of exclusion records.

    Raises:
        ExclusionReporterError: If file not found or invalid JSON.
    """
    if not log_path.exists():
        raise ExclusionReporterError(f"Exclusion log not found at {log_path}")

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ExclusionReporterError("Exclusion log must be a JSON list of records")
            return data
    except json.JSONDecodeError as e:
        raise ExclusionReporterError(f"Invalid JSON in exclusion log: {e}")


def count_exclusions_by_reason(exclusions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count exclusions grouped by exclusion reason.

    Args:
        exclusions: List of exclusion records.

    Returns:
        Dictionary mapping exclusion reason to count.
    """
    counts: Dict[str, int] = {}
    for record in exclusions:
        reason = record.get('exclusion_reason', 'Unknown')
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def calculate_total_traces(training_dir: Path, held_out_dir: Path) -> int:
    """
    Calculate the total number of trace files in the dataset directories.

    Args:
        training_dir: Path to data/training/
        held_out_dir: Path to data/held_out/

    Returns:
        Total count of .json files.
    """
    count = 0
    for directory in [training_dir, held_out_dir]:
        if directory.exists():
            count += len(list(directory.glob('*.json')))
    return count


def generate_markdown_report(
    total_traces: int,
    exclusions: List[Dict[str, Any]],
    counts_by_reason: Dict[str, int],
    output_path: Path
) -> None:
    """
    Generate a human-readable Markdown summary report.

    Args:
        total_traces: Total number of traces scanned.
        exclusions: Full list of exclusion records.
        counts_by_reason: Aggregated counts by reason.
        output_path: Path to write the markdown report.
    """
    excluded_count = len(exclusions)
    valid_count = total_traces - excluded_count
    exclusion_percentage = (excluded_count / total_traces * 100) if total_traces > 0 else 0.0

    lines = [
        "# Exclusion Summary Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Dataset Overview",
        "",
        f"- **Total Traces Scanned:** {total_traces}",
        f"- **Excluded Traces:** {excluded_count}",
        f"- **Valid Traces:** {valid_count}",
        f"- **Exclusion Rate:** {exclusion_percentage:.2f}%",
        "",
        "## Reasons for Exclusion",
        "",
    ]

    if not counts_by_reason:
        lines.append("*No exclusions recorded.*")
    else:
        lines.append("| Reason | Count | Percentage |")
        lines.append("| :--- | :--- | :--- |")
        for reason, count in sorted(counts_by_reason.items(), key=lambda x: x[1], reverse=True):
            pct = (count / excluded_count * 100) if excluded_count > 0 else 0.0
            lines.append(f"| {reason} | {count} | {pct:.2f}% |")

    lines.extend([
        "",
        "## Detailed Exclusion Log",
        "",
        "The following traces were excluded during the metric extraction phase:",
        ""
    ])

    if exclusions:
        lines.append("| Trace ID | Reason | Timestamp |")
        lines.append("| :--- | :--- | :--- |")
        for record in exclusions:
            trace_id = record.get('trace_id', 'N/A')
            reason = record.get('exclusion_reason', 'Unknown')
            timestamp = record.get('timestamp', 'N/A')
            lines.append(f"| {trace_id} | {reason} | {timestamp} |")
    else:
        lines.append("*No traces were excluded.*")

    lines.extend([
        "",
        "---",
        "",
        "*This report is automatically generated to ensure transparency in data processing for the research paper.*"
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Exclusion summary report written to {output_path}")


def run_exclusion_report(
    exclusion_log_path: Optional[Path] = None,
    training_dir: Optional[Path] = None,
    held_out_dir: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main orchestration function to run the exclusion reporting pipeline.

    Args:
        exclusion_log_path: Path to exclusion_log.json. Defaults to data/processed/exclusion_log.json.
        training_dir: Path to training traces. Defaults to data/training/.
        held_out_dir: Path to held-out traces. Defaults to data/held_out/.
        output_path: Path for the output markdown. Defaults to data/processed/exclusion_summary.md.

    Returns:
        Dictionary containing summary statistics.
    """
    # Resolve paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    
    if exclusion_log_path is None:
        exclusion_log_path = project_root / 'data' / 'processed' / 'exclusion_log.json'
    if training_dir is None:
        training_dir = project_root / 'data' / 'training'
    if held_out_dir is None:
        held_out_dir = project_root / 'data' / 'held_out'
    if output_path is None:
        output_path = project_root / 'data' / 'processed' / 'exclusion_summary.md'

    logger.info(f"Loading exclusion log from {exclusion_log_path}")
    exclusions = load_exclusion_log(exclusion_log_path)

    logger.info(f"Calculating total traces in {training_dir} and {held_out_dir}")
    total_traces = calculate_total_traces(training_dir, held_out_dir)

    logger.info("Counting exclusions by reason")
    counts_by_reason = count_exclusions_by_reason(exclusions)

    logger.info(f"Generating markdown report to {output_path}")
    generate_markdown_report(total_traces, exclusions, counts_by_reason, output_path)

    return {
        "total_traces": total_traces,
        "excluded_count": len(exclusions),
        "valid_count": total_traces - len(exclusions),
        "counts_by_reason": counts_by_reason,
        "output_file": str(output_path)
    }


def main() -> None:
    """Entry point for the exclusion reporter script."""
    try:
        result = run_exclusion_report()
        print(json.dumps(result, indent=2))
        logger.info("Exclusion reporting completed successfully.")
    except ExclusionReporterError as e:
        logger.error(f"Exclusion reporting failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()