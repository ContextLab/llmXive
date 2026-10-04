"""
Audit script to review all generated reports for "associational" language compliance
and scope adherence as per FR-007 and Constitution Principle VI.

This script scans:
1. Final JSON report (data/reports/final_report.json)
2. Correlation results CSV (data/processed/correlation_results.csv)
3. Sensitivity analysis CSVs
4. Exclusion logs and completeness reports

It flags any usage of causal language (e.g., "predict", "cause", "determine",
"effect", "impact", "influence" in a causal context) and ensures the framing
remains strictly associational/correlational.
"""
import os
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Define patterns for causal language that should be flagged
CAUSAL_PATTERNS = [
    r'\bpredict\b',
    r'\bcause\b',
    r'\bdetermine\b',
    r'\beffect\b',
    r'\bimpact\b',
    r'\binfluence\b',
    r'\bdrive\b',
    r'\bgovern\b',
    r'\bcontrol\b',
    r'\bmechanism\b',
    r'\bcausation\b',
    r'\bcausal\b',
]

# Define acceptable associational language
ASSOCIATIONAL_PATTERNS = [
    r'\bassociate\b',
    r'\bcorrelate\b',
    r'\brelate\b',
    r'\brelationship\b',
    r'\bassociation\b',
    r'\bcorrelation\b',
    r'\blinked\b',
    r'\bconnected\b',
    r'\bcorrespond\b',
    r'\bmatch\b',
]

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        print(f"Warning: {file_path} does not exist. Skipping.")
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_csv_file(file_path: Path) -> List[str]:
    """Load a CSV file and return all text content as a list of strings."""
    if not file_path.exists():
        print(f"Warning: {file_path} does not exist. Skipping.")
        return []
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        # Convert all columns to string and join
        content = []
        for col in df.columns:
            content.extend(df[col].astype(str).tolist())
        return content
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def check_text_for_causality(text: str, file_context: str = "") -> List[Dict[str, Any]]:
    """
    Check a text string for causal language patterns.
    Returns a list of findings with context.
    """
    findings = []
    text_lower = text.lower()

    for pattern in CAUSAL_PATTERNS:
        if re.search(pattern, text_lower):
            # Find the specific match and surrounding context
            match = re.search(pattern, text_lower)
            if match:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                findings.append({
                    "pattern": pattern,
                    "match": match.group(),
                    "context": context,
                    "file_context": file_context
                })

    return findings

def scan_report_json(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a JSON report file for causal language."""
    findings = []
    data = load_json_file(file_path)
    if not data:
        return findings

    # Recursively scan all string values
    def scan_dict(d: Dict, path: str = ""):
        for key, value in d.items():
            current_path = f"{path}.{key}" if path else key
            if isinstance(value, str):
                findings.extend(check_text_for_causality(value, current_path))
            elif isinstance(value, dict):
                scan_dict(value, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        findings.extend(check_text_for_causality(item, f"{current_path}[{i}]"))
                    elif isinstance(item, dict):
                        scan_dict(item, f"{current_path}[{i}]")

    scan_dict(data)
    return findings

def scan_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a CSV file for causal language."""
    findings = []
    content = load_csv_file(file_path)
    for i, text in enumerate(content):
        findings.extend(check_text_for_causality(text, f"row_{i}"))
    return findings

def generate_audit_report(findings: List[Dict[str, Any]], file_path: Path) -> Dict[str, Any]:
    """Generate a structured audit report."""
    report = {
        "audit_timestamp": str(Path(file_path).parent.name),  # Simplified timestamp
        "total_findings": len(findings),
        "findings": findings,
        "compliance_status": "PASSED" if len(findings) == 0 else "NEEDS_REVIEW",
        "recommendations": []
    }

    if findings:
        report["recommendations"].append(
            "Review flagged instances of causal language. "
            "Replace with associational terms (e.g., 'associated with', 'correlated with'). "
            "Ensure all conclusions are framed as correlational, not causal."
        )
        report["recommendations"].append(
            "Verify that the final report explicitly states the associational nature "
            "of the findings as required by FR-007."
        )

    return report

def main():
    """Main function to run the audit."""
    project_root = Path(__file__).resolve().parent.parent.parent
    reports_dir = project_root / "data" / "reports"
    processed_dir = project_root / "data" / "processed"

    all_findings = []

    # Files to audit
    files_to_audit = [
        (reports_dir / "final_report.json", "JSON Report"),
        (processed_dir / "correlation_results.csv", "Correlation Results"),
        (processed_dir / "sensitivity_comparison.csv", "Sensitivity Comparison"),
        (processed_dir / "structural_density_sensitivity.csv", "Density Sensitivity"),
        (processed_dir / "tractography_sensitivity_metrics.csv", "Tractography Sensitivity"),
        (processed_dir / "tractography_correlation_sensitivity.csv", "Tractography Correlation Sensitivity"),
        (processed_dir / "completeness_report.json", "Completeness Report"),
    ]

    print("Starting associational language audit...")
    print("=" * 60)

    for file_path, description in files_to_audit:
        if not file_path.exists():
            print(f"Skipping {description}: {file_path.name} not found")
            continue

        print(f"Auditing {description}...")
        if file_path.suffix == '.json':
            findings = scan_report_json(file_path)
        elif file_path.suffix == '.csv':
            findings = scan_csv_file(file_path)
        else:
            continue

        if findings:
            print(f"  Found {len(findings)} potential causal language instances")
            all_findings.extend(findings)
        else:
            print(f"  No issues found")

    # Generate final report
    output_path = reports_dir / "associational_language_audit.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audit_report = generate_audit_report(all_findings, output_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"Audit complete. Found {audit_report['total_findings']} issues.")
    print(f"Status: {audit_report['compliance_status']}")
    print(f"Report saved to: {output_path}")

    if audit_report['compliance_status'] == "NEEDS_REVIEW":
        print("\nRecommendations:")
        for rec in audit_report['recommendations']:
            print(f"  - {rec}")
        sys.exit(1)  # Exit with error code to indicate review needed
    else:
        print("\nAll reports comply with associational language requirements.")
        sys.exit(0)

if __name__ == "__main__":
    main()