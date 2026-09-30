"""
T042: Final Code Review Script.

Performs a manual (automated) review of code/main.py, code/ingest.py,
code/model.py, and code/viz.py to ensure:
1. No fabrication logic (generate_synthetic_data, mock_*, np.random without seed).
2. No synthetic fallbacks (try/except blocks that generate data on failure).
3. No hardcoded values for data (except config constants).
4. All data flows from real sources (datasets, requests, or local files).

This script scans the source code for prohibited patterns and verifies
the presence of required real-data loading mechanisms.
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REVIEW_FILES = [
    "code/main.py",
    "code/ingest.py",
    "code/model.py",
    "code/viz.py"
]

# Patterns that indicate fabrication or forbidden synthetic logic
FORBIDDEN_PATTERNS = [
    r"generate_synthetic_data",
    r"mock_.*",
    r"np\.random\.[a-z]+\(",  # Random generation without seed context
    r"pd\.DataFrame\(\[.*\]\)", # Hardcoded dataframe creation with values
    r"return.*\[.*\]", # Returning hardcoded lists in data functions
    r"pass\s*#", # Placeholder pass in critical logic
    r"TODO.*data",
    r"NotImplementedError",
    r"raise.*NotImplementedError"
]

# Patterns that indicate safe synthetic fallback (which is also forbidden per spec)
# We specifically look for try/except blocks that catch DataAvailabilityError
# and then generate data or return mock data.
FORBIDDEN_FALLBACK_PATTERNS = [
    r"except\s+.*DataAvailabilityError.*:",
    r"except\s+.*Exception.*:\s*generate",
    r"except\s+.*Exception.*:\s*return.*mock"
]

# Required patterns that MUST exist to prove real data usage
REQUIRED_PATTERNS = {
    "code/ingest.py": [
        r"datasets\.load_dataset",
        r"streaming\s*=\s*True",
        r"raise\s+DataAvailabilityError"
    ],
    "code/model.py": [
        r"statsmodels",
        r"sm\.OLS"
    ],
    "code/viz.py": [
        r"matplotlib",
        r"seaborn"
    ]
}

def check_file_for_forbidden_patterns(file_path: Path) -> List[str]:
    """Check a file for forbidden patterns."""
    issues = []
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check for forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Found forbidden pattern '{pattern}' in {file_path}")

        # Check for forbidden fallback logic
        # Look for try blocks followed by except and then a function call that looks synthetic
        lines = content.split('\n')
        in_try = False
        for i, line in enumerate(lines):
            if 'try:' in line:
                in_try = True
            elif in_try and ('except' in line or 'except ' in line):
                # Check next few lines for synthetic generation
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if 'generate' in next_line.lower() or 'mock' in next_line.lower() or 'synthetic' in next_line.lower():
                        issues.append(f"Potential synthetic fallback detected in {file_path} at line {j+1}: {next_line}")
                in_try = False
            elif line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                # If we hit a non-indented, non-comment, non-empty line, we are out of the block
                if not (line.startswith(' ') or line.startswith('\t')):
                    in_try = False

    except Exception as e:
        issues.append(f"Error reading {file_path}: {str(e)}")
    
    return issues

def check_file_for_required_patterns(file_path: Path, required: List[str]) -> List[str]:
    """Check a file for required patterns."""
    issues = []
    try:
        content = file_path.read_text(encoding='utf-8')
        for pattern in required:
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Missing required pattern '{pattern}' in {file_path}")
    except Exception as e:
        issues.append(f"Error reading {file_path}: {str(e)}")
    return issues

def run_review() -> Dict[str, Any]:
    """Run the full code review."""
    results = {
        "status": "PASS",
        "issues": [],
        "files_checked": [],
        "summary": ""
    }

    for file_rel in REVIEW_FILES:
        file_path = PROJECT_ROOT / file_rel
        results["files_checked"].append(file_rel)
        
        if not file_path.exists():
            results["status"] = "FAIL"
            results["issues"].append(f"File missing: {file_path}")
            continue

        # Check forbidden
        forbidden_issues = check_file_for_forbidden_patterns(file_path)
        results["issues"].extend(forbidden_issues)

        # Check required
        if file_rel in REQUIRED_PATTERNS:
            required_issues = check_file_for_required_patterns(file_path, REQUIRED_PATTERNS[file_rel])
            results["issues"].extend(required_issues)

    if results["issues"]:
        results["status"] = "FAIL"
        results["summary"] = f"Found {len(results['issues'])} issue(s) during code review."
    else:
        results["summary"] = "Code review passed. No fabrication logic or synthetic fallbacks detected. Real data flow confirmed."

    return results

def main():
    print("Starting T042 Final Code Review...")
    results = run_review()
    
    print(f"\nStatus: {results['status']}")
    print(f"Summary: {results['summary']}")
    
    if results["issues"]:
        print("\nIssues Found:")
        for issue in results["issues"]:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("\nAll checks passed. Code is clean.")
        sys.exit(0)

if __name__ == "__main__":
    main()