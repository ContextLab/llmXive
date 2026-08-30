import os
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Causal language patterns to flag
CAUSAL_PATTERNS = [
    r'\bpredicts\b',
    r'\bcaus(?:es|al|ally)\b',
    r'\bdrives\b',
    r'\binfluences\b',  # "influence" is in title but "influences" as verb is risky
    r'\bdetermines\b',
    r'\bgoverns\b',
    r'\bcontrols\b',
    r'\bresults in\b',
    r'\bleads to\b',
    r'\btriggers\b',
    r'\bproduces\b',
    r'\bcreates\b',
    r'\bcauses\b',
    r'\bmechanism(s)?\b',
    r'\bpathway(s)?\b',
    r'\bunderlying\b',
    r'\bdrive(s)?\b',
    r'\bfuel(s)?\b',
    r'\bpropel(s)?\b',
]

# Acceptable associational language
ASSOCIATIONAL_PATTERNS = [
    r'\bassociat(?:ed|ion|ions)\b',
    r'\bcorrelat(?:ed|ion|ions)\b',
    r'\brelat(?:ed|ionship|ionships)\b',
    r'\bconnect(?:ed|ion|ions)\b',
    r'\blink(?:ed|s|age)\b',
    r'\bcorrespond(?:s|ing|ence)\b',
    r'\bco-occur(?:s|ence)\b',
    r'\bco-vari(?:ate|ation)\b',
    r'\bstatistically significant\b',
    r'\bassociation\b',
    r'\bcorrelation\b',
]

def load_json_file(file_path: str) -> Dict:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise FileNotFoundError(f"Could not load JSON file {file_path}: {e}")

def load_csv_file(file_path: str) -> List[str]:
    """Load a CSV file and return all text content as a list of strings."""
    import pandas as pd
    try:
        df = pd.read_csv(file_path)
        # Convert all columns to strings and join
        return df.astype(str).values.flatten().tolist()
    except Exception as e:
        raise FileNotFoundError(f"Could not load CSV file {file_path}: {e}")

def check_text_for_causality(text: str) -> List[Tuple[str, str]]:
    """
    Check text for causal language patterns.
    Returns a list of (pattern, matched_text) tuples.
    """
    if not isinstance(text, str):
        text = str(text)
    
    findings = []
    text_lower = text.lower()
    
    for pattern in CAUSAL_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            # Get context around the match (±20 chars)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].strip()
            findings.append((pattern, f"...{context}..."))
    
    return findings

def scan_report_json(file_path: str) -> Dict:
    """
    Scan a JSON report file for causal language.
    Returns a report with findings.
    """
    data = load_json_file(file_path)
    findings = []
    
    def traverse(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                traverse(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                traverse(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            text_findings = check_text_for_causality(obj)
            for pattern, context in text_findings:
                findings.append({
                    "field": path,
                    "pattern": pattern,
                    "context": context
                })
    
    traverse(data)
    
    return {
        "file": file_path,
        "type": "json",
        "total_findings": len(findings),
        "findings": findings
    }

def scan_csv_file(file_path: str) -> Dict:
    """
    Scan a CSV file for causal language.
    Returns a report with findings.
    """
    rows = load_csv_file(file_path)
    findings = []
    
    for i, row_text in enumerate(rows):
        text_findings = check_text_for_causality(row_text)
        for pattern, context in text_findings:
            findings.append({
                "row": i,
                "pattern": pattern,
                "context": context
            })
    
    return {
        "file": file_path,
        "type": "csv",
        "total_findings": len(findings),
        "findings": findings
    }

def generate_audit_report(results_dir: str, output_path: str) -> Dict:
    """
    Generate a comprehensive audit report for associational language compliance.
    
    Args:
        results_dir: Directory containing report files to audit
        output_path: Path to save the audit report JSON
    
    Returns:
        Dictionary containing the audit report
    """
    report = {
        "audit_type": "associational_language_compliance",
        "fr_requirement": "FR-007",
        "description": "Final review of all reports for 'associational' language compliance",
        "files_audited": [],
        "summary": {
            "total_files": 0,
            "total_findings": 0,
            "compliance_status": "PASS"
        }
    }
    
    results_path = Path(results_dir)
    if not results_path.exists():
        report["error"] = f"Results directory not found: {results_dir}"
        report["summary"]["compliance_status"] = "FAIL"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return report
    
    # Find all report files
    json_files = list(results_path.glob("*.json"))
    csv_files = list(results_path.glob("*.csv"))
    
    all_findings = []
    
    # Audit JSON files
    for json_file in json_files:
        result = scan_report_json(str(json_file))
        report["files_audited"].append(result)
        all_findings.extend(result["findings"])
        report["summary"]["total_findings"] += result["total_findings"]
    
    # Audit CSV files
    for csv_file in csv_files:
        result = scan_csv_file(str(csv_file))
        report["files_audited"].append(result)
        all_findings.extend(result["findings"])
        report["summary"]["total_findings"] += result["total_findings"]
    
    report["summary"]["total_files"] = len(json_files) + len(csv_files)
    
    # Determine compliance status
    if report["summary"]["total_findings"] > 0:
        report["summary"]["compliance_status"] = "REVIEW_REQUIRED"
        report["summary"]["recommendation"] = "Review flagged instances and replace causal language with associational language"
    else:
        report["summary"]["compliance_status"] = "PASS"
        report["summary"]["recommendation"] = "All reports use appropriate associational language"
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Main entry point for the audit script."""
    # Default paths
    results_dir = "data/processed"
    output_path = "data/processed/associational_language_audit.json"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        results_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    print(f"Auditing associational language compliance...")
    print(f"Results directory: {results_dir}")
    print(f"Output file: {output_path}")
    
    report = generate_audit_report(results_dir, output_path)
    
    print(f"\nAudit Summary:")
    print(f"  Files audited: {report['summary']['total_files']}")
    print(f"  Total findings: {report['summary']['total_findings']}")
    print(f"  Compliance status: {report['summary']['compliance_status']}")
    
    if report["summary"]["compliance_status"] == "REVIEW_REQUIRED":
        print(f"\n⚠️  CAUSAL LANGUAGE DETECTED:")
        for file_report in report["files_audited"]:
            if file_report["total_findings"] > 0:
                print(f"  - {file_report['file']} ({file_report['total_findings']} findings)")
                for finding in file_report["findings"][:5]:  # Show first 5
                    print(f"    Pattern: {finding.get('pattern', finding.get('row', 'N/A'))}")
                    print(f"    Context: {finding.get('context', 'N/A')}")
        print(f"\n  Recommendation: {report['summary']['recommendation']}")
    else:
        print(f"\n✅ All reports comply with associational language requirements.")
    
    print(f"\nAudit report saved to: {output_path}")
    return report

if __name__ == "__main__":
    main()
