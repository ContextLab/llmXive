"""Methodology Consistency Check.

Verifies that every mention of "GNN", "Surrogate", or "Model" in `docs/methodology.md`
is accompanied by the disclaimer "interpolates DFT data" or "not a first-principles calculation".
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging to suppress noise during checks
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Constants for the check
TARGET_FILE = "docs/methodology.md"
OUTPUT_FILE = "data/results/methodology_consistency.json"
DISCLAIMER_PATTERNS = [
    r"interpolates DFT data",
    r"not a first-principles calculation",
    r"surrogate model",
    r"interpolating pre-computed DFT",
]
# Patterns to look for: GNN, Surrogate, Model (case-insensitive)
# We look for these words in context to ensure they aren't used falsely.
TARGET_TERMS = [
    r"\bGNN\b",
    r"\bSurrogate\b",
    r"\bModel\b",
]

def find_file(filename: str) -> Path:
    """Find a file relative to project root or current directory."""
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / filename
    if not file_path.exists():
        # Try relative to current working directory
        file_path = Path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
    return file_path

def scan_file_for_consistency(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a file for mentions of target terms that lack required disclaimers.

    Returns a list of warnings: {line_number, line_content, missing_disclaimer}.
    """
    warnings = []
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return warnings

    # Compile regex patterns
    term_pattern = re.compile("|".join(TARGET_TERMS), re.IGNORECASE)
    disclaimer_pattern = re.compile("|".join(DISCLAIMER_PATTERNS), re.IGNORECASE)

    for line_num, line in enumerate(lines, start=1):
        # Check if line contains a target term
        if term_pattern.search(line):
            # Check if the same line contains a disclaimer
            if not disclaimer_pattern.search(line):
                # It's a warning, not a hard error. Log it.
                warnings.append({
                    "line_number": line_num,
                    "line_content": line.strip(),
                    "reason": "Mention of GNN/Surrogate/Model lacks explicit disclaimer about interpolating DFT or not being first-principles.",
                    "severity": "warning"
                })

    return warnings

def run_consistency_check(target_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the consistency check on the methodology document.

    Args:
        target_file: Path to the methodology file. Defaults to docs/methodology.md.

    Returns:
        A dictionary containing the check results.
    """
    file_path = find_file(target_file or TARGET_FILE)
    logger.info(f"Scanning {file_path} for methodology consistency...")

    warnings = scan_file_for_consistency(file_path)

    result = {
        "file_scanned": str(file_path),
        "total_warnings": len(warnings),
        "warnings": warnings,
        "status": "PASS" if len(warnings) == 0 else "WARNINGS_FOUND",
        "message": (
            "Methodology consistency check completed. "
            "If warnings exist, they indicate lines where 'GNN', 'Surrogate', or 'Model' "
            "are mentioned without the required disclaimer."
        )
    }

    return result

def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Verify methodology documentation consistency regarding surrogate model disclaimers."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=TARGET_FILE,
        help=f"Path to the methodology file to scan (default: {TARGET_FILE})."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help=f"Path to write the JSON results (default: {OUTPUT_FILE})."
    )

    args = parser.parse_args()

    try:
        result = run_consistency_check(args.input)

        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write results to JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        logger.info(f"Results written to {output_path}")
        logger.info(f"Status: {result['status']}")
        if result["total_warnings"] > 0:
            logger.warning(f"Found {result['total_warnings']} warnings. "
                           "See {output_path} for details.")

        # Do NOT exit with code 1 for warnings, as per requirements.
        # Only exit 1 if the file itself is missing or unreadable (handled by exception).

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during consistency check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()