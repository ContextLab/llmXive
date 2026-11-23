import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

def load_json_lines(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON lines from a file."""
    records = []
    if not file_path.exists():
        return records
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.stderr.write(f"Warning: Failed to parse JSON at {file_path}:{line_num}: {e}\n")
    return records

def aggregate_edge_cases(
    edge_cases_log_path: Path,
    filtered_log_path: Path
) -> Dict[str, Any]:
    """
    Aggregate edge case data from edge_cases.log and edge_cases_filtered.log.
    Returns a summary dictionary.
    """
    edge_case_records = load_json_lines(edge_cases_log_path)
    filtered_records = load_json_lines(filtered_log_path)

    by_reason = defaultdict(int)
    by_workflow_type = defaultdict(int)
    total_edge_cases = len(edge_case_records)
    filtered_count = len(filtered_records)

    for record in edge_case_records:
        reason = record.get("reason", "unknown")
        by_reason[reason] += 1
        # Attempt to categorize by workflow type if available
        wf_type = record.get("workflow_type", "unknown")
        by_workflow_type[wf_type] += 1

    return {
        "total_edge_cases": total_edge_cases,
        "filtered_count": filtered_count,
        "by_reason": dict(by_reason),
        "by_workflow_type": dict(by_workflow_type),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def generate_edge_case_audit_report(
    summary_data: Dict[str, Any],
    edge_cases_log_path: Path,
    filtered_log_path: Path
) -> Dict[str, Any]:
    """
    Generate a comprehensive audit report including the summary and file existence status.
    """
    report = {
        "summary": summary_data,
        "source_files": {
            "edge_cases_log": str(edge_cases_log_path),
            "edge_cases_filtered_log": str(filtered_log_path),
            "edge_cases_log_exists": edge_cases_log_path.exists(),
            "edge_cases_filtered_log_exists": filtered_log_path.exists()
        },
        "status": "PASS" if edge_cases_log_path.exists() else "WARN: Source log missing"
    }
    return report

def save_audit_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the audit report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def main() -> None:
    """
    Main entry point for the edge case audit utility.
    Reads edge case logs and generates a summary report.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    edge_cases_log_path = project_root / "data" / "processed" / "edge_cases.log"
    filtered_log_path = project_root / "data" / "processed" / "edge_cases_filtered.log"
    output_path = project_root / "data" / "results" / "edge_case_summary.json"

    if not edge_cases_log_path.exists():
        sys.stderr.write(f"Warning: {edge_cases_log_path} does not exist. Creating empty summary.\n")
    if not filtered_log_path.exists():
        sys.stderr.write(f"Warning: {filtered_log_path} does not exist. Creating empty summary.\n")

    summary = aggregate_edge_cases(edge_cases_log_path, filtered_log_path)
    report = generate_edge_case_audit_report(summary, edge_cases_log_path, filtered_log_path)
    save_audit_report(report, output_path)

    print(f"Edge case audit report written to: {output_path}")

if __name__ == "__main__":
    main()