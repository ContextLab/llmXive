"""
Audit script to review all generated reports for "associational" language compliance
and scope adherence as per FR-007 and SC-002.

This script scans JSON and CSV reports to ensure:
1. No causal language (e.g., "causes", "determines", "leads to") is used where only association exists.
2. All required fields from the schema are present.
3. Sensitivity analysis results (absolute difference) are explicitly reported.
4. The report explicitly frames findings as "associational" or "correlational".
"""
import os
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure reports directory exists
REPORTS_DIR.mkdir(exist_ok=True)

# Causal language patterns to flag
CAUSAL_PATTERNS = [
    r'\bcauses?\b',
    r'\bdetermines?\b',
    r'\bleads to\b',
    r'\bresults in\b',
    r'\btriggers?\b',
    r'\beffects?\b', # As a verb
    r'\binfluences?\b', # Often acceptable but flagged for review
    r'\bpredicts?\b', # In the sense of "X predicts Y" implies causality in some contexts
    r'\bdrives?\b',
    r'\bgoverns?\b',
    r'\bcontrols?\b',
]

# Required associational phrases
ASSOCIATIONAL_PHRASES = [
    r'\bassociat[io]n\b',
    r'\bcorrelat[io]n\b',
    r'\brelation[io]n\b',
    r'\blink\b',
    r'\bassociat[io]nal\b',
    r'\bcorrelational\b',
    r'\bstatistically associa[te]d\b',
]

def load_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {filepath}: {e}")
        return None

def load_csv_file(filepath: Path) -> Optional[List[Dict[str, Any]]]:
    """Load a CSV file as a list of dictionaries."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def check_text_for_causality(text: str, line_num: int = 0) -> List[Tuple[int, str, str]]:
    """
    Check text for causal language patterns.
    Returns a list of (line_number, matched_pattern, context) tuples.
    """
    issues = []
    text_lower = text.lower()
    
    for pattern in CAUSAL_PATTERNS:
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            # Get context (surrounding 50 chars)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].replace('\n', ' ').strip()
            if len(context) > 100:
                context = context[:100] + "..."
            
            issues.append((line_num, pattern, context))
    
    return issues

def scan_report_json(filepath: Path) -> Dict[str, Any]:
    """Scan a JSON report file for language issues and required fields."""
    data = load_json_file(filepath)
    if data is None:
        return {"status": "error", "message": "Failed to load file"}
    
    issues = []
    required_fields = [
        "correlation_results", "sensitivity_analysis", "absolute_difference", 
        "associational_framing", "exclusion_log"
    ]
    
    # Check for required top-level fields
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        issues.append({
            "type": "missing_field",
            "fields": missing_fields
        })
    
    # Check text content recursively
    def traverse(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                traverse(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                traverse(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            text_issues = check_text_for_causality(obj)
            for line_num, pattern, context in text_issues:
                issues.append({
                    "type": "causal_language",
                    "path": path,
                    "pattern": pattern,
                    "context": context
                })
    
    traverse(data)
    
    # Check for associational framing
    has_associational = any(re.search(p, json.dumps(data).lower()) for p in ASSOCIATIONAL_PHRASES)
    if not has_associational:
        issues.append({
            "type": "missing_associational_framing",
            "message": "No explicit associational language found in the report"
        })
    
    return {
        "file": str(filepath),
        "status": "warning" if issues else "pass",
        "issues": issues
    }

def scan_csv_file(filepath: Path) -> Dict[str, Any]:
    """Scan a CSV file for required columns and issues."""
    data = load_csv_file(filepath)
    if data is None:
        return {"status": "error", "message": "Failed to load file"}
    
    issues = []
    
    # Check for required columns
    if "sensitivity_comparison.csv" in str(filepath):
        required_cols = ["metric_pair", "baseline_r", "sensitivity_r", "absolute_difference"]
        if data:
            first_row = data[0]
            missing_cols = [c for c in required_cols if c not in first_row]
            if missing_cols:
                issues.append({
                    "type": "missing_column",
                    "columns": missing_cols
                })
    
    return {
        "file": str(filepath),
        "status": "warning" if issues else "pass",
        "issues": issues
    }

def generate_audit_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary audit report."""
    total_files = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    warnings = sum(1 for r in results if r.get("status") == "warning")
    errors = sum(1 for r in results if r.get("status") == "error")
    
    all_issues = []
    for r in results:
        if r.get("issues"):
            all_issues.extend(r["issues"])
    
    return {
        "summary": {
            "total_files_scanned": total_files,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
            "compliance_rate": f"{(passed / total_files * 100):.1f}%" if total_files > 0 else "0%"
        },
        "issues_found": all_issues,
        "recommendations": [
            "Replace causal language with associational terms (e.g., 'associated with' instead of 'causes')",
            "Ensure all reports explicitly state findings are correlational/associational",
            "Verify sensitivity analysis includes absolute difference calculations"
        ]
    }

def main():
    """Main entry point for the audit script."""
    print("Starting associational language audit...")
    
    # Define files to scan
    files_to_scan = []
    
    # Scan processed data files
    if PROCESSED_DIR.exists():
        for file_path in PROCESSED_DIR.glob("*.csv"):
            files_to_scan.append(file_path)
        for file_path in PROCESSED_DIR.glob("*.json"):
            files_to_scan.append(file_path)
    
    # Scan logs
    if LOGS_DIR.exists():
        for file_path in LOGS_DIR.glob("*.json"):
            files_to_scan.append(file_path)
    
    # Scan reports directory if it exists
    if REPORTS_DIR.exists():
        for file_path in REPORTS_DIR.glob("*.json"):
            files_to_scan.append(file_path)
        for file_path in REPORTS_DIR.glob("*.csv"):
            files_to_scan.append(file_path)
    
    # Also check the main report file if it exists
    main_report = REPORTS_DIR / "final_report.json"
    if main_report.exists():
        files_to_scan.append(main_report)
    
    # Scan each file
    results = []
    for file_path in files_to_scan:
        if file_path.suffix == '.json':
            result = scan_report_json(file_path)
        elif file_path.suffix == '.csv':
            result = scan_csv_file(file_path)
        else:
            continue
        
        results.append(result)
        print(f"Scanned: {file_path} - {result['status']}")
    
    # Generate summary report
    audit_summary = generate_audit_report(results)
    
    # Save audit report
    audit_report_path = REPORTS_DIR / "associational_language_audit.json"
    with open(audit_report_path, 'w', encoding='utf-8') as f:
        json.dump(audit_summary, f, indent=2)
    
    print(f"\nAudit complete. Summary saved to: {audit_report_path}")
    print(f"Compliance rate: {audit_summary['summary']['compliance_rate']}")
    
    if audit_summary['summary']['errors'] > 0:
        print("⚠️  ERRORS FOUND - Manual review required")
        sys.exit(1)
    elif audit_summary['summary']['warnings'] > 0:
        print("⚠️  WARNINGS FOUND - Review recommended")
        sys.exit(0)
    else:
        print("✅ All checks passed - Language is compliant")
        sys.exit(0)

if __name__ == "__main__":
    main()