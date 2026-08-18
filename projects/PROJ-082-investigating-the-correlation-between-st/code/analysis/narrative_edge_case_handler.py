"""
Narrative Edge Case Handler: Zero-Studies Logic

This module implements the specific handling for the "zero studies" edge case
(N=0) as mandated by Constitution Principle VII and T015c specifications.
It ensures that when no studies are found, the system outputs a "Data Insufficient"
report rather than attempting a narrative synthesis on empty data.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger

logger = get_logger(__name__)


def load_study_count() -> int:
    """
    Load the study count from data/processed/study_count.json.

    Returns:
        int: The number of studies (N).

    Raises:
        FileNotFoundError: If the study count file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        KeyError: If the 'N' key is missing.
    """
    project_root = get_project_root()
    count_file = project_root / "data" / "processed" / "study_count.json"

    if not count_file.exists():
        raise FileNotFoundError(
            f"Study count file not found: {count_file}. "
            "Run T014a (study_counter) first."
        )

    with open(count_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'N' not in data:
        raise KeyError(f"'N' key missing in {count_file}")

    return int(data['N'])


def generate_zero_studies_summary() -> Dict[str, Any]:
    """
    Generate the structured summary for the zero-studies case.

    This function creates the specific "Data Insufficient" report content
    required when N=0. It does NOT attempt to aggregate themes.

    Returns:
        Dict[str, Any]: The summary dictionary containing metadata and content.
    """
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    summary = {
        "study_count": 0,
        "synthesis_mode": "narrative",
        "timestamp": timestamp,
        "status": "data_insufficient",
        "message": "No studies found to perform analysis.",
        "limitation_note": "Systematic Review Fallback: Insufficient data (N=0) for meta-analysis or narrative synthesis.",
        "content": {
            "header": "# No studies found",
            "overview": "The data extraction phase yielded zero eligible studies.",
            "themes": [],
            "limitations": [
                "No quantitative data available.",
                "No qualitative descriptions available.",
                "Analysis cannot proceed due to lack of input data."
            ]
        }
    }
    return summary


def run_zero_case_handler(output_path: Optional[Path] = None) -> Path:
    """
    Execute the zero-studies handling logic.

    1. Reads the study count.
    2. If N == 0, generates the zero-studies summary.
    3. Writes the summary to the output file (default: data/derived/narrative_summary.md).

    Args:
        output_path: Optional path to the output file. Defaults to the project's
                     derived narrative summary path.

    Returns:
        Path: The path to the generated output file.

    Raises:
        FileNotFoundError: If study count is missing.
        ValueError: If study count is not 0 (this handler is for N=0 only).
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "derived" / "narrative_summary.md"

    ensure_directory(output_path)

    try:
        n = load_study_count()
    except FileNotFoundError as e:
        logger.error(f"Failed to load study count: {e}")
        raise

    if n != 0:
        # This handler is specifically for N=0. If N > 0, the standard pipeline applies.
        logger.warning(f"Study count is {n}. Zero-studies handler is not applicable.")
        # We do not raise here, but log. The caller (T016) should ensure this is only called when N=0.
        # However, per strict contract, we return a placeholder or error if logic is violated.
        # For safety, we raise to prevent accidental overwriting of valid reports.
        raise ValueError(f"Zero-studies handler invoked with N={n}. Expected N=0.")

    logger.info("Detected zero studies. Generating Data Insufficient report.")
    summary_data = generate_zero_studies_summary()

    # Write the JSON metadata block at the top, followed by markdown content
    # Format: JSON block (fenced or plain) + Markdown sections
    # Based on T015c spec: "JSON Metadata Block at the top"

    with open(output_path, 'w', encoding='utf-8') as f:
        # Write JSON metadata
        f.write("```json\n")
        json.dump(summary_data, f, indent=2)
        f.write("\n```\n\n")

        # Write Markdown content
        f.write(f"# {summary_data['content']['header']}\n\n")
        f.write(f"**Status:** {summary_data['status']}\n\n")
        f.write(f"**Message:** {summary_data['message']}\n\n")

        f.write("## Study Overview\n\n")
        f.write(f"{summary_data['content']['overview']}\n\n")

        f.write("## Limitations\n\n")
        for limit in summary_data['content']['limitations']:
            f.write(f"- {limit}\n")

        f.write("\n")
        f.write("## Systematic Review Fallback\n\n")
        f.write(f"{summary_data['limitation_note']}\n")

    logger.info(f"Zero-studies report generated at: {output_path}")
    return output_path


def main() -> int:
    """
    Main entry point for the zero-studies handler script.

    Returns:
        int: 0 on success, 1 on failure.
    """
    try:
        run_zero_case_handler()
        return 0
    except Exception as e:
        logger.error(f"Zero-studies handler failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())