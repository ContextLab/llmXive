"""
Security hardening module for PII scanning in EEG research data.
Implements regex-based scanning for common PII patterns (emails, SSNs, phone numbers).
"""
import os
import re
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Define PII patterns
PII_PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'ssn_no_dash': r'\b\d{9}\b',
    'phone_us': r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'driver_license': r'\b[A-Z]{1,2}\d{4,8}\b',
    'date_of_birth': r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
}

def is_valid_credit_card(card_number: str) -> bool:
    """
    Validates a credit card number using the Luhn algorithm.
    """
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = digits_of(card_number.replace("-", "").replace(" ", ""))
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(digits_of(d * 2))
    return total % 10 == 0

def scan_text_for_pii(text: str, patterns: dict = None) -> list:
    """
    Scans a string for PII patterns.
    
    Args:
        text: The string to scan.
        patterns: Dictionary of pattern names and regex patterns.
                
    Returns:
        List of dictionaries containing match details.
    """
    if patterns is None:
        patterns = PII_PATTERNS
    
    findings = []
    for pattern_name, pattern_regex in patterns.items():
        matches = re.findall(pattern_regex, text)
        for match in matches:
            findings.append({
                'type': pattern_name,
                'value': match,
                'position': text.find(match)
            })
    return findings

def scan_csv_file(file_path: str, patterns: dict = None) -> list:
    """
    Scans a CSV file for PII.
    
    Args:
        file_path: Path to the CSV file.
        patterns: Dictionary of pattern names and regex patterns.
                
    Returns:
        List of dictionaries containing match details.
    """
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader):
                for col_num, cell in enumerate(row):
                    if cell:
                        cell_findings = scan_text_for_pii(str(cell), patterns)
                        for finding in cell_findings:
                            finding['file'] = file_path
                            finding['row'] = row_num
                            finding['column'] = col_num
                            findings.append(finding)
    except Exception as e:
        findings.append({
            'error': str(e),
            'file': file_path,
            'type': 'read_error'
        })
    return findings

def scan_json_file(file_path: str, patterns: dict = None) -> list:
    """
    Scans a JSON file for PII.
    
    Args:
        file_path: Path to the JSON file.
        patterns: Dictionary of pattern names and regex patterns.
                
    Returns:
        List of dictionaries containing match details.
    """
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            # Recursively scan JSON structure
            def scan_obj(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        scan_obj(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        scan_obj(item, f"{path}[{i}]")
                elif isinstance(obj, str):
                    obj_findings = scan_text_for_pii(obj, patterns)
                    for finding in obj_findings:
                        finding['file'] = file_path
                        finding['path'] = path
                        findings.append(finding)
            scan_obj(data)
    except Exception as e:
        findings.append({
            'error': str(e),
            'file': file_path,
            'type': 'read_error'
        })
    return findings

def scan_yaml_file(file_path: str, patterns: dict = None) -> list:
    """
    Scans a YAML file for PII.
    
    Args:
        file_path: Path to the YAML file.
        patterns: Dictionary of pattern names and regex patterns.
                
    Returns:
        List of dictionaries containing match details.
    """
    findings = []
    try:
        import yaml
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = yaml.safe_load(f)
            if data:
                def scan_obj(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            scan_obj(v, f"{path}.{k}")
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            scan_obj(item, f"{path}[{i}]")
                    elif isinstance(obj, str):
                        obj_findings = scan_text_for_pii(obj, patterns)
                        for finding in obj_findings:
                            finding['file'] = file_path
                            finding['path'] = path
                            findings.append(finding)
                scan_obj(data)
    except ImportError:
        findings.append({
            'error': 'PyYAML not installed',
            'file': file_path,
            'type': 'dependency_error'
        })
    except Exception as e:
        findings.append({
            'error': str(e),
            'file': file_path,
            'type': 'read_error'
        })
    return findings

def scan_text_file(file_path: str, patterns: dict = None) -> list:
    """
    Scans a text file for PII.
    
    Args:
        file_path: Path to the text file.
        patterns: Dictionary of pattern names and regex patterns.
                
    Returns:
        List of dictionaries containing match details.
    """
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            text_findings = scan_text_for_pii(content, patterns)
            for finding in text_findings:
                finding['file'] = file_path
                findings.append(finding)
    except Exception as e:
        findings.append({
            'error': str(e),
            'file': file_path,
            'type': 'read_error'
        })
    return findings

def scan_directory(directory_path: str, patterns: dict = None) -> list:
    """
    Recursively scans a directory for PII in supported file types.
    
    Args:
        directory_path: Path to the directory to scan.
        patterns: Dictionary of pattern names and regex patterns.
                
    Returns:
        List of dictionaries containing match details.
    """
    all_findings = []
    supported_extensions = {'.csv', '.json', '.yaml', '.yml', '.txt', '.md'}
    
    if not os.path.exists(directory_path):
        all_findings.append({
            'error': f'Directory not found: {directory_path}',
            'file': directory_path,
            'type': 'directory_error'
        })
        return all_findings
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            if ext in supported_extensions:
                if ext == '.csv':
                    findings = scan_csv_file(file_path, patterns)
                elif ext == '.json':
                    findings = scan_json_file(file_path, patterns)
                elif ext in ['.yaml', '.yml']:
                    findings = scan_yaml_file(file_path, patterns)
                else:  # .txt, .md, etc.
                    findings = scan_text_file(file_path, patterns)
                
                all_findings.extend(findings)
    
    return all_findings

def generate_report(findings: list, output_path: str) -> None:
    """
    Generates a PII scan report.
    
    Args:
        findings: List of PII findings.
        output_path: Path to write the report.
    """
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("PII Security Scan Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Scan Time: {datetime.now().isoformat()}\n")
        f.write(f"Total Findings: {len(findings)}\n")
        f.write("=" * 50 + "\n\n")
        
        if not findings:
            f.write("No PII findings detected.\n")
        else:
            # Group findings by type
            by_type = {}
            for finding in findings:
                p_type = finding.get('type', 'unknown')
                if p_type not in by_type:
                    by_type[p_type] = []
                by_type[p_type].append(finding)
            
            for p_type, items in by_type.items():
                f.write(f"\n{p_type.upper()} ({len(items)} occurrences):\n")
                f.write("-" * 30 + "\n")
                for item in items[:10]:  # Limit to first 10 per type
                    f.write(f"  File: {item.get('file', 'N/A')}\n")
                    f.write(f"  Value: {item.get('value', 'N/A')}\n")
                    if 'row' in item:
                        f.write(f"  Row: {item['row']}, Col: {item.get('column', 'N/A')}\n")
                    if 'path' in item:
                        f.write(f"  Path: {item['path']}\n")
                    f.write("\n")
            
            if len(findings) > 10:
                f.write(f"\n... and {len(findings) - 10} more findings (truncated).\n")

def main():
    """
    Main entry point for PII scanning.
    Scans data/raw and data/processed directories.
    """
    # Define directories to scan
    project_root = Path(__file__).parent.parent
    directories_to_scan = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed'
    ]
    
    all_findings = []
    
    print("Starting PII Security Scan...")
    for directory in directories_to_scan:
        if directory.exists():
            print(f"Scanning {directory}...")
            findings = scan_directory(str(directory))
            all_findings.extend(findings)
        else:
            print(f"Directory not found, skipping: {directory}")
    
    # Generate report
    report_path = project_root / 'pii_scan_report.txt'
    generate_report(all_findings, str(report_path))
    
    print(f"Scan complete. Report written to {report_path}")
    print(f"Total findings: {len(all_findings)}")
    
    # Exit with error code if PII found
    if all_findings:
        print("WARNING: PII detected in scanned files!")
        sys.exit(1)
    else:
        print("SUCCESS: No PII detected.")
        sys.exit(0)

if __name__ == '__main__':
    main()
