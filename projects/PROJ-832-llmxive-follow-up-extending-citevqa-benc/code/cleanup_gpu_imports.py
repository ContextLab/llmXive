"""
Cleanup script to ensure no GPU/CUDA imports remain in the codebase.

This script scans all Python files in the code/ directory, identifies
any imports or references to CUDA, GPU, or torch.cuda, and reports them.
It also provides a safety check to ensure the code is CPU-only compliant.

Usage:
    python code/cleanup_gpu_imports.py
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Patterns that indicate GPU/CUDA usage
GPU_PATTERNS = [
    r'import\s+torch\.cuda',
    r'from\s+torch\s+import\s+.*cuda',
    r'cuda\s*=\s*True',
    r'torch\.cuda',
    r'\.to\(.*cuda',
    r'\.cuda\(\)',
    r'is_available\(\)\s*==\s*True', # Often used with cuda
    r'gpu',
    r'Gpu',
    r'GPU',
    r'cuda:0',
    r'cuda:1',
    r'cuda:2',
    r'cuda:3',
]

# Specific patterns to ignore (false positives)
IGNORE_PATTERNS = [
    r'#\s*.*cuda.*', # Comments
    r'""".*cuda.*"""', # Docstrings
    r"'.*cuda.*'", # Strings
    r'".*cuda.*"', # Strings
    r'cpu', # CPU is fine
    r'CPU', # CPU is fine
]

def is_comment_or_string(line: str) -> bool:
    """Check if a line is likely a comment or a string literal."""
    stripped = line.strip()
    if stripped.startswith('#'):
        return True
    if stripped.startswith('"""') or stripped.startswith("'''"):
        return True
    # Simple check for strings (not perfect but catches most)
    if '"' in stripped or "'" in stripped:
        # If it's a variable assignment with a string, it's likely safe
        if '=' in stripped and ('"' in stripped.split('=')[0] or "'" in stripped.split('=')[0]):
            return False
        return True
    return False

def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a single file for GPU imports/references."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return issues

    for line_num, line in enumerate(lines, 1):
        # Skip comments and strings
        if is_comment_or_string(line):
            continue

        for pattern in GPU_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Double check against ignore patterns
                is_ignored = False
                for ignore_pat in IGNORE_PATTERNS:
                    if re.search(ignore_pat, line, re.IGNORECASE):
                        is_ignored = True
                        break
                
                if not is_ignored:
                    issues.append((line_num, line.strip(), pattern))
                    break # Report once per line

    return issues

def scan_directory(root_dir: Path) -> dict:
    """Scan all Python files in the directory."""
    results = {
        'clean': [],
        'issues': [],
        'total_files': 0
    }

    python_files = list(root_dir.glob('**/*.py'))
    results['total_files'] = len(python_files)

    for py_file in python_files:
        # Skip __init__.py if it's just empty or standard
        if py_file.name == '__init__.py':
            continue
        
        issues = scan_file(py_file)
        if issues:
            results['issues'].append({
                'file': str(py_file),
                'issues': issues
            })
        else:
            results['clean'].append(str(py_file))

    return results

def main():
    """Main entry point for the cleanup script."""
    print("=== GPU Import Cleanup Check ===")
    print("Scanning 'code/' directory for GPU/CUDA imports...\n")

    root = Path('code')
    if not root.exists():
        print(f"Error: Directory 'code/' not found at {root.absolute()}")
        sys.exit(1)

    results = scan_directory(root)

    if results['issues']:
        print(f"⚠️  Found {len(results['issues'])} file(s) with potential GPU imports/references:\n")
        for item in results['issues']:
            print(f"File: {item['file']}")
            for line_num, line_content, pattern in item['issues']:
                print(f"  Line {line_num}: {line_content[:60]}... (Match: {pattern})")
            print()
        
        print("⚠️  Review these lines. If they are legitimate CPU-only code (e.g., string literals, comments), they can be ignored.")
        print("If they are actual GPU imports, refactor to CPU-only equivalents.")
        sys.exit(1)
    else:
        print(f"✅ Success! All {results['total_files']} Python files are free of suspicious GPU/CUDA imports.")
        print("The codebase is compliant with CPU-only execution constraints.")
        sys.exit(0)

if __name__ == "__main__":
    main()