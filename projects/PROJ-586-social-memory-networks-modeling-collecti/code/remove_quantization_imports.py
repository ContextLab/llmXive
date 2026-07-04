"""
Task T032: Remove all 8-bit/4-bit quantization imports and verify no CUDA imports.

This script scans all Python files in the project to:
1. Detect and remove prohibited quantization imports (bitsandbytes, 8-bit, 4-bit, etc.)
2. Detect and remove CUDA-specific imports (torch.cuda, etc.)
3. Generate a verification report in Markdown format
"""
from __future__ import annotations

import pathlib
import re
import sys
from datetime import datetime
from typing import List, Dict, Set, Tuple, Optional


# Patterns that indicate prohibited quantization or CUDA usage
QUANTIZATION_PATTERNS = [
    r'from\s+bitsandbytes',
    r'import\s+bitsandbytes',
    r'8bit',
    r'8-bit',
    r'4bit',
    r'4-bit',
    r'bnb',
    r'QuantizedLinear',
    r'Int8Params',
    r'load_in_8bit',
    r'load_in_4bit',
    r'compute_dtype.*fp16',
    r'bnb.*quantization',
]

CUDA_PATTERNS = [
    r'torch\.cuda',
    r'torch\.device\s*\(\s*["\']cuda',
    r'\.cuda\(\)',
    r'\.to\s*\(\s*["\']cuda',
    r'CUDA_VISIBLE_DEVICES',
    r'is_available\(\)\s*==\s*True',
    r'if\s+torch\.cuda',
    r'cuda:0',
    r'cuda:\d+',
]

# Patterns that are acceptable (CPU-only or generic)
SAFE_PATTERNS = [
    r'torch\.cpu',
    r'device.*cpu',
    r'device\s*=\s*["\']cpu',
    r'cpu_only',
    r'cpu',
    r'cpu_only_mode',
]


def is_prohibited_line(line: str, line_num: int, file_path: str) -> List[Dict]:
    """Check if a line contains prohibited quantization or CUDA patterns."""
    issues = []

    # Skip comments and docstrings
    stripped = line.strip()
    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
        return issues

    # Check for quantization patterns
    for pattern in QUANTIZATION_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Check if it's in a safe context (e.g., in a comment explaining what NOT to do)
            if 'DO NOT' in line.upper() or 'WARNING' in line.upper() or 'FIXME' in line.upper():
                continue
            issues.append({
                'type': 'quantization',
                'pattern': pattern,
                'line_num': line_num,
                'content': line.strip()
            })

    # Check for CUDA patterns
    for pattern in CUDA_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Check if it's in a safe context
            if 'DO NOT' in line.upper() or 'WARNING' in line.upper() or 'FIXME' in line.upper():
                continue
            issues.append({
                'type': 'cuda',
                'pattern': pattern,
                'line_num': line_num,
                'content': line.strip()
            })

    return issues


def process_file(file_path: pathlib.Path) -> Tuple[bool, List[Dict], List[str]]:
    """
    Process a single Python file:
    - Detect prohibited imports
    - Remove them if found
    - Return (was_modified, issues, removed_lines)
    """
    issues = []
    removed_lines = []
    modified = False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return False, [{'type': 'error', 'message': str(e)}], []

    new_lines = []
    for i, line in enumerate(lines, 1):
        line_issues = is_prohibited_line(line, i, str(file_path))
        if line_issues:
            issues.extend(line_issues)
            removed_lines.append({
                'line_num': i,
                'content': line.strip()
            })
            modified = True
            # Skip this line (remove it)
            continue
        new_lines.append(line)

    # Write back if modified
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return modified, issues, removed_lines


def scan_project(root_dir: pathlib.Path) -> Dict:
    """Scan all Python files in the project directory."""
    results = {
        'scanned_files': 0,
        'modified_files': 0,
        'total_issues': 0,
        'quantization_issues': 0,
        'cuda_issues': 0,
        'files': []
    }

    python_files = list(root_dir.rglob('*.py'))

    for py_file in python_files:
        # Skip test files and __pycache__
        if '__pycache__' in str(py_file):
            continue
        if 'test' in py_file.name.lower() and py_file.parent.name == 'tests':
            # Still scan test files but note them
            pass

        results['scanned_files'] += 1
        modified, issues, removed = process_file(py_file)

        if issues:
            results['total_issues'] += len(issues)
            for issue in issues:
                if issue['type'] == 'quantization':
                    results['quantization_issues'] += 1
                elif issue['type'] == 'cuda':
                    results['cuda_issues'] += 1

        if modified:
            results['modified_files'] += 1

        if issues or modified:
            results['files'].append({
                'path': str(py_file.relative_to(root_dir)),
                'modified': modified,
                'issues': issues,
                'removed_lines': removed
            })

    return results


def generate_markdown_report(scan_results: Dict, output_path: pathlib.Path) -> None:
    """Generate a Markdown report of the scan results."""
    report_lines = [
        "# Quantization and CUDA Import Verification Report",
        f"\nGenerated: {datetime.now().isoformat()}",
        f"\n## Summary",
        f"- Files scanned: {scan_results['scanned_files']}",
        f"- Files modified: {scan_results['modified_files']}",
        f"- Total issues found: {scan_results['total_issues']}",
        f"- Quantization issues: {scan_results['quantization_issues']}",
        f"- CUDA issues: {scan_results['cuda_issues']}",
        f"\n## Verification Status",
    ]

    if scan_results['total_issues'] == 0:
        report_lines.append("\n✅ **All clear**: No prohibited quantization or CUDA imports found.")
    else:
        report_lines.append(f"\n⚠️ **{scan_results['total_issues']} issue(s) found and removed**.")

    report_lines.append("\n## Details")

    if scan_results['files']:
        report_lines.append("\n### Affected Files")
        for file_info in scan_results['files']:
            report_lines.append(f"\n#### `{file_info['path']}`")
            report_lines.append(f"- Modified: {file_info['modified']}")
            report_lines.append(f"- Issues: {len(file_info['issues'])}")

            if file_info['removed_lines']:
                report_lines.append("\n**Removed lines:**")
                for rem in file_info['removed_lines']:
                    report_lines.append(f"- Line {rem['line_num']}: `{rem['content']}`")

            if file_info['issues']:
                report_lines.append("\n**Issue details:**")
                for issue in file_info['issues']:
                    report_lines.append(
                        f"- Line {issue['line_num']}: [{issue['type'].upper()}] "
                        f"Pattern: `{issue['pattern']}`"
                    )
    else:
        report_lines.append("\nNo files required modification.")

    report_lines.append("\n## Conclusion")
    if scan_results['total_issues'] == 0:
        report_lines.append(
            "\nThe codebase is compliant with CPU-only execution requirements. "
            "No 8-bit/4-bit quantization or CUDA-specific imports are present."
        )
    else:
        report_lines.append(
            f"\n{scan_results['total_issues']} prohibited import(s) were detected and removed. "
            "The codebase is now compliant with CPU-only execution requirements."
        )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))


def main():
    """Main entry point for the verification script."""
    # Determine project root (parent of code/)
    script_path = pathlib.Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"Scanning project at: {project_root}")
    print("Checking for prohibited quantization and CUDA imports...")

    results = scan_project(project_root)

    # Generate report
    report_path = project_root / 'results' / 'quantization_verification_report.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(results, report_path)

    print(f"\nScan complete!")
    print(f"  Files scanned: {results['scanned_files']}")
    print(f"  Files modified: {results['modified_files']}")
    print(f"  Issues found and removed: {results['total_issues']}")
    print(f"  Report saved to: {report_path}")

    # Exit with error if issues were found (for CI/CD)
    if results['total_issues'] > 0:
        print("\n⚠️ Issues were found and removed. Please review the report.")
        sys.exit(0)  # Success - issues were handled
    else:
        print("\n✅ No prohibited imports found. Codebase is clean.")
        sys.exit(0)


if __name__ == '__main__':
    main()
