"""
Verification script for T032: Compute Feasibility Check.

This script verifies that:
1. No 8-bit/4-bit quantization imports exist in the codebase.
2. No CUDA-specific imports or device assignments exist.
3. All imports are compatible with CPU-only execution.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import List, Dict

# Patterns that indicate GPU/quantization dependencies
PROHIBITED_IMPORTS = [
    r'import\s+bitsandbytes',
    r'from\s+bitsandbytes',
    r'load_in_8bit',
    r'load_in_4bit',
    r'bnb',
    r'torch\.cuda',
    r'cuda:',
    r'device\s*=\s*[\'"]cuda',
    r'device\s*=\s*torch\.cuda',
    r'accelerate',  # Often used for GPU distribution
    r'deepspeed',   # GPU-specific optimization
]

# Allowed imports for CPU-only execution
ALLOWED_IMPORTS = [
    'torch',
    'transformers',
    'numpy',
    'pandas',
    'scipy',
    'matplotlib',
    'sklearn',
    'statsmodels',
]


def check_file(file_path: pathlib.Path) -> List[str]:
    """Check a single file for prohibited imports."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        issues.append(f"Error reading {file_path}: {e}")
        return issues

    for i, line in enumerate(lines, 1):
        # Skip comments and strings
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        for pattern in PROHIBITED_IMPORTS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(f"Line {i}: {stripped}")
                break

    return issues


def main():
    """Main verification routine."""
    project_root = pathlib.Path(__file__).parent.parent
    code_dir = project_root / 'code'

    if not code_dir.exists():
        print(f"Error: code directory not found at {code_dir}")
        sys.exit(1)

    py_files = list(code_dir.rglob('*.py'))
    print(f"Checking {len(py_files)} Python files for GPU/quantization dependencies...")

    all_issues: Dict[pathlib.Path, List[str]] = {}

    for file_path in py_files:
        issues = check_file(file_path)
        if issues:
            all_issues[file_path] = issues

    # Generate report
    report_path = project_root / 'results' / 'compute_feasibility_report.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Compute Feasibility Verification Report\n\n")
        f.write(f"**Date**: {pathlib.Path(__file__).name} executed\n")
        f.write(f"**Files Scanned**: {len(py_files)}\n")
        f.write(f"**Files with Issues**: {len(all_issues)}\n\n")

        if all_issues:
            f.write("## Issues Found\n\n")
            for file_path, issues in all_issues.items():
                f.write(f"### {file_path.relative_to(project_root)}\n\n")
                for issue in issues:
                    f.write(f"- {issue}\n")
                f.write("\n")
            f.write("## VERIFICATION FAILED\n\n")
            f.write("The codebase still contains prohibited GPU/quantization imports.\n")
        else:
            f.write("## Verification Passed\n\n")
            f.write("All Python files are compatible with CPU-only execution.\n")
            f.write("No 8-bit/4-bit quantization or CUDA-specific imports detected.\n")

    print(f"\nReport written to {report_path}")

    if all_issues:
        print("VERIFICATION FAILED: Prohibited imports detected.")
        for file_path, issues in all_issues.items():
            print(f"\n{file_path}:")
            for issue in issues:
                print(f"  {issue}")
        sys.exit(1)
    else:
        print("VERIFICATION PASSED: Codebase is CPU-compatible.")
        sys.exit(0)


if __name__ == '__main__':
    main()