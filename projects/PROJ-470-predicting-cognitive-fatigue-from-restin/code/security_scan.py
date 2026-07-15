import os
import re
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import List, Dict, Any, Tuple

# PII Patterns
PII_PATTERNS = {
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone_us': re.compile(r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-.\s]?){3}\d{4}\b'),
    'date_of_birth': re.compile(r'\b(?:\d{1,2}[-./]\d{1,2}[-./]\d{2,4})\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'drivers_license': re.compile(r'\b[A-Z]{1,2}\d{6,8}\b'),
    'passport': re.compile(r'\b[A-Z0-9]{6,9}\b'),
}

# Common PII keywords that might indicate sensitive data
PII_KEYWORDS = [
    'social_security', 'ssn', 'credit_card', 'passport', 'driver_license',
    'medical_record', 'patient_id', 'npi', 'medicare', 'medicaid',
    'biometric', 'genetic', 'dna', 'fingerprint', 'retina'
]

def scan_text_for_pii(text: str, filename: str = "unknown") -> List[Dict[str, Any]]:
    """Scan a text string for PII patterns."""
    findings = []
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            for match in matches:
                findings.append({
                    'file': filename,
                    'type': pii_type,
                    'match': match,
                    'severity': 'high' if pii_type in ['ssn', 'credit_card'] else 'medium'
                })
    
    # Check for keywords
    text_lower = text.lower()
    for keyword in PII_KEYWORDS:
        if keyword in text_lower:
            # Find the context around the keyword
            idx = text_lower.find(keyword)
            context = text[max(0, idx-50):idx+50]
            findings.append({
                'file': filename,
                'type': 'keyword',
                'match': keyword,
                'context': context,
                'severity': 'low'
            })
    
    return findings

def scan_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """Scan a CSV file for PII."""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row_num, row in enumerate(reader):
                for col_num, cell in enumerate(row):
                    cell_findings = scan_text_for_pii(str(cell), filepath)
                    for finding in cell_findings:
                        finding['row'] = row_num
                        finding['column'] = col_num
                    findings.extend(cell_findings)
    except Exception as e:
        findings.append({
            'file': filepath,
            'type': 'error',
            'match': str(e),
            'severity': 'critical'
        })
    return findings

def scan_json_file(filepath: str) -> List[Dict[str, Any]]:
    """Scan a JSON file for PII."""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            text_content = json.dumps(data)
            findings = scan_text_for_pii(text_content, filepath)
    except Exception as e:
        findings.append({
            'file': filepath,
            'type': 'error',
            'match': str(e),
            'severity': 'critical'
        })
    return findings

def scan_yaml_file(filepath: str) -> List[Dict[str, Any]]:
    """Scan a YAML file for PII."""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = yaml.safe_load(f)
            text_content = yaml.dump(data)
            findings = scan_text_for_pii(text_content, filepath)
    except Exception as e:
        findings.append({
            'file': filepath,
            'type': 'error',
            'match': str(e),
            'severity': 'critical'
        })
    return findings

def scan_text_file(filepath: str) -> List[Dict[str, Any]]:
    """Scan a text file for PII."""
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            findings = scan_text_for_pii(content, filepath)
    except Exception as e:
        findings.append({
            'file': filepath,
            'type': 'error',
            'match': str(e),
            'severity': 'critical'
        })
    return findings

def scan_directory(directory: str, extensions: List[str] = None) -> Dict[str, Any]:
    """Scan a directory for PII in supported file types."""
    if extensions is None:
        extensions = ['.csv', '.json', '.yaml', '.yml', '.txt']
    
    all_findings = []
    summary = {
        'directory': directory,
        'total_files_scanned': 0,
        'files_with_findings': 0,
        'total_findings': 0,
        'findings_by_type': {},
        'findings_by_severity': {},
        'critical_findings': []
    }
    
    directory_path = Path(directory)
    if not directory_path.exists():
        return {
            'error': f"Directory does not exist: {directory}",
            'findings': []
        }
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and any(file_path.suffix == ext for ext in extensions):
            summary['total_files_scanned'] += 1
            file_findings = []
            
            try:
                if file_path.suffix == '.csv':
                    file_findings = scan_csv_file(str(file_path))
                elif file_path.suffix in ['.json']:
                    file_findings = scan_json_file(str(file_path))
                elif file_path.suffix in ['.yaml', '.yml']:
                    file_findings = scan_yaml_file(str(file_path))
                elif file_path.suffix == '.txt':
                    file_findings = scan_text_file(str(file_path))
                
                if file_findings:
                    summary['files_with_findings'] += 1
                    all_findings.extend(file_findings)
                    
                    for finding in file_findings:
                        finding_type = finding.get('type', 'unknown')
                        severity = finding.get('severity', 'unknown')
                        
                        summary['findings_by_type'][finding_type] = \
                            summary['findings_by_type'].get(finding_type, 0) + 1
                        summary['findings_by_severity'][severity] = \
                            summary['findings_by_severity'].get(severity, 0) + 1
                        
                        if severity == 'critical':
                            summary['critical_findings'].append(finding)
            except Exception as e:
                all_findings.append({
                    'file': str(file_path),
                    'type': 'scan_error',
                    'match': str(e),
                    'severity': 'critical'
                })
    
    summary['total_findings'] = len(all_findings)
    return {
        'summary': summary,
        'findings': all_findings
    }

def main():
    """Main entry point for the security scan."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan project files for PII')
    parser.add_argument('--directory', '-d', default='data', 
                      help='Directory to scan (default: data)')
    parser.add_argument('--output', '-o', default='data/security_scan_report.json',
                      help='Output file for scan report')
    parser.add_argument('--extensions', '-e', nargs='+', 
                      default=['.csv', '.json', '.yaml', '.yml', '.txt'],
                      help='File extensions to scan')
    parser.add_argument('--fail-on-critical', action='store_true',
                      help='Exit with error code if critical findings are found')
    
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.directory}")
    print(f"File extensions: {args.extensions}")
    
    result = scan_directory(args.directory, args.extensions)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\nScan complete. Report saved to: {output_path}")
    print(f"Total files scanned: {result['summary']['total_files_scanned']}")
    print(f"Files with findings: {result['summary']['files_with_findings']}")
    print(f"Total findings: {result['summary']['total_findings']}")
    
    if result['summary']['findings_by_severity']:
        print("\nFindings by severity:")
        for severity, count in result['summary']['findings_by_severity'].items():
            print(f"  {severity}: {count}")
    
    if result['summary']['critical_findings']:
        print("\nCritical findings:")
        for finding in result['summary']['critical_findings']:
            print(f"  - {finding}")
        
        if args.fail_on_critical:
            print("\nFailing due to critical findings.")
            sys.exit(1)
    else:
        print("\nNo critical findings detected.")
    
    sys.exit(0)

if __name__ == '__main__':
    main()
