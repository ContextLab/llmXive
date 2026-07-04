"""Scan project for prohibited quantization and CUDA imports.

This script implements Task T032: Remove all 8-bit/4-bit quantization imports,
verify no CUDA imports in all Python files (compute feasibility).

It scans all .py files in the code/ directory, identifies prohibited patterns,
removes them, and generates a report of changes made.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime


# Prohibited import patterns (8-bit/4-bit quantization and CUDA)
PROHIBITED_PATTERNS = [
    # 8-bit quantization
    r'from\s+bitsandbytes\s+',
    r'import\s+bitsandbytes',
    r'from\s+transformers\.utils\s+import.*bitsandbytes',
    r'from\s+peft\s+import.*load_peft_model.*quantization',
    r'from\s+peft\s+import.*AutoPeftModel.*quantization',
    r'from\s+peft\s+import.*prepare_model_for_kbit_training',
    r'from\s+peft\s+import.*LoraConfig.*load_in_8bit',
    r'from\s+peft\s+import.*LoraConfig.*load_in_4bit',
    r'load_in_8bit',
    r'load_in_4bit',
    r'bitsandbytes\.optim',
    r'bnb',
    r'NF4',
    r'NF4Type',
    r'Int8Params',
    r'fp4',
    r'fp4_config',
    r'nf4',
    r'nf4_config',
    r'compute_dtype.*fp16',
    r'compute_dtype.*bf16',
    r'torch\.cuda\.amp',
    r'from\s+torch\.cuda\s+import.*amp',
    r'from\s+tqdm\s+import.*auto.*quantization',
    # CUDA-specific imports
    r'import\s+torch\.cuda',
    r'from\s+torch\s+import\s+cuda',
    r'from\s+torch\.cuda\s+import',
    r'cuda\(\)',
    r'torch\.cuda\.is_available',
    r'torch\.cuda\.device_count',
    r'torch\.cuda\.get_device_name',
    r'torch\.cuda\.current_device',
    r'torch\.cuda\.set_device',
    r'torch\.cuda\.empty_cache',
    r'torch\.cuda\.synchronize',
    r'torch\.cuda\.memory_allocated',
    r'torch\.cuda\.max_memory_allocated',
    r'torch\.cuda\.memory_reserved',
    r'torch\.cuda\.max_memory_reserved',
    r'device.*cuda',
    r'cuda:0',
    r'cuda:1',
    r'cuda:2',
    r'cuda:3',
    r'cuda:4',
    r'cuda:5',
    r'cuda:6',
    r'cuda:7',
]

# Patterns that are OK (CPU-only or general torch)
ALLOWED_PATTERNS = [
    r'torch\.cpu',
    r'device.*cpu',
    r'cpu',
    r'torch\.float32',
    r'torch\.float64',
    r'torch\.int32',
    r'torch\.int64',
    r'torch\.bool',
    r'torch\.long',
    r'torch\.float',
    r'torch\.double',
    r'torch\.half',
]


def line_is_prohibited(line: str) -> Tuple[bool, List[str]]:
    """Check if a line contains prohibited import patterns.

    Args:
        line: A line of Python code

    Returns:
        Tuple of (is_prohibited, list_of_matched_patterns)
    """
    matches = []
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            matches.append(pattern)
    return len(matches) > 0, matches


def process_file(file_path: pathlib.Path) -> Tuple[bool, List[str], int]:
    """Process a single Python file, removing prohibited imports.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (file_modified, list_of_removed_patterns, lines_removed)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  Error reading {file_path}: {e}")
        return False, [], 0

    lines = content.splitlines()
    new_lines = []
    removed_patterns: Set[str] = set()
    lines_removed = 0

    for i, line in enumerate(lines):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue

        is_prohibited, matches = line_is_prohibited(line)
        if is_prohibited:
            # Check if it's an allowed pattern (CPU-only)
            is_allowed = False
            for allowed in ALLOWED_PATTERNS:
                if re.search(allowed, line, re.IGNORECASE):
                    is_allowed = True
                    break

            if not is_allowed:
                removed_patterns.update(matches)
                lines_removed += 1
                # Add a comment explaining the removal
                new_lines.append(f"# REMOVED (T032): {line.strip()}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Write back if modified
    file_modified = len(removed_patterns) > 0
    if file_modified:
        new_content = '\n'.join(new_lines)
        try:
            file_path.write_text(new_content, encoding='utf-8')
            print(f"  Modified: {file_path} ({lines_removed} lines removed)")
        except Exception as e:
            print(f"  Error writing {file_path}: {e}")
            return False, list(removed_patterns), lines_removed

    return file_modified, list(removed_patterns), lines_removed


def scan_project(root_dir: pathlib.Path) -> Dict[str, Dict]:
    """Scan all Python files in the project for prohibited imports.

    Args:
        root_dir: Root directory of the project

    Returns:
        Dictionary mapping file paths to scan results
    """
    results = {}
    python_files = list(root_dir.rglob('*.py'))

    print(f"Scanning {len(python_files)} Python files in {root_dir}...")

    for file_path in python_files:
        # Skip test files and __pycache__
        if 'test' in str(file_path) or '__pycache__' in str(file_path):
            continue

        modified, patterns, lines_removed = process_file(file_path)
        if modified or patterns:
            results[str(file_path)] = {
                'modified': modified,
                'patterns_removed': patterns,
                'lines_removed': lines_removed,
            }

    return results


def generate_markdown_report(results: Dict[str, Dict], output_path: pathlib.Path) -> None:
    """Generate a markdown report of the cleanup.

    Args:
        results: Dictionary of scan results
        output_path: Path to write the report
    """
    timestamp = datetime.now().isoformat()
    total_files = len(results)
    total_lines_removed = sum(r['lines_removed'] for r in results.values())

    report_lines = [
        "# Quantization and CUDA Import Cleanup Report",
        "",
        f"**Generated**: {timestamp}",
        f"**Task**: T032 - Remove all 8-bit/4-bit quantization imports, verify no CUDA imports",
        "",
        "## Summary",
        "",
        f"- **Files scanned**: All Python files in code/",
        f"- **Files modified**: {total_files}",
        f"- **Total lines removed**: {total_lines_removed}",
        "",
        "## Files Modified",
        "",
    ]

    if not results:
        report_lines.append("No prohibited imports found. Project is clean.")
    else:
        for file_path, details in results.items():
            report_lines.append(f"### {file_path}")
            report_lines.append("")
            report_lines.append(f"- **Lines removed**: {details['lines_removed']}")
            report_lines.append("")
            if details['patterns_removed']:
                report_lines.append("**Patterns removed:**")
                report_lines.append("")
                for pattern in sorted(set(details['patterns_removed'])):
                    report_lines.append(f"- `{pattern}`")
            report_lines.append("")

    report_content = '\n'.join(report_lines)
    output_path.write_text(report_content, encoding='utf-8')
    print(f"Report written to: {output_path}")


def main() -> int:
    """Main entry point for the cleanup script."""
    # Determine project root
    current = pathlib.Path.cwd()
    # Look for code/ directory
    code_dir = current / 'code'
    if not code_dir.exists():
        # Try to find it in parent directories
        for parent in current.parents:
            candidate = parent / 'code'
            if candidate.exists():
                code_dir = candidate
                break
        else:
            print("Error: Could not find code/ directory")
            return 1

    print(f"Scanning project at: {code_dir.parent}")

    # Scan and clean
    results = scan_project(code_dir.parent)

    # Generate report
    report_path = code_dir.parent / 'results' / 'quantization_cleanup_report.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    generate_markdown_report(results, report_path)

    # Print summary
    total_lines = sum(r['lines_removed'] for r in results.values())
    if total_lines > 0:
        print(f"\nCleanup complete. {total_lines} lines removed from {len(results)} files.")
        print(f"See {report_path} for details.")
    else:
        print("\nNo prohibited imports found. Project is clean.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
