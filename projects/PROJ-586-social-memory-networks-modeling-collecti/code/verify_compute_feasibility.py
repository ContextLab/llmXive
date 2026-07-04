"""Verify compute feasibility: remove quantization, verify no CUDA imports."""
from __future__ import annotations

import pathlib
import re
import sys
from typing import List, Dict, Set, Tuple, Optional


PROHIBITED_PATTERNS = {
    'bitsandbytes': r'\bimport\s+bitsandbytes\b|\bfrom\s+bitsandbytes\b',
    'torch.cuda': r'\btorch\.cuda\b|\bfrom\s+torch\s+import.*cuda\b',
    'load_in_8bit': r'\bload_in_8bit\s*=\s*True\b|\bload_in_8bit\b',
    'load_in_4bit': r'\bload_in_4bit\s*=\s*True\b|\bload_in_4bit\b',
    'bnb_config': r'\bbnb_config\b',
}


def line_is_prohibited(line: str) -> Tuple[bool, Optional[str]]:
    """Check if a line contains prohibited imports/patterns.
    
    Returns (is_prohibited, pattern_name).
    """
    for pattern_name, pattern in PROHIBITED_PATTERNS.items():
        if re.search(pattern, line, re.IGNORECASE):
            return True, pattern_name
    return False, None


def process_file(filepath: pathlib.Path) -> Dict[str, any]:
    """Scan a single Python file for prohibited patterns.
    
    Returns dict with 'path', 'violations', 'line_numbers', 'lines'.
    """
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line_no, line in enumerate(lines, start=1):
            is_prohibited, pattern_name = line_is_prohibited(line)
            if is_prohibited:
                violations.append({
                    'line_number': line_no,
                    'pattern': pattern_name,
                    'line': line.rstrip()
                })
    except Exception as e:
        violations.append({
            'error': str(e),
            'line_number': 0
        })
    
    return {
        'path': str(filepath),
        'violations': violations,
        'is_clean': len(violations) == 0
    }


def scan_project(root: pathlib.Path) -> Dict[str, any]:
    """Scan entire project for prohibited patterns.
    
    Returns summary with file results and statistics.
    """
    python_files = list(root.glob('**/*.py'))
    results = []
    violations_by_pattern: Dict[str, int] = {}
    
    for py_file in sorted(python_files):
        result = process_file(py_file)
        results.append(result)
        
        for v in result['violations']:
            pattern = v.get('pattern', 'error')
            violations_by_pattern[pattern] = violations_by_pattern.get(pattern, 0) + 1
    
    clean_files = sum(1 for r in results if r['is_clean'])
    total_violations = sum(len(r['violations']) for r in results)
    
    return {
        'root': str(root),
        'total_files': len(python_files),
        'clean_files': clean_files,
        'files_with_violations': len(python_files) - clean_files,
        'total_violations': total_violations,
        'violations_by_pattern': violations_by_pattern,
        'file_results': results
    }


def generate_markdown_report(scan_result: Dict[str, any]) -> str:
    """Generate a markdown report of scan results."""
    lines = [
        '# Compute Feasibility Verification Report',
        '',
        '## Summary',
        '',
        f"- **Project Root**: {scan_result['root']}",
        f"- **Total Python Files**: {scan_result['total_files']}",
        f"- **Clean Files**: {scan_result['clean_files']}",
        f"- **Files with Violations**: {scan_result['files_with_violations']}",
        f"- **Total Violations**: {scan_result['total_violations']}",
        '',
    ]
    
    if scan_result['violations_by_pattern']:
        lines.extend([
            '## Violations by Pattern',
            '',
        ])
        for pattern, count in sorted(scan_result['violations_by_pattern'].items()):
            lines.append(f"- **{pattern}**: {count}")
        lines.append('')
    
    if scan_result['files_with_violations'] > 0:
        lines.extend([
            '## Files with Violations',
            '',
        ])
        for result in scan_result['file_results']:
            if not result['is_clean']:
                lines.append(f"### {result['path']}")
                lines.append('')
                for v in result['violations']:
                    if 'error' in v:
                        lines.append(f"- **Error**: {v['error']}")
                    else:
                        lines.append(
                            f"- Line {v['line_number']} "
                            f"({v['pattern']}): `{v['line']}`"
                        )
                lines.append('')
    else:
        lines.extend([
            '## Result',
            '',
            '✅ **PASS**: No prohibited imports or patterns detected.',
            '',
            'The codebase is CPU-only and does not use:',
            '- `bitsandbytes` (8-bit/4-bit quantization)',
            '- `torch.cuda` (CUDA/GPU acceleration)',
            '- `load_in_8bit` or `load_in_4bit` flags',
            '',
        ])
    
    return '\n'.join(lines)


def build_parser():
    """Build argument parser."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Verify compute feasibility: scan for quantization & CUDA imports'
    )
    parser.add_argument(
        '--root',
        type=pathlib.Path,
        default=pathlib.Path('code'),
        help='Root directory to scan (default: code)'
    )
    parser.add_argument(
        '--output',
        type=pathlib.Path,
        default=None,
        help='Output file for markdown report (default: print to stdout)'
    )
    return parser


def main():
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    root = args.root
    if not root.exists():
        print(f"Error: root directory {root} does not exist", file=sys.stderr)
        return 1
    
    scan_result = scan_project(root)
    report = generate_markdown_report(scan_result)
    
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)
    
    # Exit with error code if violations found
    if scan_result['total_violations'] > 0:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
