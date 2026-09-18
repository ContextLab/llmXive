import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from code.config import Config

logger = logging.getLogger(__name__)

# PII Patterns: Email, Phone, SSN, Credit Card, IP Address
PII_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "phone_us": re.compile(r'(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "credit_card": re.compile(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'),
    "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    "driver_license": re.compile(r'\b[A-Z0-9]{6,9}\b'), # Generic broad pattern, context dependent
}

class PIIResult:
    def __init__(self, file_path: str, line_number: int, pattern_type: str, matched_text: str):
        self.file_path = file_path
        self.line_number = line_number
        self.pattern_type = pattern_type
        self.matched_text = matched_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "pattern_type": self.pattern_type,
            "matched_text": self.matched_text
        }

def scan_text_for_pii(text: str, file_path: str) -> List[PIIResult]:
    """Scan a block of text for PII patterns."""
    results = []
    lines = text.splitlines()
    for line_num, line in enumerate(lines, 1):
        for p_type, pattern in PII_PATTERNS.items():
            matches = pattern.findall(line)
            for match in matches:
                # Ensure we capture the full match string if findall returns groups
                if isinstance(match, tuple):
                    full_match = next((m for m in match if m), match[0])
                else:
                    full_match = match
                
                # Avoid false positives for IP addresses that are just numbers
                if p_type == "ip_address":
                    parts = full_match.split('.')
                    if not all(0 <= int(p) <= 255 for p in parts):
                        continue

                results.append(PIIResult(file_path, line_num, p_type, full_match))
    return results

def scan_csv_file(file_path: Path) -> List[PIIResult]:
    """Scan a CSV file for PII."""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for line_num, row in enumerate(reader, 1):
                for cell in row:
                    cell_results = scan_text_for_pii(cell, str(file_path))
                    # Adjust line number if we want to be more granular, but row index is fine
                    results.extend(cell_results)
    except Exception as e:
        logger.error(f"Error scanning CSV {file_path}: {e}")
    return results

def scan_json_file(file_path: Path) -> List[PIIResult]:
    """Scan a JSON file for PII."""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # Simple recursive scan of string values
        # For large files, a streaming approach might be needed, but text scan covers all strings
        results = scan_text_for_pii(content, str(file_path))
    except Exception as e:
        logger.error(f"Error scanning JSON {file_path}: {e}")
    return results

def scan_directory_for_pii(directory: Path) -> List[PIIResult]:
    """Recursively scan a directory for PII in text-based files."""
    all_results = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return all_results

    # Extensions to scan
    extensions = {'.csv', '.json', '.txt', '.log', '.tsv', '.yaml', '.yml'}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if Path(file).suffix.lower() in extensions:
                file_path = Path(root) / file
                if file_path.suffix.lower() == '.csv':
                    all_results.extend(scan_csv_file(file_path))
                elif file_path.suffix.lower() == '.json':
                    all_results.extend(scan_json_file(file_path))
                else:
                    # Default to text scan for others
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        all_results.extend(scan_text_for_pii(content, str(file_path)))
                    except Exception as e:
                        logger.error(f"Error reading {file_path}: {e}")
    return all_results

def generate_security_report(results: List[PIIResult], output_path: Optional[Path] = None) -> Dict[str, Any]:
    """Generate a summary report of PII findings."""
    report = {
        "total_pii_found": len(results),
        "files_affected": len(set(r.file_path for r in results)),
        "leaks": []
    }
    
    if results:
        report["leaks"] = [r.to_dict() for r in results]
        logger.warning(f"Found {len(results)} potential PII leaks.")
    else:
        logger.info("No PII leaks detected.")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Security report written to {output_path}")
    
    return report

def run_pii_security_check(target_directory: Optional[Path] = None, output_file: Optional[Path] = None) -> Dict[str, Any]:
    """Main entry point for running the security check."""
    if target_directory is None:
        target_directory = Path(Config.DATA_PROCESSED)
    
    logger.info(f"Scanning directory: {target_directory}")
    results = scan_directory_for_pii(target_directory)
    
    if output_file is None:
        output_file = Path(Config.REPORTS) / "pii_scan.json"
    
    return generate_security_report(results, output_file)

def main():
    """CLI entry point for PII scanning."""
    import argparse
    parser = argparse.ArgumentParser(description="Scan for PII in project data.")
    parser.add_argument("--target-dir", type=str, default=None, help="Directory to scan")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    target = Path(args.target_dir) if args.target_dir else None
    output = Path(args.output) if args.output else None

    report = run_pii_security_check(target_directory=target, output_file=output)
    
    if report["total_pii_found"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    import sys
    main()
