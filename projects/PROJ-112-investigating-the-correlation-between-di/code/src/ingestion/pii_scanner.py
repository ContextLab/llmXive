"""
PII Scanner Module for llmXive Project.

This module provides functionality to scan data files for Personally Identifiable
Information (PII) patterns and calculate SHA256 checksums for artifact verification.
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Configure logger
from src.utils.logger import get_logger

logger = get_logger(__name__)

# PII Patterns to detect
PII_PATTERNS = {
    'email': re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
    'phone': re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'date_of_birth': re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'),
    'url': re.compile(r'https?://[^\s]+'),
    'username': re.compile(r'\b(?:user|name|login|account|id|identifier)[\s=:]+["\']?[\w\s]+["\']?', re.IGNORECASE),
}

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    current_path = Path(__file__).resolve()
    # Traverse up to find 'code' directory, then project root
    for parent in current_path.parents:
        if parent.name == 'code':
            return parent.parent
    # Fallback: assume current working directory is project root
    return Path.cwd()

def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        SHA256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()

def scan_for_pii(file_path: Path) -> Dict[str, List[str]]:
    """
    Scan a file for PII patterns.

    Args:
        file_path: Path to the file to scan.

    Returns:
        Dictionary mapping PII type to list of found matches.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    findings: Dict[str, List[str]] = {pattern_name: [] for pattern_name in PII_PATTERNS}

    try:
        # Try to read as text (UTF-8)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Read line by line to handle large files
            for line_num, line in enumerate(f, 1):
                for pattern_name, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(line)
                    if matches:
                        # Limit matches per line to avoid huge logs
                        for match in matches[:5]:  # First 5 matches per pattern per line
                            findings[pattern_name].append(f"Line {line_num}: {match}")
    except Exception as e:
        logger.warning(f"Error reading file {file_path}: {e}")
        # If binary or unreadable, try binary scan for text patterns
        with open(file_path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern_name, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(line)
                    if matches:
                        for match in matches[:5]:
                            findings[pattern_name].append(f"Line {line_num}: {match}")

    # Remove empty lists
    findings = {k: v for k, v in findings.items() if v}
    return findings

def validate_no_pii(scan_results: Dict[str, List[str]]) -> bool:
    """
    Validate that no PII was found.

    Args:
        scan_results: Dictionary of PII findings.

    Returns:
        True if no PII found, False otherwise.
    """
    total_matches = sum(len(v) for v in scan_results.values())
    return total_matches == 0

def record_checksums(
    files: List[Path],
    output_path: Path,
    existing_hashes: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Calculate checksums for a list of files and save to a JSON file.

    Args:
        files: List of file paths to checksum.
        output_path: Path to the output JSON file.
        existing_hashes: Optional dictionary of existing hashes to merge.

    Returns:
        Dictionary of file paths to checksums.
    """
    checksums = existing_hashes.copy() if existing_hashes else {}

    for file_path in files:
        if file_path.exists():
            try:
                checksum = calculate_file_checksum(file_path)
                # Store relative path for portability
                rel_path = str(file_path.relative_to(get_project_root()))
                checksums[rel_path] = checksum
                logger.info(f"Calculated checksum for {rel_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        else:
            logger.warning(f"File not found, skipping checksum: {file_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksums saved to {output_path}")
    return checksums

def run_pii_scan_and_checksums(
    input_files: List[Path],
    output_report_path: Path,
    output_checksums_path: Path,
    existing_checksums: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Run PII scan on input files and calculate checksums.

    Args:
        input_files: List of file paths to scan.
        output_report_path: Path to write the PII scan report.
        output_checksums_path: Path to write the checksums JSON.
        existing_checksums: Optional existing checksums to merge.

    Returns:
        Tuple of (PII report dictionary, checksums dictionary).
    """
    all_findings: Dict[str, Any] = {
        "scan_timestamp": str(Path.cwd()),  # Placeholder for actual timestamp
        "files_scanned": [],
        "total_pii_matches": 0,
        "pii_by_type": {},
        "pii_found": 0
    }

    checksums = existing_checksums.copy() if existing_checksums else {}

    for file_path in input_files:
        if not file_path.exists():
            logger.warning(f"Skipping non-existent file: {file_path}")
            continue

        rel_path = str(file_path.relative_to(get_project_root()))
        all_findings["files_scanned"].append(rel_path)

        # Scan for PII
        try:
            findings = scan_for_pii(file_path)
            file_match_count = sum(len(v) for v in findings.values())
            all_findings["total_pii_matches"] += file_match_count

            if findings:
                all_findings["pii_by_type"][rel_path] = findings
                all_findings["pii_found"] += file_match_count
                logger.warning(f"PII found in {rel_path}: {file_match_count} matches")
            else:
                logger.info(f"No PII found in {rel_path}")

        except Exception as e:
            logger.error(f"Error scanning {file_path}: {e}")
            all_findings["errors"] = all_findings.get("errors", [])
            all_findings["errors"].append({"file": rel_path, "error": str(e)})

        # Calculate checksum
        try:
            checksum = calculate_file_checksum(file_path)
            checksums[rel_path] = checksum
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {e}")

    # Write PII report
    output_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, 'w', encoding='utf-8') as f:
        json.dump(all_findings, f, indent=2)
    logger.info(f"PII scan report saved to {output_report_path}")

    # Write checksums
    record_checksums(input_files, output_checksums_path, checksums)

    return all_findings, checksums

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for the PII scanner."""
    parser = argparse.ArgumentParser(
        description="Scan data files for PII and calculate artifact checksums."
    )
    parser.add_argument(
        "--input-files",
        nargs="+",
        required=True,
        help="Paths to input files to scan (e.g., data/raw/agp_raw.tsv)."
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default="data/processed/results/pii_scan_report.json",
        help="Path to write the PII scan report (default: data/processed/results/pii_scan_report.json)."
    )
    parser.add_argument(
        "--output-checksums",
        type=Path,
        default="state/artifact_hashes.json",
        help="Path to write the checksums JSON (default: state/artifact_hashes.json)."
    )
    return parser

def main() -> int:
    """
    Main entry point for the PII scanner.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    # Convert input paths to absolute paths relative to project root
    project_root = get_project_root()
    input_files = [project_root / Path(p) for p in args.input_files]
    output_report = project_root / args.output_report
    output_checksums = project_root / args.output_checksums

    # Load existing checksums if they exist
    existing_checksums = None
    if output_checksums.exists():
        try:
            with open(output_checksums, 'r', encoding='utf-8') as f:
                existing_checksums = json.load(f)
            logger.info(f"Loaded existing checksums from {output_checksums}")
        except Exception as e:
            logger.warning(f"Could not load existing checksums: {e}")

    try:
        report, checksums = run_pii_scan_and_checksums(
            input_files=input_files,
            output_report_path=output_report,
            output_checksums_path=output_checksums,
            existing_checksums=existing_checksums
        )

        # Verify no PII
        if report["pii_found"] > 0:
            logger.error(f"PII detected! Total matches: {report['pii_found']}")
            return 1

        logger.info("PII scan completed successfully. No PII found.")
        return 0

    except Exception as e:
        logger.error(f"PII scan failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
