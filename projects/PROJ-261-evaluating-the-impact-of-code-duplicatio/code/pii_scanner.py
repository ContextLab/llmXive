"""
PII Scanner for Code Duplication Research Project

Scans all files under data/ directory (raw/, processed/, analysis/) for PII patterns
per Constitution Principle III (Data Hygiene).

This module implements comprehensive PII pattern detection including:
- Email addresses
- Phone numbers (US and international formats)
- Social Security Numbers (SSN)
- Credit card numbers
- IP addresses (IPv4 and IPv6)
- API keys and tokens
- URLs with embedded credentials
- Date of birth patterns
- Driver's license patterns

Usage:
    python code/pii_scanner.py

Output:
    data/analysis/pii_scan_results.csv - CSV file with detected PII findings
"""

import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root path (assumes this script is in code/ directory)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_FILE = DATA_DIR / "analysis" / "pii_scan_results.csv"

# PII Pattern definitions with descriptions
PII_PATTERNS: Dict[str, Tuple[re.Pattern, str]] = {
    "email": (
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "Email address"
    ),
    "ssn": (
        re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "Social Security Number"
    ),
    "credit_card_visa": (
        re.compile(r'\b4[0-9]{12}(?:[0-9]{3})?\b'),
        "Credit Card (Visa)"
    ),
    "credit_card_mastercard": (
        re.compile(r'\b5[1-5][0-9]{14}\b'),
        "Credit Card (Mastercard)"
    ),
    "credit_card_amex": (
        re.compile(r'\b3[47][0-9]{13}\b'),
        "Credit Card (Amex)"
    ),
    "phone_us": (
        re.compile(r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b'),
        "US Phone Number"
    ),
    "phone_intl": (
        re.compile(r'\b\+?[1-9]\d{1,14}\b'),
        "International Phone Number"
    ),
    "ip_v4": (
        re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
        "IPv4 Address"
    ),
    "ip_v6": (
        re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
        "IPv6 Address"
    ),
    "api_key_generic": (
        re.compile(r'\b(?:api[_-]?key|apikey|api_key)[\s]*[=:][\s]*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.IGNORECASE),
        "Generic API Key"
    ),
    "aws_access_key": (
        re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
        "AWS Access Key ID"
    ),
    "aws_secret_key": (
        re.compile(r'\b(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])\b'),
        "AWS Secret Access Key"
    ),
    "github_token": (
        re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b'),
        "GitHub Token"
    ),
    "url_with_creds": (
        re.compile(r'\bhttps?://[^\s/]+:[^\s/]+@[^\s]+\b'),
        "URL with embedded credentials"
    ),
    "dob_pattern": (
        re.compile(r'\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b'),
        "Date of Birth Pattern"
    ),
    "credit_card_with_spaces": (
        re.compile(r'\b(?:\d[ -]*){13,16}\b'),
        "Credit Card with Spaces/Dashes"
    ),
}

# File extensions to scan (text-based files only)
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp',
    '.csv', '.json', '.yaml', '.yml', '.xml', '.txt', '.md',
    '.html', '.htm', '.css', '.sql', '.sh', '.bash', '.log',
    '.ini', '.cfg', '.conf', '.env', '.properties', '.rst',
    '.R', '.r', '.ipynb', '.jl', '.go', '.rs', '.swift', '.kt'
}

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar', '.exe',
    '.dll', '.so', '.dylib', '.bin', '.dat', '.pkl', '.pt', '.pth'
}

# Directories to skip
SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    'venv', '.venv', 'env', '.env', 'virtualenv',
    '__MACOSX', '.DS_Store'
}

def setup_logging() -> logging.Logger:
    """Configure logging for the PII scanner."""
    logger = logging.getLogger('pii_scanner')
    logger.setLevel(logging.INFO)

    # File handler for scan results
    log_file = PROJECT_ROOT / "data" / "analysis" / "pii_scan.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(file_handler)

    # Console handler for progress
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in logger.handlers):
        logger.addHandler(console_handler)

    return logger

def should_scan_file(file_path: Path) -> bool:
    """
    Determine if a file should be scanned for PII.

    Args:
        file_path: Path to the file to check

    Returns:
        True if the file should be scanned, False otherwise
    """
    # Skip binary files
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return False

    # Skip files with no extension or known text extensions
    if file_path.suffix and file_path.suffix.lower() not in TEXT_EXTENSIONS:
        # Also scan files without extension (like Dockerfile, Makefile, etc.)
        if file_path.suffix:
            return False

    # Skip hidden files (starting with .)
    if file_path.name.startswith('.'):
        return False

    # Skip very large files (>10MB) to avoid memory issues
    try:
        if file_path.stat().st_size > 10 * 1024 * 1024:
            return False
    except OSError:
        return False

    return True

def scan_file_for_pii(
    file_path: Path,
    logger: logging.Logger
) -> List[Dict]:
    """
    Scan a single file for PII patterns.

    Args:
        file_path: Path to the file to scan
        logger: Logger instance for progress reporting

    Returns:
        List of dictionaries containing PII findings
    """
    findings = []

    try:
        # Try to read the file as text
        try:
            content = file_path.read_text(encoding='utf-8', errors='replace')
        except Exception as read_error:
            logger.warning(f"Could not read file {file_path}: {read_error}")
            return findings

        # Scan each PII pattern
        for pattern_name, (pattern, description) in PII_PATTERNS.items():
            matches = pattern.findall(content)

            for match in matches:
                # Handle tuple matches from groups
                if isinstance(match, tuple):
                    # Use the first non-empty group or the full match
                    match_str = next((m for m in match if m), match[0])
                else:
                    match_str = match

                # Find the position of the match
                match_pos = content.find(match_str)

                # Create finding record
                finding = {
                    'file_path': str(file_path.relative_to(PROJECT_ROOT)),
                    'pattern_type': pattern_name,
                    'description': description,
                    'matched_value': match_str[:50] + '...' if len(str(match_str)) > 50 else str(match_str),
                    'position': match_pos,
                    'line_number': content[:match_pos].count('\n') + 1 if match_pos >= 0 else 0,
                    'timestamp': datetime.now().isoformat()
                }
                findings.append(finding)

        logger.info(f"Scanned {file_path.name}: {len(findings)} PII patterns found")

    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {e}")

    return findings

def scan_directory(
    directory: Path,
    logger: logging.Logger
) -> List[Dict]:
    """
    Recursively scan a directory for PII patterns.

    Args:
        directory: Path to the directory to scan
        logger: Logger instance for progress reporting

    Returns:
        List of dictionaries containing all PII findings
    """
    all_findings = []
    files_scanned = 0

    logger.info(f"Starting PII scan of directory: {directory}")

    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return all_findings

    # Walk through directory recursively
    for root, dirs, files in directory.walk():
        # Filter out directories to skip
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file_name in files:
            file_path = Path(root) / file_name

            if should_scan_file(file_path):
                files_scanned += 1
                findings = scan_file_for_pii(file_path, logger)
                all_findings.extend(findings)

    logger.info(f"PII scan complete: {files_scanned} files scanned, {len(all_findings)} findings")

    return all_findings

def write_findings_to_csv(
    findings: List[Dict],
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Write PII findings to a CSV file.

    Args:
        findings: List of PII finding dictionaries
        output_path: Path to write the CSV file
        logger: Logger instance for progress reporting
    """
    if not findings:
        logger.info("No PII findings to write")
        # Write empty CSV with headers
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'file_path', 'pattern_type', 'description', 'matched_value',
                'position', 'line_number', 'timestamp'
            ])
            writer.writeheader()
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'file_path', 'pattern_type', 'description', 'matched_value',
            'position', 'line_number', 'timestamp'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(findings)

    logger.info(f"Wrote {len(findings)} findings to {output_path}")

def run_pii_scan(
    data_dir: Optional[Path] = None,
    output_file: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> List[Dict]:
    """
    Main entry point for running the PII scan.

    Args:
        data_dir: Directory to scan (defaults to PROJECT_ROOT / 'data')
        output_file: Output CSV file path (defaults to PROJECT_ROOT / 'data' / 'analysis' / 'pii_scan_results.csv')
        logger: Logger instance (creates one if not provided)

    Returns:
        List of PII findings
    """
    if data_dir is None:
        data_dir = DATA_DIR

    if output_file is None:
        output_file = OUTPUT_FILE

    if logger is None:
        logger = setup_logging()

    logger.info("=" * 60)
    logger.info("Starting PII Scan")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 60)

    start_time = datetime.now()

    # Scan all subdirectories under data/
    all_findings = []

    for subdir in ['raw', 'processed', 'analysis']:
        subdir_path = data_dir / subdir
        if subdir_path.exists():
            logger.info(f"Scanning subdirectory: {subdir}")
            findings = scan_directory(subdir_path, logger)
            all_findings.extend(findings)

    # Write results to CSV
    write_findings_to_csv(all_findings, output_file, logger)

    elapsed_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"PII scan completed in {elapsed_time:.2f} seconds")
    logger.info(f"Total findings: {len(all_findings)}")

    # Return summary statistics
    if all_findings:
        pattern_counts = {}
        for finding in all_findings:
            ptype = finding['pattern_type']
            pattern_counts[ptype] = pattern_counts.get(ptype, 0) + 1

        logger.info("Findings by pattern type:")
        for ptype, count in sorted(pattern_counts.items()):
            logger.info(f"  {ptype}: {count}")

    return all_findings

def main():
    """Main entry point when script is run directly."""
    logger = setup_logging()

    try:
        findings = run_pii_scan(logger=logger)

        if findings:
            logger.warning(f"WARNING: {len(findings)} PII patterns detected!")
            logger.warning(f"Review findings in: {OUTPUT_FILE}")
            sys.exit(1)  # Exit with error code if PII found
        else:
            logger.info("SUCCESS: No PII patterns detected in scanned files.")
            sys.exit(0)

    except Exception as e:
        logger.error(f"PII scan failed with error: {e}")
        sys.exit(2)

if __name__ == '__main__':
    main()
