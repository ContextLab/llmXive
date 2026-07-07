"""
Security hardening for data handling: PII scan implementation.

This module scans the project's data directories for potential Personally
Identifiable Information (PII) patterns in text-based data files (CSV, JSON, TXT,
YAML). It is designed to run as a pre-processing or post-processing step to
ensure no sensitive participant data leaks into the analysis pipeline.

Scanned patterns include:
- Social Security Numbers (SSN)
- Email addresses
- Phone numbers (US formats)
- Credit card numbers (basic patterns)
- Common PII field names (e.g., "patient_id", "ssn", "dob")

Output:
- Prints a summary of findings to stdout.
- Writes a detailed JSON report to `data/analysis/pii_scan_report.json`.
- Exits with code 1 if any PII is detected.
"""
import os
import re
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import Dict, List, Any, Set
import logging

# Configure logging
logger = logging.getLogger(__name__)

# PII Regex Patterns
PII_PATTERNS = {
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "us_phone": re.compile(r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b'),
    "credit_card": re.compile(r'\b(?:4\d{3}|5[1-5]\d{2}|6771|6011|3[47]\d{2})[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b'),
    "date_of_birth": re.compile(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'),
    "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
}

# Suspicious Column Names (Case-insensitive check)
SUSPICIOUS_COLUMNS = {
    "ssn", "social_security", "social_security_number",
    "patient_id", "patient_name", "subject_name", "participant_name",
    "dob", "date_of_birth", "birth_date",
    "email", "phone", "telephone", "mobile",
    "address", "street", "city", "state", "zip", "postal_code",
    "credit_card", "card_number", "billing_address"
}

def scan_text_for_pii(text: str, filename: str) -> List[Dict[str, Any]]:
    """Scan a string for PII patterns."""
    findings = []
    for p_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            # Count occurrences
            count = len(matches)
            # Mask the first match for the report (don't expose real PII)
            masked_sample = pattern.sub("[REDACTED]", text[text.find(matches[0]):text.find(matches[0])+50]) if matches[0] in text else "[REDACTED]"
            findings.append({
                "file": filename,
                "type": p_type,
                "count": count,
                "sample": masked_sample
            })
    return findings

def scan_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a CSV file for PII in headers and content."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            # Check headers first
            try:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    for h in headers:
                        if h.lower().strip() in SUSPICIOUS_COLUMNS:
                            findings.append({
                                "file": str(file_path),
                                "type": "suspicious_header",
                                "count": 1,
                                "sample": f"Header: {h}"
                            })
                # Scan content (limit to first 1000 rows for performance)
                for i, row in enumerate(reader):
                    if i > 1000:
                        break
                    for cell in row:
                        if cell:
                            findings.extend(scan_text_for_pii(str(cell), str(file_path)))
            except Exception as e:
                logger.warning(f"Could not parse CSV {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
    return findings

def scan_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a JSON file for PII."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                data = json.load(f)
                # Convert to string for pattern scanning
                text_data = json.dumps(data)
                # Check keys
                if isinstance(data, dict):
                    for key in data.keys():
                        if key.lower().strip() in SUSPICIOUS_COLUMNS:
                            findings.append({
                                "file": str(file_path),
                                "type": "suspicious_key",
                                "count": 1,
                                "sample": f"Key: {key}"
                            })
                findings.extend(scan_text_for_pii(text_data, str(file_path)))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {file_path}, scanning as text.")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_text:
                    findings.extend(scan_text_for_pii(f_text.read(), str(file_path)))
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
    return findings

def scan_yaml_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a YAML file for PII."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                data = yaml.safe_load(f)
                if data:
                    text_data = json.dumps(data)
                    if isinstance(data, dict):
                        for key in data.keys():
                            if key.lower().strip() in SUSPICIOUS_COLUMNS:
                                findings.append({
                                    "file": str(file_path),
                                    "type": "suspicious_key",
                                    "count": 1,
                                    "sample": f"Key: {key}"
                                })
                    findings.extend(scan_text_for_pii(text_data, str(file_path)))
            except yaml.YAMLError:
                logger.warning(f"Invalid YAML in {file_path}, scanning as text.")
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f_text:
                    findings.extend(scan_text_for_pii(f_text.read(), str(file_path)))
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
    return findings

def scan_text_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a plain text file for PII."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            findings.extend(scan_text_for_pii(content, str(file_path)))
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
    return findings

def scan_directory(root_dir: str) -> Dict[str, Any]:
    """Recursively scan a directory for PII in supported file types."""
    root_path = Path(root_dir)
    if not root_path.exists():
        logger.error(f"Directory {root_dir} does not exist.")
        return {"status": "error", "message": "Directory not found"}

    all_findings = []
    file_count = 0
    scanned_files = []

    # Supported extensions
    supported_extensions = {'.csv', '.json', '.yaml', '.yml', '.txt'}

    for file_path in root_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            # Skip hidden files and common non-data files
            if file_path.name.startswith('.') or file_path.name == 'requirements.txt':
                continue
            
            file_count += 1
            scanned_files.append(str(file_path))
            
            if file_path.suffix.lower() == '.csv':
                findings = scan_csv_file(file_path)
            elif file_path.suffix.lower() == '.json':
                findings = scan_json_file(file_path)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                findings = scan_yaml_file(file_path)
            else:
                findings = scan_text_file(file_path)
            
            all_findings.extend(findings)

    return {
        "status": "completed",
        "directory_scanned": str(root_path),
        "files_scanned": file_count,
        "files_list": scanned_files,
        "findings": all_findings,
        "total_pii_detected": len(all_findings)
    }

def main():
    """Main entry point for the PII scanner."""
    # Define the project root relative to the script location
    # Assuming script is in code/, root is ../
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} not found. Exiting.")
        sys.exit(1)

    print(f"Starting PII scan on: {data_dir}")
    results = scan_directory(str(data_dir))

    # Save report
    analysis_dir = project_root / "data" / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    report_path = analysis_dir / "pii_scan_report.json"

    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n--- PII Scan Summary ---")
    print(f"Directory scanned: {results['directory_scanned']}")
    print(f"Files scanned: {results['files_scanned']}")
    print(f"Total PII findings: {results['total_pii_detected']}")
    
    if results['findings']:
        print("\nFindings detected:")
        for finding in results['findings']:
            print(f"  - Type: {finding['type']} | File: {finding['file']} | Sample: {finding['sample']}")
        print(f"\nWARNING: PII detected! Detailed report saved to {report_path}")
        sys.exit(1)
    else:
        print("\nNo PII patterns detected. Data handling is secure.")
        sys.exit(0)

if __name__ == "__main__":
    main()