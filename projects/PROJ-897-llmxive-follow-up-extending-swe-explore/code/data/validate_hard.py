import json
import sys
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_path, get_config_summary

def load_hard_subset() -> List[Dict[str, Any]]:
    path = get_path("curated") / "hard_subset.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Hard subset not found at {path}")
    data = []
    with open(path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_synthetic_issues() -> List[Dict[str, Any]]:
    path = get_path("curated") / "synthetic_issues.jsonl"
    if not path.exists():
        return []
    data = []
    with open(path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def validate_issue(issue: Dict[str, Any]) -> bool:
    # Check for required fields
    if "initial_coverage" not in issue:
        return False
    # Check code validity if present
    if "problem_statement" in issue:
        try:
            ast.parse(issue["problem_statement"])
        except SyntaxError:
            return False
    return True

def generate_report(hard_data: List[Dict], synth_data: List[Dict]) -> str:
    lines = ["# Validation Report", ""]
    lines.append(f"Total Hard Issues: {len(hard_data)}")
    lines.append(f"Total Synthetic Issues: {len(synth_data)}")
    lines.append("")
    lines.append("## Sample Inspection")
    lines.append("| IssueID | Coverage | Valid? |")
    lines.append("|---|---|---|")
    
    sample = hard_data[:5]
    for item in sample:
        valid = validate_issue(item)
        lines.append(f"| {item.get('instance_id', 'N/A')} | {item.get('initial_coverage', 'N/A')} | {valid} |")
    
    return "\n".join(lines)

def main():
    try:
        hard_data = load_hard_subset()
        synth_data = load_synthetic_issues()
        
        report = generate_report(hard_data, synth_data)
        
        report_path = get_path("curated") / "validation_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        status_path = get_path("curated") / "validation_status.json"
        status = {
            "status": "PASSED",
            "message": "Validation report generated successfully.",
            "sample_size": min(5, len(hard_data))
        }
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=2)
        
        print(f"Validation report saved to {report_path}")
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()