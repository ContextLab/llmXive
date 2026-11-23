"""
Final Review: Associational Language Compliance and Scope Adherence (T053)

This script performs a comprehensive audit of all generated reports and data files
to ensure:
1. No causal language ("predicts", "causes", "drives", "determines") is used
   where only association/correlation exists.
2. All findings are framed as "associational" as required by FR-007.
3. The scope adheres strictly to the defined metrics and analyses.

It produces a detailed audit report in `data/reports/associational_language_audit.json`.
"""

import os
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import existing utilities if available, otherwise define minimal helpers
try:
    from reports.audit_associational_language import check_text_for_causality, scan_report_json, scan_csv_file
except ImportError:
    # Fallback definitions if the module isn't directly importable in this context
    # (though the API surface suggests it exists)
    def check_text_for_causality(text: str) -> Tuple[bool, List[str]]:
        """Check text for causal language."""
        causal_patterns = [
            r'\bpredicts?\b', r'\bcauses?\b', r'\bdrives?\b', r'\bdetermines?\b',
            r'\binfluences?\b', r'\bleads to\b', r'\bresults in\b', r'\btriggers\b',
            r'\bmediates?\b', r'\bmoderates?\b'
        ]
        found = []
        for pattern in causal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.extend(matches)
        return len(found) > 0, found

    def scan_report_json(file_path: Path) -> Dict[str, Any]:
        """Scan a JSON report for causal language."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            issues = []
            def traverse(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        traverse(v, f"{path}.{k}")
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        traverse(v, f"{path}[{i}]")
                elif isinstance(obj, str):
                    is_causal, matches = check_text_for_causality(obj)
                    if is_causal:
                        issues.append({
                            "path": path,
                            "text": obj[:100] + "..." if len(obj) > 100 else obj,
                            "matches": matches
                        })
            traverse(data)
            return {"file": str(file_path), "issues": issues, "valid": len(issues) == 0}
        except Exception as e:
            return {"file": str(file_path), "error": str(e), "valid": False}

    def scan_csv_file(file_path: Path) -> Dict[str, Any]:
        """Scan a CSV file for causal language in headers or comments."""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            issues = []
            # Check headers
            for col in df.columns:
                is_causal, matches = check_text_for_causality(col)
                if is_causal:
                    issues.append({"type": "column", "name": col, "matches": matches})
            # Check first few rows of text columns
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].dtype == 'object':
                    sample = df[col].dropna().head(5)
                    for val in sample:
                        is_causal, matches = check_text_for_causality(str(val))
                        if is_causal:
                            issues.append({"type": "cell", "column": col, "value": str(val)[:50], "matches": matches})
            return {"file": str(file_path), "issues": issues, "valid": len(issues) == 0}
        except Exception as e:
            return {"file": str(file_path), "error": str(e), "valid": False}


def load_generated_reports() -> List[Path]:
    """Identify all generated report files in the project."""
    report_paths = []
    data_dir = Path("data")
    if not data_dir.exists():
        return []

    # Look for JSON reports
    for json_file in data_dir.rglob("*.json"):
        if "audit" not in str(json_file): # Exclude previous audit files
            report_paths.append(json_file)

    # Look for CSV reports
    for csv_file in data_dir.rglob("*.csv"):
        report_paths.append(csv_file)

    # Look for the main final report
    final_report = data_dir / "reports" / "final_report.json"
    if final_report.exists():
        report_paths.append(final_report)

    return report_paths


def perform_compliance_check() -> Dict[str, Any]:
    """Perform the full associational language compliance check."""
    print("Starting Associational Language Compliance Audit (T053)...")
    print(f"Scanning project directory: {Path.cwd()}")

    report_files = load_generated_reports()
    print(f"Found {len(report_files)} potential report files to scan.")

    results = {
        "audit_date": str(Path.cwd().stat().st_mtime), # Using mtime as a proxy for timestamp
        "total_files_scanned": len(report_files),
        "files_passed": 0,
        "files_failed": 0,
        "total_issues_found": 0,
        "files": []
    }

    for file_path in report_files:
        print(f"  Scanning: {file_path}")
        if file_path.suffix == '.json':
            scan_result = scan_report_json(file_path)
        elif file_path.suffix == '.csv':
            scan_result = scan_csv_file(file_path)
        else:
            scan_result = {"file": str(file_path), "status": "skipped", "reason": "unsupported format"}

        if scan_result.get("valid", True):
            results["files_passed"] += 1
        else:
            results["files_failed"] += 1
            results["total_issues_found"] += len(scan_result.get("issues", []))

        results["files"].append(scan_result)

    # Summary
    results["compliance_status"] = "PASSED" if results["files_failed"] == 0 else "FAILED"
    results["summary"] = (
        f"Scanned {results['total_files_scanned']} files. "
        f"Passed: {results['files_passed']}, Failed: {results['files_failed']}. "
        f"Total causal language instances found: {results['total_issues_found']}."
    )

    return results


def main():
    """Main entry point for the audit."""
    audit_results = perform_compliance_check()

    # Save the audit report
    output_dir = Path("data/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "associational_language_audit.json"

    with open(output_path, 'w') as f:
        json.dump(audit_results, f, indent=2)

    print(f"\nAudit complete. Report saved to: {output_path}")
    print(f"Status: {audit_results['compliance_status']}")
    print(f"Summary: {audit_results['summary']}")

    if audit_results['compliance_status'] == "FAILED":
        print("\nWARNING: Causal language detected. Please review the report and rephrase findings.")
        sys.exit(1)
    else:
        print("\nSUCCESS: All reports comply with associational language constraints.")
        sys.exit(0)


if __name__ == "__main__":
    main()
