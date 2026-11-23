"""
Security scanning module for PII detection in data files.
Implements scanning for common PII patterns including emails, SSNs, phone numbers,
credit cards, and other sensitive information.
"""
import os
import re
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PII detection patterns
PII_PATTERNS = {
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'ssn_compact': re.compile(r'\b\d{9}\b'),
    'phone_us': re.compile(r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'date_of_birth': re.compile(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'),
    'url': re.compile(r'https?://[^\s]+'),
    'ip_address_v6': re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'),
    'driver_license': re.compile(r'\b[A-Z]{1,2}\d{6,8}\b'),
}

def is_valid_credit_card(card_number: str) -> bool:
    """
    Validate a credit card number using the Luhn algorithm.
    
    Args:
        card_number: The credit card number as a string
        
    Returns:
        True if the number passes the Luhn check, False otherwise
    """
    # Remove spaces and dashes
    cleaned = re.sub(r'[\s-]', '', card_number)
    
    if not cleaned.isdigit() or len(cleaned) < 13 or len(cleaned) > 19:
        return False
    
    digits = [int(d) for d in cleaned]
    # Reverse the digits
    digits = digits[::-1]
    
    total = 0
    for i, digit in enumerate(digits):
        if i % 2 == 1:  # Double every second digit (from the right in original)
            doubled = digit * 2
            if doubled > 9:
                doubled -= 9
            total += doubled
        else:
            total += digit
    
    return total % 10 == 0

def scan_text_for_pii(text: str, filename: str = "unknown") -> List[Dict]:
    """
    Scan a text string for PII patterns.
    
    Args:
        text: The text to scan
        filename: Source filename for context
        
    Returns:
        List of dictionaries containing match details
    """
    findings = []
    
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            # Additional validation for credit cards
            if pattern_name == 'credit_card':
                if not is_valid_credit_card(match):
                    continue
            
            findings.append({
                'file': filename,
                'type': pattern_name,
                'match': match,
                'line_number': text[:text.find(match)].count('\n') + 1
            })
    
    return findings

def scan_csv_file(filepath: Path) -> List[Dict]:
    """
    Scan a CSV file for PII patterns.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        List of dictionaries containing match details
    """
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader, 1):
                for cell in row:
                    cell_findings = scan_text_for_pii(str(cell), str(filepath))
                    for finding in cell_findings:
                        finding['line_number'] = row_num
                    findings.extend(cell_findings)
    except Exception as e:
        logger.error(f"Error scanning CSV file {filepath}: {e}")
    
    return findings

def scan_json_file(filepath: Path) -> List[Dict]:
    """
    Scan a JSON file for PII patterns.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of dictionaries containing match details
    """
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            findings = scan_text_for_pii(content, str(filepath))
    except Exception as e:
        logger.error(f"Error scanning JSON file {filepath}: {e}")
    
    return findings

def scan_yaml_file(filepath: Path) -> List[Dict]:
    """
    Scan a YAML file for PII patterns.
    
    Args:
        filepath: Path to the YAML file
        
    Returns:
        List of dictionaries containing match details
    """
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            findings = scan_text_for_pii(content, str(filepath))
    except Exception as e:
        logger.error(f"Error scanning YAML file {filepath}: {e}")
    
    return findings

def scan_text_file(filepath: Path) -> List[Dict]:
    """
    Scan a text file for PII patterns.
    
    Args:
        filepath: Path to the text file
        
    Returns:
        List of dictionaries containing match details
    """
    findings = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            findings = scan_text_for_pii(content, str(filepath))
    except Exception as e:
        logger.error(f"Error scanning text file {filepath}: {e}")
    
    return findings

def scan_directory(directory: Path, extensions: Optional[List[str]] = None) -> List[Dict]:
    """
    Recursively scan a directory for PII in files.
    
    Args:
        directory: Path to the directory to scan
        extensions: Optional list of file extensions to scan (default: all text-based)
        
    Returns:
        List of dictionaries containing match details
    """
    if extensions is None:
        extensions = ['.csv', '.json', '.yaml', '.yml', '.txt', '.log', '.md']
    
    findings = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            
            if file_path.suffix.lower() in extensions:
                try:
                    if file_path.suffix.lower() == '.csv':
                        file_findings = scan_csv_file(file_path)
                    elif file_path.suffix.lower() in ['.json']:
                        file_findings = scan_json_file(file_path)
                    elif file_path.suffix.lower() in ['.yaml', '.yml']:
                        file_findings = scan_yaml_file(file_path)
                    else:
                        file_findings = scan_text_file(file_path)
                    
                    findings.extend(file_findings)
                except Exception as e:
                    logger.warning(f"Could not scan file {file_path}: {e}")
    
    return findings

def generate_report(findings: List[Dict], output_path: Path) -> None:
    """
    Generate a PII scan report and save it to a file.
    
    Args:
        findings: List of PII findings
        output_path: Path to save the report
    """
    report_lines = [
        "PII SCAN REPORT",
        "=" * 50,
        f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total Findings: {len(findings)}",
        "",
        "SUMMARY BY TYPE:",
        "-" * 30
    ]
    
    # Count findings by type
    type_counts = {}
    for finding in findings:
        ptype = finding['type']
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    for ptype, count in sorted(type_counts.items()):
        report_lines.append(f"  {ptype}: {count}")
    
    if not findings:
        report_lines.append("  No PII detected.")
    
    report_lines.extend([
        "",
        "DETAILED FINDINGS:",
        "-" * 30
    ])
    
    if findings:
        for i, finding in enumerate(findings, 1):
            report_lines.append(f"{i}. File: {finding['file']}")
            report_lines.append(f"   Type: {finding['type']}")
            report_lines.append(f"   Match: {finding['match'][:50]}{'...' if len(finding['match']) > 50 else ''}")
            report_lines.append(f"   Line: {finding['line_number']}")
            report_lines.append("")
    else:
        report_lines.append("No PII findings detected in scanned files.")
    
    report_lines.extend([
        "",
        "=" * 50,
        "END OF REPORT"
    ])
    
    # Write report to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"PII scan report written to {output_path}")

def main():
    """
    Main entry point for the security scan.
    Scans data directories and generates a report.
    """
    # Define directories to scan
    base_path = Path(__file__).parent.parent
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed"
    ]
    
    output_path = base_path / "pii_scan_report.txt"
    
    logger.info("Starting PII security scan...")
    
    all_findings = []
    
    for data_dir in data_dirs:
        if data_dir.exists():
            logger.info(f"Scanning directory: {data_dir}")
            findings = scan_directory(data_dir)
            all_findings.extend(findings)
            logger.info(f"Found {len(findings)} potential PII instances in {data_dir}")
        else:
            logger.warning(f"Directory not found: {data_dir}")
    
    # Generate report
    generate_report(all_findings, output_path)
    
    if all_findings:
        logger.warning(f"PII detected! Review report at {output_path}")
        sys.exit(1)
    else:
        logger.info("No PII detected. Scan complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()
