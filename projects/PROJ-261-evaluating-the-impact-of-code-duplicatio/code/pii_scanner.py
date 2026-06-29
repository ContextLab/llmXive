"""
PII Scanner Module

Scans code files for personally identifiable information patterns.
"""
import csv
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import get_pii_scan_enabled

logger = logging.getLogger(__name__)

# PII patterns per Constitution Principle III
PII_PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone': r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    'ssn': r'\d{3}[-.]?\d{2}[-.]?\d{4}',
    'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'api_key': r'[A-Za-z0-9_-]{32,}',
    'aws_key': r'AKIA[0-9A-Z]{16}'
}

def setup_logging():
    """Configure logging for PII scanner."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def should_scan_file(file_path: Path) -> bool:
    """
    Determine if a file should be scanned for PII.
    
    Args:
        file_path: Path to file
        
    Returns:
        True if file should be scanned
    """
    # Skip binary files and common non-code extensions
    skip_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.exe', '.dll'}
    return file_path.suffix.lower() not in skip_extensions

def scan_file_for_pii(file_path: Path) -> List[dict]:
    """
    Scan a single file for PII patterns.
    
    Args:
        file_path: Path to file
        
    Returns:
        List of PII findings with location info
    """
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        logger.warning(f"Failed to read {file_path}: {e}")
        return findings
    
    for pattern_name, pattern in PII_PATTERNS.items():
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                findings.append({
                    'file': str(file_path),
                    'line': line_num,
                    'pattern': pattern_name,
                    'match': match.group()[:50],  # Truncate for safety
                    'timestamp': datetime.now().isoformat()
                })
    
    return findings

def scan_directory(
    directory: Path,
    recursive: bool = True
) -> List[dict]:
    """
    Scan directory for PII in all code files.
    
    Args:
        directory: Path to directory
        recursive: Scan subdirectories
        
    Returns:
        List of all PII findings
    """
    findings = []
    
    logger.info(f"Starting PII scan of directory: {directory}")
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return findings
    
    # FIX: Use Path.rglob() instead of .walk() which doesn't exist
    if recursive:
        file_paths = list(directory.rglob('*'))
    else:
        file_paths = list(directory.glob('*'))
    
    for file_path in file_paths:
        if not file_path.is_file():
            continue
        
        if not should_scan_file(file_path):
            continue
        
        try:
            file_findings = scan_file_for_pii(file_path)
            findings.extend(file_findings)
        except Exception as e:
            logger.warning(f"Failed to scan {file_path}: {e}")
    
    logger.info(f"PII scan completed. Found {len(findings)} potential issues")
    return findings

def write_findings_to_csv(
    findings: List[dict],
    output_path: str
) -> None:
    """
    Write PII findings to CSV file.
    
    Args:
        findings: List of finding dictionaries
        output_path: Path to output CSV
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not findings:
        # Write empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['file', 'line', 'pattern', 'match', 'timestamp'])
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=findings[0].keys())
        writer.writeheader()
        writer.writerows(findings)
    
    logger.info(f"Written {len(findings)} findings to {output_path}")

def run_pii_scan(
    data_dir: str,
    output_path: str
) -> List[dict]:
    """
    Run full PII scan on data directory.
    
    Args:
        data_dir: Path to data directory
        output_path: Path to output CSV
        
    Returns:
        List of findings
    """
    data_path = Path(data_dir)
    findings = scan_directory(data_path)
    write_findings_to_csv(findings, output_path)
    return findings

def main():
    """Main entry point for PII scanner."""
    setup_logging()
    
    base_path = Path(__file__).parent.parent
    data_dir = base_path / 'data'
    output_path = base_path / 'data' / 'analysis' / 'pii_findings.csv'
    
    if not get_pii_scan_enabled():
        logger.info("PII scanning is disabled in config")
        return 0
    
    try:
        findings = run_pii_scan(str(data_dir), str(output_path))
        
        if findings:
            logger.warning(f"Found {len(findings)} potential PII instances")
        else:
            logger.info("No PII patterns detected")
        
        return 0
        
    except Exception as e:
        logger.error(f"PII scan failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())