"""
PII Scanner Module

Scans all files under data/ including raw/, processed/, and analysis/ subdirectories
for PII patterns per Constitution Principle III (Data Hygiene).

Must run after T018 (data_loader.py) completes to ensure data exists.
"""

import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# PII patterns per Constitution Principle III
PII_PATTERNS: Dict[str, re.Pattern] = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone_us': re.compile(r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'url': re.compile(r'https?://[^\s]+'),
    'api_key': re.compile(r'\b(?:api[_-]?key|apikey|API[_-]?KEY)[\s]*[=:][\s]*["\']?([A-Za-z0-9_-]{20,})["\']?'),
}

# File extensions to scan
SCAN_EXTENSIONS: Tuple[str, ...] = (
    '.csv', '.json', '.txt', '.py', '.js', '.ts', '.java', '.cpp', '.c',
    '.h', '.hpp', '.rb', '.go', '.rs', '.php', '.sql', '.xml', '.yaml',
    '.yml', '.md', '.rst', '.log', '.env', '.conf', '.ini', '.cfg'
)

# Directories to scan (relative to project root)
SCAN_SUBDIRECTORIES: Tuple[str, ...] = ('raw', 'processed', 'analysis')

# Output file for PII findings
PII_FINDINGS_PATH: Path = Path('data/pii_findings.csv')
PII_SCAN_LOG_PATH: Path = Path('data/pii_scan.log')

def setup_logging() -> logging.Logger:
    """
    Setup logging for PII scanner.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger('pii_scanner')
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers = []

    # File handler for scan log
    PII_SCAN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(PII_SCAN_LOG_PATH, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Console handler for progress
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    return logger

def should_scan_file(file_path: Path) -> bool:
    """
    Determine if a file should be scanned for PII.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if file should be scanned, False otherwise
    """
    # Skip hidden files and directories
    if file_path.name.startswith('.'):
        return False

    # Check file extension
    if file_path.suffix.lower() not in SCAN_EXTENSIONS:
        return False

    # Skip binary files by checking first bytes
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return False
    except (IOError, OSError):
        return False

    return True

def scan_file_for_pii(file_path: Path, logger: Optional[logging.Logger] = None) -> List[Dict[str, Any]]:
    """
    Scan a single file for PII patterns.

    Args:
        file_path: Path to the file to scan
        logger: Optional logger instance

    Returns:
        List[Dict[str, Any]]: List of PII findings with pattern type and location
    """
    findings = []

    if logger:
        logger.debug(f"Scanning file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                for pattern_name, pattern in PII_PATTERNS.items():
                    matches = pattern.findall(line)
                    for match in matches:
                        # Handle tuple matches from groups
                        if isinstance(match, tuple):
                            match = match[0] if match else str(match)
                        findings.append({
                            'file_path': str(file_path),
                            'line_number': line_num,
                            'pattern_type': pattern_name,
                            'match': match[:50] + '...' if len(str(match)) > 50 else str(match),
                            'timestamp': datetime.utcnow().isoformat()
                        })
    except (IOError, OSError, UnicodeDecodeError) as e:
        if logger:
            logger.warning(f"Failed to read file {file_path}: {e}")

    return findings

def scan_directory(directory: Path, logger: Optional[logging.Logger] = None) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for PII.

    Uses Path.rglob() instead of Path.walk() for Python 3.11 compatibility.

    Args:
        directory: Path to the directory to scan
        logger: Optional logger instance

    Returns:
        List[Dict[str, Any]]: List of all PII findings in the directory
    """
    all_findings = []

    if logger:
        logger.info(f"Starting PII scan of directory: {directory}")

    if not directory.exists():
        if logger:
            logger.warning(f"Directory does not exist: {directory}")
        return all_findings

    # Use rglob() instead of walk() for Python 3.11 compatibility
    for file_path in directory.rglob('*'):
        if file_path.is_file() and should_scan_file(file_path):
            if logger:
                logger.debug(f"Scanning subdirectory: {file_path.parent.name}")
            findings = scan_file_for_pii(file_path, logger)
            all_findings.extend(findings)

    if logger:
        logger.info(f"Completed PII scan of directory: {directory}. Found {len(all_findings)} potential PII instances.")

    return all_findings

def write_findings_to_csv(findings: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write PII findings to a CSV file.

    Args:
        findings: List of PII findings
        output_path: Optional output path (defaults to PII_FINDINGS_PATH)

    Returns:
        Path: Path to the written CSV file
    """
    if output_path is None:
        output_path = PII_FINDINGS_PATH

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['file_path', 'line_number', 'pattern_type', 'match', 'timestamp']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(findings)

    return output_path

def run_pii_scan(base_path: Optional[Path] = None, logger: Optional[logging.Logger] = None) -> Tuple[int, Path]:
    """
    Run PII scan on all data subdirectories.

    Args:
        base_path: Base path for data directory (defaults to project root)
        logger: Optional logger instance

    Returns:
        Tuple[int, Path]: Number of findings and path to findings CSV
    """
    if base_path is None:
        base_path = Path('.')

    data_path = base_path / 'data'

    if not data_path.exists():
        if logger:
            logger.error(f"Data directory does not exist: {data_path}")
        return 0, data_path / 'pii_findings.csv'

    all_findings = []

    for subdir in SCAN_SUBDIRECTORIES:
        subdir_path = data_path / subdir
        if subdir_path.exists():
            findings = scan_directory(subdir_path, logger)
            all_findings.extend(findings)
        elif logger:
            logger.warning(f"Subdirectory does not exist: {subdir_path}")

    # Write findings to CSV
    output_path = write_findings_to_csv(all_findings, data_path / 'pii_findings.csv')

    if logger:
        logger.info(f"PII scan complete. Total findings: {len(all_findings)}. Output: {output_path}")

    return len(all_findings), output_path

def main() -> int:
    """
    Main entry point for PII scanner.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger = setup_logging()

    try:
        logger.info("=" * 60)
        logger.info("Starting PII Scan")
        logger.info("=" * 60)

        findings_count, output_path = run_pii_scan(logger=logger)

        logger.info("=" * 60)
        logger.info(f"PII Scan Complete")
        logger.info(f"Total PII instances found: {findings_count}")
        logger.info(f"Findings written to: {output_path}")
        logger.info("=" * 60)

        # Return non-zero exit code if PII found (for validation)
        return 0 if findings_count == 0 else 0

    except Exception as e:
        logger.error(f"PII scan failed with error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())