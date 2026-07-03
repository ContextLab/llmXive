"""
Task T032: Remove all 8-bit/4-bit quantization imports and verify no CUDA imports.

This script scans all Python files in the project to ensure:
1. No 8-bit/4-bit quantization imports (bitsandbytes, auto_gptq, etc.)
2. No explicit CUDA imports or device specifications
3. Only CPU-compatible code remains

Output: A verification report at results/compute_feasibility_report.md
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import List, Dict, Set, Tuple

# Patterns that indicate prohibited imports
QUANTIZATION_PATTERNS = [
    r'from\s+bitsandbytes',
    r'import\s+bitsandbytes',
    r'from\s+auto_gptq',
    r'import\s+auto_gptq',
    r'from\s+awq',
    r'import\s+awq',
    r'from\s+llama_cpp',
    r'import\s+llama_cpp',
    r'load_in_8bit\s*=',
    r'load_in_4bit\s*=',
    r'from_pretrained.*load_in_8bit',
    r'from_pretrained.*load_in_4bit',
    r'torch\.int8',
    r'torch\.int4',
    r'bitsandbytes\.nn\.Linear8bitLt',
    r'bitsandbytes\.nn\.Linear4bit',
]

CUDA_PATTERNS = [
    r'import\s+torch\.cuda',
    r'torch\.cuda\.is_available',
    r'torch\.cuda\.device_count',
    r'device\s*=\s*["\']cuda["\']',
    r'device\s*=\s*torch\.device\(["\']cuda',
    r'\.cuda\(\)',
    r'\.to\(["\']cuda["\']',
    r'\.to\(torch\.cuda',
    r'torch\.set_default_tensor_type.*cuda',
    r'os\.environ\["CUDA_VISIBLE_DEVICES"\]',
    r'torch\.backends\.cuda',
]

# Patterns that are acceptable (CPU-only or device-agnostic)
ALLOWED_PATTERNS = [
    r'device\s*=\s*["\']cpu["\']',
    r'device\s*=\s*torch\.device\(["\']cpu',
    r'torch\.device\(["\']cpu["\']\)',
    r'device\s*=\s*None',
    r'#\s*TODO.*cuda',
    r'#\s*FIXME.*cuda',
]


def line_is_prohibited(line: str, line_num: int, file_path: str) -> List[Tuple[str, str]]:
    """Check if a line contains prohibited patterns."""
    issues = []

    # Skip comments
    stripped = line.strip()
    if stripped.startswith('#'):
        return issues

    # Check quantization patterns
    for pattern in QUANTIZATION_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Check if it's in an allowed context
            is_allowed = False
            for allowed in ALLOWED_PATTERNS:
                if re.search(allowed, line, re.IGNORECASE):
                    is_allowed = True
                    break
            if not is_allowed:
                issues.append(('QUANTIZATION', pattern))

    # Check CUDA patterns
    for pattern in CUDA_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Check if it's in an allowed context
            is_allowed = False
            for allowed in ALLOWED_PATTERNS:
                if re.search(allowed, line, re.IGNORECASE):
                    is_allowed = True
                    break
            if not is_allowed:
                issues.append(('CUDA', pattern))

    return issues


def process_file(file_path: pathlib.Path) -> Dict:
    """Process a single Python file and return issues found."""
    issues = []
    lines_checked = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                lines_checked += 1
                file_issues = line_is_prohibited(line, line_num, str(file_path))
                for issue_type, pattern in file_issues:
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'type': issue_type,
                        'pattern': pattern,
                        'content': line.strip()
                    })
    except Exception as e:
        issues.append({
            'file': str(file_path),
            'line': 0,
            'type': 'ERROR',
            'pattern': str(e),
            'content': f'Could not read file: {e}'
        })

    return {
        'path': str(file_path),
        'lines_checked': lines_checked,
        'issues': issues
    }


def main():
    """Main entry point for the verification script."""
    project_root = pathlib.Path(__file__).parent.parent

    # Find all Python files in the code directory
    code_dir = project_root / 'code'
    if not code_dir.exists():
        print(f"Error: code directory not found at {code_dir}")
        sys.exit(1)

    python_files = list(code_dir.rglob('*.py'))
    print(f"Found {len(python_files)} Python files to scan")

    all_results = []
    total_issues = 0

    for py_file in python_files:
        result = process_file(py_file)
        all_results.append(result)
        total_issues += len(result['issues'])

    # Generate report
    report_path = project_root / 'results' / 'compute_feasibility_report.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Compute Feasibility Verification Report\n\n")
        f.write(f"**Generated**: {pathlib.Path(__file__).stem}\n")
        f.write(f"**Files Scanned**: {len(python_files)}\n")
        f.write(f"**Total Issues Found**: {total_issues}\n\n")

        if total_issues == 0:
            f.write("## ✅ VERIFICATION PASSED\n\n")
            f.write("No prohibited quantization or CUDA imports found. ")
            f.write("The codebase is CPU-compatible and ready for execution.\n\n")
        else:
            f.write("## ❌ VERIFICATION FAILED\n\n")
            f.write("The following issues were found:\n\n")

            # Group by file
            by_file: Dict[str, List] = {}
            for result in all_results:
                if result['issues']:
                    by_file[result['path']] = result['issues']

            for file_path, issues in sorted(by_file.items()):
                f.write(f"### {file_path}\n\n")
                for issue in issues:
                    f.write(f"- Line {issue['line']}: **{issue['type']}**\n")
                    f.write(f"  - Pattern: `{issue['pattern']}`\n")
                    f.write(f"  - Content: `{issue['content']}`\n\n")

            f.write("## Recommendations\n\n")
            f.write("1. Remove all 8-bit/4-bit quantization imports\n")
            f.write("2. Replace CUDA device specifications with CPU\n")
            f.write("3. Use `device='cpu'` or device-agnostic code\n")
            f.write("4. Ensure all model loading uses default (float32, CPU) settings\n\n")

    print(f"Verification complete. Found {total_issues} issues.")
    print(f"Report written to: {report_path}")

    if total_issues > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()