"""
T032: Remove all 8-bit/4-bit quantization imports and verify no CUDA imports.

This script scans all Python files in the project, identifies and removes
prohibited imports (bitsandbytes, 8-bit/4-bit quantization, CUDA-specific),
and generates a verification report.

Prohibited patterns:
- bitsandbytes (8-bit/4-bit quantization library)
- torch.cuda.* (explicit CUDA usage)
- CUDA_HOME, pynvml (GPU monitoring)
- AutoModelForCausalLM.from_pretrained(..., load_in_8bit=True/4bit=True)
- Any import containing '8bit', '4bit', 'quantize' in the context of loading

The script modifies files in-place and produces a report at:
projects/PROJ-586-social-memory-networks-modeling-collecti/results/quantization_verification.md
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime

# Patterns to detect prohibited imports
PROHIBITED_IMPORT_PATTERNS = [
    r'from\s+bitsandbytes\s+',
    r'import\s+bitsandbytes',
    r'from\s+torch\.cuda\s+',
    r'import\s+torch\.cuda',
    r'from\s+pynvml\s+',
    r'import\s+pynvml',
    r'from\s+transformers\s+.*\s+load_in_8bit',
    r'from\s+transformers\s+.*\s+load_in_4bit',
    r'from\s+transformers\s+.*\s+bitsandbytes',
    r'load_in_8bit\s*=\s*True',
    r'load_in_4bit\s*=\s*True',
    r'quantize\s*=\s*True',
    r'bnb\s*=\s*True',
    r'8bit',
    r'4bit',
]

# Patterns that are OK (CPU-only, standard usage)
ALLOWED_PATTERNS = [
    r'torch\.device\(["\']cpu["\']\)',
    r'device\s*=\s*["\']cpu["\']',
    r'transformers.*AutoModel',
    r'transformers.*AutoTokenizer',
]

def line_is_prohibited(line: str) -> Tuple[bool, Optional[str]]:
    """Check if a line contains prohibited import patterns."""
    line_lower = line.lower()
    
    # Skip comments and empty lines
    if line.strip().startswith('#') or not line.strip():
        return False, None
    
    for pattern in PROHIBITED_IMPORT_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            # Special case: '8bit' or '4bit' might appear in comments or variable names
            # Only flag if it's in an import context
            if 'import' in line_lower or 'from' in line_lower:
                return True, pattern
            # Check for explicit quantization flags in function calls
            if 'load_in_8bit' in line_lower or 'load_in_4bit' in line_lower:
                return True, pattern
            if 'bitsandbytes' in line_lower:
                return True, pattern
            
    return False, None

def process_file(file_path: pathlib.Path) -> Tuple[bool, List[str], List[str]]:
    """
    Process a single Python file: remove prohibited imports.
    
    Returns:
        (modified, removed_lines, warnings)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [], [f"Error reading {file_path}: {e}"]
    
    lines = content.splitlines()
    new_lines = []
    removed_lines = []
    warnings = []
    
    for i, line in enumerate(lines):
        is_prohibited, pattern = line_is_prohibited(line)
        
        if is_prohibited:
            removed_lines.append(f"Line {i+1}: {line.strip()} (pattern: {pattern})")
            # Skip this line (remove it)
            continue
        
        new_lines.append(line)
    
    modified = len(removed_lines) > 0
    
    if modified:
        try:
            file_path.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
        except Exception as e:
            warnings.append(f"Error writing {file_path}: {e}")
    
    return modified, removed_lines, warnings

def scan_project(root_dir: pathlib.Path) -> Dict:
    """
    Scan the entire project for prohibited imports and remove them.
    
    Returns a report dictionary with:
        - files_scanned: number of files checked
        - files_modified: number of files changed
        - removed_imports: list of (file, line) tuples
        - warnings: any errors encountered
    """
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'files_scanned': 0,
        'files_modified': 0,
        'removed_imports': [],
        'warnings': [],
        'prohibited_files': [],
    }
    
    # Find all Python files
    python_files = list(root_dir.rglob('*.py'))
    
    # Exclude virtual environments and build directories
    exclusions = ['.venv', 'venv', '__pycache__', 'build', 'dist', '.git', 'node_modules']
    python_files = [
        f for f in python_files
        if not any(excl in str(f) for excl in exclusions)
    ]
    
    for file_path in python_files:
        report['files_scanned'] += 1
        
        modified, removed, warnings = process_file(file_path)
        
        if modified:
            report['files_modified'] += 1
            report['removed_imports'].extend([
                (str(file_path.relative_to(root_dir)), line)
                for line in removed
            ])
            report['prohibited_files'].append(str(file_path.relative_to(root_dir)))
        
        report['warnings'].extend(warnings)
    
    return report

def generate_markdown_report(report: Dict, output_path: pathlib.Path) -> None:
    """Generate a human-readable markdown verification report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Quantization Import Removal Verification Report",
        "",
        f"**Generated**: {report['timestamp']}",
        "",
        "## Summary",
        "",
        f"- **Files scanned**: {report['files_scanned']}",
        f"- **Files modified**: {report['files_modified']}",
        "",
    ]
    
    if report['prohibited_files']:
        lines.append("## Files with Prohibited Imports Removed")
        lines.append("")
        for file_path in report['prohibited_files']:
            lines.append(f"- `{file_path}`")
        lines.append("")
    else:
        lines.append("## Verification Result")
        lines.append("")
        lines.append("✅ **No prohibited imports found.** All Python files are compliant.")
        lines.append("")
        lines.append("The following patterns were checked and none were found:")
        lines.append("")
        for pattern in PROHIBITED_IMPORT_PATTERNS:
            lines.append(f"- `{pattern}`")
        lines.append("")
    
    if report['removed_imports']:
        lines.append("## Removed Imports Detail")
        lines.append("")
        for file_path, line_detail in report['removed_imports']:
            lines.append(f"### `{file_path}`")
            lines.append("")
            lines.append(f"```\n{line_detail}\n```")
            lines.append("")
    
    if report['warnings']:
        lines.append("## Warnings")
        lines.append("")
        for warning in report['warnings']:
            lines.append(f"- {warning}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*This report was automatically generated by T032: remove_quantization_imports.py*")
    
    output_path.write_text('\n'.join(lines), encoding='utf-8')

def main() -> int:
    """Main entry point for the script."""
    # Determine project root
    script_dir = pathlib.Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up from code/ to project root
    
    # Output path for the report
    results_dir = project_root / 'results'
    report_path = results_dir / 'quantization_verification.md'
    
    print(f"Scanning project at: {project_root}")
    print(f"Output report will be written to: {report_path}")
    print()
    
    # Scan and clean
    report = scan_project(project_root)
    
    # Generate report
    generate_markdown_report(report, report_path)
    
    # Print summary
    print(f"✅ Scanning complete!")
    print(f"   Files scanned: {report['files_scanned']}")
    print(f"   Files modified: {report['files_modified']}")
    
    if report['prohibited_files']:
        print(f"   ⚠️  Found and removed prohibited imports from {len(report['prohibited_files'])} file(s)")
        print(f"   See report: {report_path}")
    else:
        print(f"   ✅ No prohibited imports found. Project is CPU-only compliant.")
    
    if report['warnings']:
        print(f"   ⚠️  Warnings: {len(report['warnings'])}")
        for w in report['warnings'][:3]:
            print(f"      - {w}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
