"""Feynman Quote Verification Utility.

Scans all generated reports in data/results/ for the mandatory
Scientific Integrity quote by Richard Feynman.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# The exact quote required by T046, T055, and this task (T059)
FEYNMAN_QUOTE = "The first principle is that you must not fool yourself — and you are the easiest person to fool."

# Directories to scan
RESULTS_DIR = Path("data/results")

# File patterns to scan
SCAN_PATTERNS = ["*.md", "*.json", "*.txt"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def scan_file_for_quote(file_path: Path) -> bool:
    """Scan a single file for the Feynman quote.

    Args:
        file_path: Path to the file to scan.

    Returns:
        True if the quote is found, False otherwise.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            return FEYNMAN_QUOTE in content
    except UnicodeDecodeError:
        # Skip binary files (e.g., .parquet, .pt)
        logger.debug(f"Skipping binary file: {file_path}")
        return False
    except Exception as e:
        logger.warning(f"Error reading {file_path}: {e}")
        return False


def scan_directory(directory: Path, patterns: List[str]) -> List[Dict[str, Any]]:
    """Scan all matching files in a directory for the quote.

    Args:
        directory: The directory to scan.
        patterns: List of glob patterns (e.g., ["*.md", "*.json"]).

    Returns:
        A list of dicts with 'path', 'found', and 'error' keys.
    """
    results = []
    if not directory.exists():
        logger.error(f"Results directory not found: {directory}")
        return [{"path": str(directory), "found": False, "error": "Directory not found"}]

    for pattern in patterns:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                found = scan_file_for_quote(file_path)
                results.append({
                    "path": str(file_path),
                    "found": found,
                    "error": None
                })
                if found:
                    logger.info(f"Found quote in: {file_path}")
                else:
                    logger.warning(f"Missing quote in: {file_path}")

    return results


def run_verification() -> int:
    """Run the verification and return exit code.

    Returns:
        0 if all files contain the quote, 1 otherwise.
    """
    logger.info(f"Scanning {RESULTS_DIR} for Feynman quote...")
    logger.info(f"Quote: \"{FEYNMAN_QUOTE}\"")

    results = scan_directory(RESULTS_DIR, SCAN_PATTERNS)

    if not results:
        logger.warning("No files found to scan.")
        # If no files exist, we cannot verify compliance.
        # Depending on strictness, this might be a failure.
        # For now, we assume if there are no reports yet, we fail.
        return 1

    missing_files = [r["path"] for r in results if not r["found"]]

    if missing_files:
        logger.error(f"FAILED: The Feynman quote is missing in {len(missing_files)} file(s):")
        for f in missing_files:
            logger.error(f"  - {f}")
        return 1

    logger.info("SUCCESS: All scanned reports contain the Feynman quote.")
    return 0


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Verify Feynman quote presence in generated reports."
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=str(RESULTS_DIR),
        help="Path to the results directory to scan."
    )
    parser.add_argument(
        "--patterns",
        type=str,
        nargs="+",
        default=SCAN_PATTERNS,
        help="Glob patterns for files to scan (e.g., *.md *.json)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write a JSON audit report."
    )

    args = parser.parse_args()

    # Override defaults if provided
    scan_dir = Path(args.results_dir)
    patterns = args.patterns

    results = scan_directory(scan_dir, patterns)

    # Write audit report if requested
    if args.output:
        report = {
            "status": "PASS" if all(r["found"] for r in results) else "FAIL",
            "scanned_files": len(results),
            "missing_files": [r["path"] for r in results if not r["found"]],
            "quote": FEYNMAN_QUOTE
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Audit report written to {args.output}")

    exit_code = 0 if all(r["found"] for r in results) else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()