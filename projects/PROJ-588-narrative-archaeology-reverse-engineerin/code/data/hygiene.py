"""
Data Hygiene Module for Narrative Archaeology Pipeline.

Implements:
- MD5 checksum verification for raw data integrity
- PII scanning for sensitive information in text files
- Protection against in-place modifications
"""
import os
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import code.config as config
from data.download import calculate_md5

logger = logging.getLogger(__name__)

# PII Patterns for scanning (email, phone, SSN, etc.)
PII_PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone_us': r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
    'date_of_birth': r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
}

def verify_raw_data_checksum(
    raw_dir: Path,
    checksum_manifest: Path,
    expected_checksums: Optional[Dict[str, str]] = None
) -> Tuple[bool, List[str]]:
    """
    Verify MD5 checksums of all files in raw data directory against manifest.

    Args:
        raw_dir: Path to raw data directory
        checksum_manifest: Path to manifest file containing expected checksums
        expected_checksums: Optional dict of filename -> expected_md5. If provided,
                            overrides manifest file.

    Returns:
        Tuple of (all_valid, list_of_failed_files)
    """
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return False, [f"Directory missing: {raw_dir}"]

    if expected_checksums is None:
        if not checksum_manifest.exists():
            logger.error(f"Checksum manifest does not exist: {checksum_manifest}")
            return False, [f"Manifest missing: {checksum_manifest}"]
        
        # Load manifest (assumed format: "checksum  filename" per line)
        expected_checksums = {}
        with open(checksum_manifest, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        checksum = parts[0]
                        filename = ' '.join(parts[1:])
                        expected_checksums[filename] = checksum

    failed_files = []
    all_valid = True

    for filename, expected_md5 in expected_checksums.items():
        file_path = raw_dir / filename
        if not file_path.exists():
            logger.warning(f"File missing during checksum verification: {file_path}")
            failed_files.append(filename)
            all_valid = False
            continue

        actual_md5 = calculate_md5(file_path)
        if actual_md5 != expected_md5:
            logger.error(f"Checksum mismatch for {filename}: expected {expected_md5}, got {actual_md5}")
            failed_files.append(filename)
            all_valid = False
        else:
            logger.debug(f"Checksum verified for {filename}")

    return all_valid, failed_files

def scan_for_pii(
    file_path: Path,
    patterns: Optional[Dict[str, str]] = None
) -> Dict[str, List[str]]:
    """
    Scan a text file for potential PII patterns.

    Args:
        file_path: Path to file to scan
        patterns: Optional dict of pattern_name -> regex. Uses defaults if None.

    Returns:
        Dict mapping pattern_type to list of matched strings found
    """
    if patterns is None:
        patterns = PII_PATTERNS

    findings = {pattern_type: [] for pattern_type in patterns}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for pattern_type, pattern in patterns.items():
                matches = re.findall(pattern, content)
                if matches:
                    findings[pattern_type] = list(set(matches))  # Deduplicate
                    logger.warning(f"Found {len(matches)} potential {pattern_type} PII in {file_path.name}")
    except Exception as e:
        logger.error(f"Error scanning file {file_path} for PII: {e}")
        return findings

    return findings

def enforce_no_inplace_modifications(
    file_path: Path,
    backup_dir: Path
) -> bool:
    """
    Ensure a file is not modified in-place by creating a backup first.
    
    This function creates a backup copy of the file before any operations.
    The caller should use the backup path for any modifications.

    Args:
        file_path: Path to the file to protect
        backup_dir: Directory where backups will be stored

    Returns:
        True if backup was created successfully, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File does not exist: {file_path}")
        return False

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / file_path.name

    try:
        # Create backup
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup of {file_path.name} at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {e}")
        return False

def run_data_hygiene_check(
    raw_data_dir: Path,
    output_dir: Path,
    checksum_manifest: Optional[Path] = None
) -> Dict:
    """
    Run comprehensive data hygiene checks on a dataset.

    Args:
        raw_data_dir: Path to raw data directory
        output_dir: Path where hygiene report will be written
        checksum_manifest: Optional path to checksum manifest file

    Returns:
        Dict containing hygiene check results
    """
    results = {
        'checksum_verified': False,
        'checksum_failures': [],
        'pii_findings': {},
        'backups_created': [],
        'overall_status': 'PASSED'
    }

    # 1. Verify checksums if manifest exists
    if checksum_manifest and checksum_manifest.exists():
        logger.info("Running checksum verification...")
        valid, failures = verify_raw_data_checksum(raw_data_dir, checksum_manifest)
        results['checksum_verified'] = valid
        results['checksum_failures'] = failures
        if not valid:
            results['overall_status'] = 'FAILED'

    # 2. Scan for PII in text files
    logger.info("Scanning for PII...")
    text_extensions = ['.txt', '.csv', '.json', '.tsv', '.md']
    for file_path in raw_data_dir.rglob('*'):
        if file_path.suffix.lower() in text_extensions:
            findings = scan_for_pii(file_path)
            if any(findings.values()):
                results['pii_findings'][str(file_path)] = findings
                results['overall_status'] = 'WARNING'

    # 3. Create backups for all raw files
    logger.info("Creating backups of raw data...")
    backup_dir = output_dir / 'backups'
    for file_path in raw_data_dir.rglob('*'):
        if file_path.is_file():
            if enforce_no_inplace_modifications(file_path, backup_dir):
                results['backups_created'].append(str(file_path))

    # Write report
    report_path = output_dir / 'hygiene_report.json'
    import json
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Hygiene check complete. Report written to {report_path}")
    return results

if __name__ == "__main__":
    # Example usage for testing
    logging.basicConfig(level=logging.INFO)
    
    # This would normally be called with real paths from config
    # raw_dir = config.get_data_path() / "raw"
    # output_dir = config.get_output_path()
    # manifest = config.get_data_path() / "checksums.txt"
    
    # results = run_data_hygiene_check(raw_dir, output_dir, manifest)
    # print(f"Hygiene check status: {results['overall_status']}")
    pass
