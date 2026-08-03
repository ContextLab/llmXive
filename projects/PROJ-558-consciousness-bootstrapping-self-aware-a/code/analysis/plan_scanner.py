"""
Plan Scanner for T003a: Identify occurrences of 'Teacher-Student Distillation',
'Pre-computed Teacher Labels', or 'external truth' in plan.md.

This script scans the plan.md file and outputs a JSON report listing line numbers
and context for any matches found.
"""
import os
import json
import re
from typing import List, Dict, Any
from pathlib import Path

# Define the patterns to search for
PATTERNS = [
    r"Teacher-Student Distillation",
    r"Pre-computed Teacher Labels",
    r"external truth"
]

def scan_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Scan a file for the defined patterns and return a list of matches.
    
    Args:
        file_path: Path to the file to scan.
        
    Returns:
        A list of dictionaries containing line number, context, and matched pattern.
    """
    matches = []
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return matches
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, start=1):
        for pattern in PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                matches.append({
                    "line_number": line_num,
                    "context": line.strip(),
                    "pattern_matched": pattern
                })
    
    return matches

def main():
    """Main function to run the plan scanner."""
    # Determine the path to plan.md relative to the project root
    # Assuming the script is run from the project root or code/analysis/
    project_root = Path(__file__).resolve().parent.parent.parent
    plan_path = project_root / "plan.md"
    
    print(f"Scanning {plan_path} for forbidden patterns...")
    
    matches = scan_file(str(plan_path))
    
    if matches:
        print(f"\nFound {len(matches)} occurrence(s):\n")
        report = {
            "file": str(plan_path),
            "total_matches": len(matches),
            "matches": matches
        }
        print(json.dumps(report, indent=2))
        
        # Save the report to a JSON file for T003b to use
        output_path = project_root / "artifacts" / "plan_scan_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to: {output_path}")
    else:
        print("\nNo occurrences found.")
        # Still create an empty report for consistency
        report = {
            "file": str(plan_path),
            "total_matches": 0,
            "matches": []
        }
        output_path = project_root / "artifacts" / "plan_scan_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"Empty report saved to: {output_path}")

if __name__ == "__main__":
    main()
