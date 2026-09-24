"""
Audit script to detect and report hardcoded paths in the codebase.
Ensures all paths are derived from code/config.py.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

# Define patterns that indicate hardcoded paths
HARDCODED_PATTERNS = [
    r'["\'](/[\w/\.]+)["\']',  # Absolute paths like "/home/user/..."
    r'["\']([A-Za-z]:\\[\w\\\.]+)["\']',  # Windows absolute paths
    r'["\']([\w]+/[\w/\.]+\.csv)["\']',  # Relative paths to data files without config
    r'["\']([\w]+/[\w/\.]+\.json)["\']',  # Relative paths to json files without config
    r'["\']([\w]+/[\w/\.]+\.log)["\']',  # Relative paths to log files without config
    r'["\']([\w]+/[\w/\.]+\.txt)["\']',  # Relative paths to txt files without config
    r'["\']([\w]+/[\w/\.]+\.png)["\']',  # Relative paths to image files without config
]

# Known safe paths that are allowed to be hardcoded (e.g., config file itself)
SAFE_PATHS = {
    "config.yaml",
    "requirements.txt",
    ".flake8",
    "pyproject.toml",
}

# Expected config imports
CONFIG_IMPORT_PATTERNS = [
    r"from\s+config\s+import",
    r"import\s+config",
]

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in the given directory recursively."""
    return list(directory.rglob("*.py"))

def check_hardcoded_paths(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Check a Python file for hardcoded paths.
    Returns a list of (line_number, line_content, issue_description).
    """
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [(0, "", f"Error reading file: {e}")]

    for line_num, line in enumerate(lines, 1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        for pattern in HARDCODED_PATTERNS:
            matches = re.finditer(pattern, line)
            for match in matches:
                matched_path = match.group(1)
                
                # Check if it's a safe path
                if any(safe in matched_path for safe in SAFE_PATHS):
                    continue
                
                # Check if it's a config reference
                if "config" in matched_path.lower():
                    continue
                
                # Check if it's a standard library path (e.g., /usr/bin)
                if matched_path.startswith("/usr/") or matched_path.startswith("/etc/"):
                    continue
                
                # Check if it's a relative path that should use config
                if any(ext in matched_path for ext in ['.csv', '.json', '.log', '.txt', '.png', '.parquet']):
                    # This is likely a data/results file that should use config
                    issues.append((
                        line_num,
                        line.rstrip(),
                        f"Hardcoded data/results path detected: '{matched_path}'. Should use config path."
                    ))
                    break

    return issues

def check_config_usage(file_path: Path) -> bool:
    """Check if the file imports from config.py."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for pattern in CONFIG_IMPORT_PATTERNS:
            if re.search(pattern, content):
                return True
        return False
    except Exception:
        return False

def audit_codebase(code_dir: Path) -> Dict[str, List[Tuple[int, str, str]]]:
    """
    Audit the entire codebase for hardcoded paths.
    Returns a dictionary mapping file paths to their issues.
    """
    results = {}
    python_files = find_python_files(code_dir)
    
    print(f"Auditing {len(python_files)} Python files in {code_dir}...")
    
    for file_path in python_files:
        issues = check_hardcoded_paths(file_path)
        if issues:
            results[str(file_path)] = issues
        
        # Check if file uses config
        if not check_config_usage(file_path):
            # Only warn for non-test files
            if "test" not in str(file_path):
                print(f"⚠️  {file_path} does not import from config.py")
    
    return results

def generate_report(results: Dict[str, List[Tuple[int, str, str]]]) -> str:
    """Generate a human-readable report of findings."""
    if not results:
        return "✅ No hardcoded paths detected. All paths appear to use config.py."
    
    report_lines = ["🔍 Hardcoded Path Audit Report", "=" * 40, ""]
    
    for file_path, issues in results.items():
        report_lines.append(f"📁 {file_path}:")
        for line_num, line_content, issue_desc in issues:
            report_lines.append(f"  Line {line_num}: {issue_desc}")
            report_lines.append(f"    {line_content}")
        report_lines.append("")
    
    report_lines.append(f"❌ Found {sum(len(v) for v in results.values())} hardcoded path issue(s) in {len(results)} file(s).")
    return "\n".join(report_lines)

def main():
    """Main entry point for the audit script."""
    # Determine project root
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"❌ Error: Code directory not found at {code_dir}")
        sys.exit(1)
    
    print(f"Starting hardcoded path audit at {code_dir}...")
    results = audit_codebase(code_dir)
    report = generate_report(results)
    
    print("\n" + report)
    
    # Exit with error code if issues found
    if results:
        print("\n⚠️  Please review and fix the hardcoded paths above.")
        print("   All data/results paths should be derived from code/config.py")
        sys.exit(1)
    else:
        print("\n✅ Audit passed: No hardcoded paths detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()