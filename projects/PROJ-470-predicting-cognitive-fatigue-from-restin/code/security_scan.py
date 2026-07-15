"""
Security hardening module for PII (Personally Identifiable Information) scanning.

This module implements regex-based and heuristic scanning for common PII patterns
in text, CSV, JSON, YAML, and general directory structures. It is designed to
run on the processed data and configuration files to ensure no sensitive patient
information leaks into the research artifacts.

Patterns detected:
- Social Security Numbers (US)
- Phone numbers (US/International formats)
- Email addresses
- Credit Card numbers (Luhn check)
- IP addresses
- Date of Birth (common formats)
- Patient IDs (generic patterns)
"""
import os
import re
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Regex patterns for common PII
PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone_us": re.compile(r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "date_of_birth": re.compile(r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b"),
    "patient_id_generic": re.compile(r"\b(?:PAT|ID|PID)[-_\s]?\d{4,}\b", re.IGNORECASE),
    "medical_record_number": re.compile(r"\b(?:MRN|MR)[-_\s]?\d{6,}\b", re.IGNORECASE),
}

# Credit card validation helper
def is_valid_credit_card(card_number: str) -> bool:
    """Luhn algorithm for credit card validation."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0

def scan_text_for_pii(text: str, filename: str = "unknown") -> List[Dict[str, Any]]:
    """
    Scan a text string for PII patterns.
    
    Args:
        text: The text content to scan.
        filename: The source filename for reporting context.
        
    Returns:
        A list of dictionaries containing match details.
    """
    findings = []
    for ptype, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            # Additional validation for specific types
            if ptype == "credit_card" and not is_valid_credit_card(match):
                continue
            findings.append({
                "type": ptype,
                "value": match,
                "file": filename,
                "line": None, # Line number not tracked in raw string scan
                "timestamp": datetime.now().isoformat()
            })
    return findings

def scan_csv_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    Scan a CSV file for PII.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        List of findings.
    """
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for line_num, row in enumerate(reader, 1):
                for cell in row:
                    if not isinstance(cell, str):
                        continue
                    matches = scan_text_for_pii(cell, str(filepath))
                    for m in matches:
                        m["line"] = line_num
                        findings.append(m)
    except Exception as e:
        print(f"Error scanning CSV {filepath}: {e}", file=sys.stderr)
    return findings

def scan_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    Scan a JSON file for PII.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        List of findings.
    """
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Scan raw content first
            raw_matches = scan_text_for_pii(content, str(filepath))
            findings.extend(raw_matches)
            
            # Also parse and scan values if valid JSON
            try:
                data = json.loads(content)
                # Recursive scan of values
                def scan_obj(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            scan_obj(v, f"{path}.{k}")
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj):
                            scan_obj(v, f"{path}[{i}]")
                    elif isinstance(obj, str):
                        matches = scan_text_for_pii(obj, str(filepath))
                        for m in matches:
                            m["context_path"] = path
                            findings.append(m)
                
                scan_obj(data)
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Error scanning JSON {filepath}: {e}", file=sys.stderr)
    return findings

def scan_yaml_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    Scan a YAML file for PII.
    
    Args:
        filepath: Path to the YAML file.
        
    Returns:
        List of findings.
    """
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            raw_matches = scan_text_for_pii(content, str(filepath))
            findings.extend(raw_matches)
            
            try:
                data = yaml.safe_load(content)
                def scan_obj(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            scan_obj(v, f"{path}.{k}")
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj):
                            scan_obj(v, f"{path}[{i}]")
                    elif isinstance(obj, str):
                        matches = scan_text_for_pii(obj, str(filepath))
                        for m in matches:
                            m["context_path"] = path
                            findings.append(m)
                
                if data:
                    scan_obj(data)
            except yaml.YAMLError:
                pass
    except Exception as e:
        print(f"Error scanning YAML {filepath}: {e}", file=sys.stderr)
    return findings

def scan_text_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    Scan a generic text file line by line.
    
    Args:
        filepath: Path to the text file.
        
    Returns:
        List of findings.
    """
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                matches = scan_text_for_pii(line, str(filepath))
                for m in matches:
                    m["line"] = line_num
                    findings.append(m)
    except Exception as e:
        print(f"Error scanning text file {filepath}: {e}", file=sys.stderr)
    return findings

def scan_directory(root_path: Path, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recursively scan a directory for PII in supported file types.
    
    Args:
        root_path: Root directory to scan.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                    If None, scans all common config/data extensions.
                    
    Returns:
        A summary dictionary containing total counts and detailed findings.
    """
    if extensions is None:
        extensions = ['.csv', '.json', '.yaml', '.yml', '.txt', '.md']
    
    all_findings = []
    files_scanned = 0
    files_with_findings = 0
    findings_by_file = {}

    for ext in extensions:
        for filepath in root_path.rglob(f"*{ext}"):
            if filepath.is_file():
                files_scanned += 1
                findings = []
                
                if ext.lower() in ['.csv']:
                    findings = scan_csv_file(filepath)
                elif ext.lower() in ['.json']:
                    findings = scan_json_file(filepath)
                elif ext.lower() in ['.yaml', '.yml']:
                    findings = scan_yaml_file(filepath)
                else:
                    findings = scan_text_file(filepath)
                
                if findings:
                    files_with_findings += 1
                    findings_by_file[str(filepath)] = findings
                    all_findings.extend(findings)

    return {
        "scan_timestamp": datetime.now().isoformat(),
        "root_path": str(root_path),
        "files_scanned": files_scanned,
        "files_with_findings": files_with_findings,
        "total_findings": len(all_findings),
        "findings_by_file": findings_by_file
    }

def main():
    """
    Entry point for the security scan script.
    Scans the project's data and code directories and outputs a JSON report.
    """
    # Define default paths relative to project root
    # Assuming script runs from project root or code/ directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    output_file = project_root / "data" / "security_scan_report.json"
    
    print(f"Starting PII security scan on: {project_root}")
    print(f"Scanning directories: {data_dir}, {code_dir}")
    
    all_findings = []
    files_scanned = 0
    files_with_findings = 0
    findings_by_file = {}

    # Scan data directory
    if data_dir.exists():
        result = scan_directory(data_dir)
        files_scanned += result["files_scanned"]
        files_with_findings += result["files_with_findings"]
        all_findings.extend([f for sublist in result["findings_by_file"].values() for f in sublist])
        findings_by_file.update(result["findings_by_file"])
        print(f"  Data dir: {result['files_scanned']} files, {result['total_findings']} findings")
    
    # Scan code directory (config files, etc.)
    if code_dir.exists():
        result = scan_directory(code_dir)
        files_scanned += result["files_scanned"]
        files_with_findings += result["files_with_findings"]
        all_findings.extend([f for sublist in result["findings_by_file"].values() for f in sublist])
        findings_by_file.update(result["findings_by_file"])
        print(f"  Code dir: {result['files_scanned']} files, {result['total_findings']} findings")

    report = {
        "scan_timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "files_scanned": files_scanned,
        "files_with_findings": files_with_findings,
        "total_findings": len(all_findings),
        "findings_by_file": findings_by_file,
        "status": "CLEAN" if len(all_findings) == 0 else "VIOLATIONS_FOUND"
    }

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Scan complete. Report written to: {output_file}")
    if report["total_findings"] > 0:
        print(f"WARNING: Found {report['total_findings']} potential PII instances.")
        sys.exit(1)
    else:
        print("SUCCESS: No PII detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()
