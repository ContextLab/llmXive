"""
Final Validation Script for Statistical and Causal Compliance.

This script validates that:
1. Statistical methods selected match data distribution checks.
2. No causal language slipped through in reports/logs.
"""
import json
import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime

def load_json_file(file_path: str) -> dict:
    """Load a JSON file and return its contents."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: str, data: dict):
    """Save data to a JSON file."""
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def validate_method_selection(method_log: dict) -> list:
    """
    Validate that method selection logic was followed correctly.
    
    Checks:
    - If data was zero-inflated, ZINB/Hurdle should be selected.
    - If non-normal, Spearman should be selected.
    - If normal, Pearson should be selected.
    
    Returns a list of validation issues (warnings/errors).
    """
    issues = []
    
    # Basic structure check
    if "method_selection_log" not in method_log:
        issues.append("ERROR: 'method_selection_log' key missing in input file.")
        return issues
    
    log_entries = method_log["method_selection_log"]
    
    if not isinstance(log_entries, list):
        issues.append("ERROR: 'method_selection_log' is not a list.")
        return issues
    
    for entry in log_entries:
        # Check for required fields
        if "data_type" not in entry or "method_selected" not in entry:
            issues.append(f"WARNING: Incomplete log entry: {entry}")
            continue
        
        data_type = entry["data_type"]
        method = entry["method_selected"]
        
        # Validate logic
        if data_type == "zero_inflated" and method not in ["ZINB", "Hurdle"]:
            issues.append(f"ERROR: Zero-inflated data should use ZINB/Hurdle, got {method}.")
        elif data_type == "non_normal" and method not in ["Spearman", "SparCC"]:
            issues.append(f"WARNING: Non-normal data should use Spearman/SparCC, got {method}.")
        elif data_type == "normal" and method not in ["Pearson", "SparCC"]:
            issues.append(f"WARNING: Normal data should use Pearson/SparCC, got {method}.")
    
    return issues

def scan_causal_language(file_path: str) -> list:
    """
    Scan a file for causal language violations.
    
    Regex pattern matches words like: causes, leads to, effect, causal.
    """
    violations = []
    pattern = re.compile(r'\b(causes|leads to|effect|causal)\b', re.IGNORECASE)
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            matches = pattern.finditer(content)
            for match in matches:
                # Get context (line number)
                line_num = content[:match.start()].count('\n') + 1
                violations.append({
                    "file": file_path,
                    "line": line_num,
                    "match": match.group(),
                    "context": match.group()
                })
    except FileNotFoundError:
        pass  # File not found is handled by the caller
    
    return violations

def run_validation_pipeline(
    method_log_path: str,
    report_paths: list,
    output_path: str
) -> dict:
    """
    Run the full validation pipeline.
    
    Args:
        method_log_path: Path to method_selection_log.json
        report_paths: List of paths to report files to scan for causal language
        output_path: Path to write the validation report
    
    Returns:
        Validation report dict
    """
    report = {
        "timestamp": str(datetime.now()),
        "method_selection_validation": {
            "status": "PASSED",
            "issues": []
        },
        "causal_language_validation": {
            "status": "PASSED",
            "violations": []
        },
        "overall_status": "PASSED"
    }
    
    # Validate method selection
    if os.path.exists(method_log_path):
        method_log = load_json_file(method_log_path)
        method_issues = validate_method_selection(method_log)
        report["method_selection_validation"]["issues"] = method_issues
        if any("ERROR" in issue for issue in method_issues):
            report["method_selection_validation"]["status"] = "FAILED"
            report["overall_status"] = "FAILED"
        elif method_issues:
            report["method_selection_validation"]["status"] = "WARNINGS"
    else:
        report["method_selection_validation"]["status"] = "SKIPPED"
        report["method_selection_validation"]["issues"].append("Input file not found.")
    
    # Scan for causal language
    for report_path in report_paths:
        if os.path.exists(report_path):
            violations = scan_causal_language(report_path)
            report["causal_language_validation"]["violations"].extend(violations)
    
    if report["causal_language_validation"]["violations"]:
        report["causal_language_validation"]["status"] = "FAILED"
        report["overall_status"] = "FAILED"
    
    # Write report
    save_json_file(output_path, report)
    return report

def main():
    parser = argparse.ArgumentParser(description="Run final validation of pipeline results.")
    parser.add_argument("--method-log", type=str, default="data/metadata/method_selection_log.json", help="Path to method selection log")
    parser.add_argument("--reports", type=str, nargs="+", default=["data/results/report_draft.md", "data/results/final_report.md"], help="Paths to report files to scan")
    parser.add_argument("--output", type=str, default="data/results/final_validation_report.json", help="Output validation report path")
    
    args = parser.parse_args()
    
    print("Starting final validation pipeline...")
    
    report = run_validation_pipeline(
        method_log_path=args.method_log,
        report_paths=args.reports,
        output_path=args.output
    )
    
    print(f"Validation report written to {args.output}")
    print(f"Overall Status: {report['overall_status']}")
    
    if report["overall_status"] == "FAILED":
        print("VALIDATION FAILED. Please review the report.")
        sys.exit(1)
    else:
        print("VALIDATION PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
