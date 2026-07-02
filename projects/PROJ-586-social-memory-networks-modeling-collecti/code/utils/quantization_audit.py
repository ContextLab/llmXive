"""
Quantization and CUDA Audit Tool for Social Memory Networks Project.

This script scans all Python files in the project to ensure:
1. No 8-bit or 4-bit quantization imports are present (e.g., bitsandbytes, peft with quantization)
2. No CUDA imports or usage are present (only CPU execution allowed)
3. All imports are compatible with the CPU-only CI environment (2 CPU, ~7GB RAM)

Usage:
    python code/utils/quantization_audit.py [--strict]

Exit codes:
    0 - Audit passed, all files are compatible
    1 - Audit failed, incompatible imports found
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

# Forbidden patterns for quantization
QUANTIZATION_FORBIDDEN_PATTERNS = [
    r'import\s+bitsandbytes',
    r'from\s+bitsandbytes',
    r'import\s+peft.*quantization',
    r'from\s+peft.*quantization',
    r'import\s+llama\.quantization',
    r'from\s+llama\.quantization',
    r'import\s+transformers.*quantization',
    r'from\s+transformers.*quantization',
    r'load_in_8bit\s*=',
    r'load_in_4bit\s*=',
    r'bnb_8bit',
    r'bnb_4bit',
    r'compute_dtype\s*=\s*torch\.float16',
    r'compute_dtype\s*=\s*torch\.bfloat16',
    r'quantization_config',
    r'BitsAndBytesConfig',
]

# Forbidden patterns for CUDA
CUDA_FORBIDDEN_PATTERNS = [
    r'import\s+torch\.cuda',
    r'from\s+torch\.cuda',
    r'torch\.cuda\.is_available',
    r'torch\.cuda\.device',
    r'torch\.cuda\.get_device_count',
    r'torch\.cuda\.current_device',
    r'device\s*=\s*["\']cuda["\']',
    r'device\s*=\s*torch\.cuda\.device',
    r'\.to\(["\']cuda["\']',
    r'\.cuda\(\)',
    r'torch\.set_default_tensor_type\(.*cuda',
]

# Allowed CPU-only patterns
CPU_ALLOWED_PATTERNS = [
    r'device\s*=\s*["\']cpu["\']',
    r'device\s*=\s*tensor\.device',
    r'\.to\(["\']cpu["\']',
    r'torch\.cpu',
]

def scan_file(file_path: Path, project_root: Path) -> Tuple[List[str], List[str]]:
    """
    Scan a single Python file for forbidden imports and patterns.

    Args:
        file_path: Path to the Python file to scan
        project_root: Root of the project for relative path calculation

    Returns:
        Tuple of (quantization_issues, cuda_issues)
    """
    quantization_issues = []
    cuda_issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [f"Error reading file: {e}"], []

    rel_path = file_path.relative_to(project_root)

    # Check for quantization patterns
    for i, line in enumerate(lines, 1):
        for pattern in QUANTIZATION_FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                quantization_issues.append(
                    f"{rel_path}:{i}: Found forbidden quantization pattern: {line.strip()}"
                )

    # Check for CUDA patterns
    for i, line in enumerate(lines, 1):
        for pattern in CUDA_FORBIDDEN_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                cuda_issues.append(
                    f"{rel_path}:{i}: Found forbidden CUDA pattern: {line.strip()}"
                )

    return quantization_issues, cuda_issues

def find_python_files(root: Path) -> List[Path]:
    """
    Find all Python files in the project directory.

    Args:
        root: Root directory to search

    Returns:
        List of Path objects for all Python files
    """
    python_files = []
    for ext in ['*.py']:
        python_files.extend(root.rglob(ext))

    # Exclude test files from the scan (they may have different requirements)
    # Actually, we should scan them too to ensure consistency
    return sorted(python_files)

def run_audit(project_root: Path, strict: bool = False) -> int:
    """
    Run the complete quantization and CUDA audit.

    Args:
        project_root: Root of the project
        strict: If True, fail on any warning; otherwise, only fail on errors

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print(f"Scanning project at: {project_root}")
    print("=" * 80)

    python_files = find_python_files(project_root)
    print(f"Found {len(python_files)} Python files to scan")
    print("=" * 80)

    all_quantization_issues = []
    all_cuda_issues = []

    for file_path in python_files:
        quant_issues, cuda_issues = scan_file(file_path, project_root)
        all_quantization_issues.extend(quant_issues)
        all_cuda_issues.extend(cuda_issues)

    # Report results
    has_quantization_issues = len(all_quantization_issues) > 0
    has_cuda_issues = len(all_cuda_issues) > 0

    if has_quantization_issues:
        print("\n❌ QUANTIZATION ISSUES FOUND:")
        print("-" * 40)
        for issue in all_quantization_issues:
            print(f"  {issue}")
        print()

    if has_cuda_issues:
        print("\n❌ CUDA ISSUES FOUND:")
        print("-" * 40)
        for issue in all_cuda_issues:
            print(f"  {issue}")
        print()

    if not has_quantization_issues and not has_cuda_issues:
        print("\n✅ AUDIT PASSED: No forbidden quantization or CUDA imports found.")
        print("All files are compatible with CPU-only execution.")
        return 0
    else:
        print("\n❌ AUDIT FAILED: Found incompatible imports.")
        print("Please remove the forbidden patterns listed above.")
        return 1

def main():
    """Main entry point for the audit script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Audit project for forbidden quantization and CUDA imports'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail on any warning, not just errors'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help='Path to project root (default: parent of this script)'
    )

    args = parser.parse_args()

    # Ensure project root is absolute
    project_root = args.project_root.resolve()

    if not project_root.exists():
        print(f"Error: Project root does not exist: {project_root}")
        sys.exit(1)

    exit_code = run_audit(project_root, args.strict)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
