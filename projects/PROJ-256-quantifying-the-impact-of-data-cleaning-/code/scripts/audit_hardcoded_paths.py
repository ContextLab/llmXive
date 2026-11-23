"""
T1205: Audit all Python modules in code/ for hardcoded path strings.
Generates a report of all hardcoded paths found.
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any

# Common hardcoded path patterns to detect
HARDCODED_PATH_PATTERNS = [
    r'"data/raw/[^"]*"',
    r"'data/raw/[^']*'",
    r'"data/processed/[^"]*"',
    r"'data/processed/[^']*'",
    r'"output/figures/[^"]*"',
    r"'output/figures/[^']*'",
    r'"output/reports/[^"]*"',
    r"'output/reports/[^']*'",
    r'"data/raw"',
    r"'data/raw'",
    r'"data/processed"',
    r"'data/processed'",
    r'"output/figures"',
    r"'output/figures'",
    r'"output/reports"',
    r"'output/reports'",
]

# Patterns that should be ignored (these are config references or comments)
IGNORE_PATTERNS = [
    r'#.*',  # Comments
    r'config\.',  # Config references
    r'Path\(',  # Path constructor calls
    r'os\.path',  # os.path usage
    r'__file__',  # __file__ usage
]

def is_comment_or_string_context(line: str, match_start: int, match_end: int) -> bool:
    """Check if the match is inside a comment or a valid config reference."""
    # Check if it's in a comment
    if '#' in line[:match_start]:
        # Find the comment start
        comment_start = line.find('#')
        if comment_start < match_start:
            return True
    
    # Check for config references
    if 'config.' in line:
        return True
    
    return False

def audit_file(file_path: Path) -> List[Dict[str, Any]]:
    """Audit a single Python file for hardcoded paths."""
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return findings
    
    for line_num, line in enumerate(lines, 1):
        for pattern in HARDCODED_PATH_PATTERNS:
            matches = list(re.finditer(pattern, line))
            for match in matches:
                # Skip if it's in a comment or config reference
                if is_comment_or_string_context(line, match.start(), match.end()):
                    continue
                
                # Skip if it's part of a larger valid pattern (like config reference)
                if re.search(r'config\.[^"]*' + match.group(), line):
                    continue
                
                findings.append({
                    'file': str(file_path),
                    'line': line_num,
                    'content': line.strip(),
                    'matched_string': match.group(),
                    'pattern': pattern
                })
    
    return findings

def main():
    """Main function to audit all Python files in code/ directory."""
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / 'code'
    
    if not code_dir.exists():
        print(f"Error: code/ directory not found at {code_dir}")
        return
    
    all_findings = []
    
    # Audit all Python files in code/ directory
    for py_file in code_dir.rglob('*.py'):
        # Skip __pycache__ directories
        if '__pycache__' in str(py_file):
            continue
        
        findings = audit_file(py_file)
        all_findings.extend(findings)
    
    # Generate report
    report = {
        'total_files_audited': len(list(code_dir.rglob('*.py'))),
        'total_hardcoded_paths_found': len(all_findings),
        'findings': all_findings
    }
    
    # Write report to data/processed/audit_hardcoded_paths.json
    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / 'audit_hardcoded_paths.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Audit complete. Found {len(all_findings)} hardcoded path instances.")
    print(f"Report written to: {output_file}")
    
    # Also print summary to console
    if all_findings:
        print("\nHardcoded paths found:")
        for finding in all_findings[:20]:  # Show first 20
            print(f"  {finding['file']}:{finding['line']} - {finding['matched_string']}")
        if len(all_findings) > 20:
            print(f"  ... and {len(all_findings) - 20} more")

if __name__ == '__main__':
    main()
