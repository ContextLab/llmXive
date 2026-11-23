"""
Verification script for T021d.
Asserts that data/raw/repo_selection_rubric.json exists and contains the required schema.
"""
import json
import os
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    output_path = base_dir / "data" / "raw" / "repo_selection_rubric.json"
    
    if not os.path.exists(output_path):
        print(f"FAIL: Output file not found: {output_path}")
        sys.exit(1)
    
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"FAIL: Invalid JSON in {output_path}")
        sys.exit(1)
    
    required_keys = ["selected_repos", "tolerance_check"]
    for key in required_keys:
        if key not in data:
            print(f"FAIL: Missing key '{key}' in output")
            sys.exit(1)
    
    if not isinstance(data["tolerance_check"], dict):
        print("FAIL: tolerance_check must be a dictionary")
        sys.exit(1)
    
    if "loc" not in data["tolerance_check"] or "cc" not in data["tolerance_check"]:
        print("FAIL: tolerance_check must contain 'loc' and 'cc' booleans")
        sys.exit(1)
    
    if not isinstance(data["selected_repos"], list):
        print("FAIL: selected_repos must be a list")
        sys.exit(1)
    
    print("PASS: T021d output verification successful.")
    print(f"  - Selected repos: {len(data['selected_repos'])}")
    print(f"  - Tolerance check (loc): {data['tolerance_check']['loc']}")
    print(f"  - Tolerance check (cc): {data['tolerance_check']['cc']}")
    sys.exit(0)

if __name__ == "__main__":
    main()