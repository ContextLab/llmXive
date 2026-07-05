"""
PII Scanner for Security Hardening (Task T042).

Verifies no PII leakage in data/processed/ outputs by scanning text fields
for patterns like emails, phone numbers, SSNs, and names.
"""
import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from config import get_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PII Regex Patterns
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_us": re.compile(r"(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "date_of_birth": re.compile(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"),
}

# Common names list (subset for demonstration, in production use a larger list or external API)
COMMON_NAMES = {
    "john", "jane", "doe", "smith", "johnson", "williams", "brown", "jones",
    "garcia", "miller", "davis", "rodriguez", "martinez", "hernandez", "lopez"
}

@dataclass
class PIIResult:
    file_path: str
    line_number: int
    column: Optional[int]
    field_name: str
    pii_type: str
    matched_text: str

def scan_text_for_pii(text: str, line_num: int = 0, field_name: str = "unknown") -> List[PIIResult]:
    """Scan a string for PII patterns."""
    results = []
    if not isinstance(text, str):
        return results
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.finditer(text)
        for match in matches:
            results.append(PIIResult(
                file_path="unknown",
                line_number=line_num,
                column=match.start(),
                field_name=field_name,
                pii_type=pii_type,
                matched_text=match.group()
            ))
    
    # Simple name check (case-insensitive)
    words = text.lower().split()
    for word in words:
        if word in COMMON_NAMES and len(word) > 3:
            results.append(PIIResult(
                file_path="unknown",
                line_number=line_num,
                column=text.lower().find(word),
                field_name=field_name,
                pii_type="common_name",
                matched_text=word
            ))
    
    return results

def scan_csv_file(file_path: Path) -> List[PIIResult]:
    """Scan a CSV file for PII in text fields."""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                for field_name, value in row.items():
                    if value and isinstance(value, str):
                        found = scan_text_for_pii(value, line_num, field_name)
                        for res in found:
                            res.file_path = str(file_path)
                            results.append(res)
    except Exception as e:
        logger.error(f"Error scanning CSV {file_path}: {e}")
    return results

def scan_json_file(file_path: Path) -> List[PIIResult]:
    """Scan a JSON file for PII in string values."""
    results = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def traverse(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    traverse(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                found = scan_text_for_pii(obj, 0, path)
                for res in found:
                    res.file_path = str(file_path)
                    results.append(res)
        
        traverse(data)
    except Exception as e:
        logger.error(f"Error scanning JSON {file_path}: {e}")
    return results

def scan_directory_for_pii(directory: Path) -> Dict[str, List[PIIResult]]:
    """Recursively scan a directory for PII in text-based files."""
    all_results = {}
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return all_results
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            suffix = file_path.suffix.lower()
            results = []
            
            if suffix == ".csv":
                results = scan_csv_file(file_path)
            elif suffix == ".json":
                results = scan_json_file(file_path)
            elif suffix in [".txt", ".md", ".log"]:
                # Scan text files line by line
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, start=1):
                            found = scan_text_for_pii(line, line_num, "line")
                            for res in found:
                                res.file_path = str(file_path)
                                results.append(res)
                except Exception as e:
                    logger.error(f"Error scanning text file {file_path}: {e}")
            
            if results:
                all_results[str(file_path)] = results
    
    return all_results

def generate_security_report(results: Dict[str, List[PIIResult]], output_path: Path) -> bool:
    """Generate a security report JSON file."""
    report = {
        "scan_summary": {
            "total_files_scanned": len(results),
            "files_with_pii": len([r for r in results.values() if r]),
            "total_pii_findings": sum(len(r) for r in results.values())
        },
        "findings": []
    }
    
    for file_path, findings in results.items():
        for finding in findings:
            report["findings"].append({
                "file": finding.file_path,
                "line": finding.line_number,
                "column": finding.column,
                "field": finding.field_name,
                "type": finding.pii_type,
                "masked_value": f"{finding.matched_text[:2]}***{finding.matched_text[-2:]}" if len(finding.matched_text) > 4 else "***"
            })
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Security report generated: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write security report: {e}")
        return False

def run_pii_security_check() -> bool:
    """
    Main entry point for T042: Security hardening.
    Scans data/processed/ for PII and generates a report.
    Returns True if no PII found or if PII is acceptable (e.g., anonymized IDs), False if critical PII detected.
    """
    processed_dir = get_path("data", "processed")
    report_path = get_path("state", "projects", "PROJ-345", "security_report.json")
    
    logger.info(f"Scanning directory: {processed_dir}")
    results = scan_directory_for_pii(processed_dir)
    
    if not results:
        logger.info("No text files found in data/processed/ or no PII detected.")
        # Still generate an empty report
        generate_security_report({}, report_path)
        return True
    
    # Generate report
    generate_security_report(results, report_path)
    
    # Check for critical PII
    critical_types = {"email", "phone_us", "ssn", "credit_card"}
    critical_found = False
    
    for file_path, findings in results.items():
        for finding in findings:
            if finding.pii_type in critical_types:
                critical_found = True
                logger.critical(f"CRITICAL PII FOUND: {finding.pii_type} in {file_path} at line {finding.line_number}")
    
    if critical_found:
        logger.error("SECURITY HARDENING FAILED: Critical PII detected in processed data.")
        return False
    
    logger.info("SECURITY HARDENING PASSED: No critical PII detected.")
    return True

def main():
    """CLI entry point."""
    success = run_pii_security_check()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
