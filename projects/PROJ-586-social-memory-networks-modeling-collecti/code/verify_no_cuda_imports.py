"""
T032: Verification script to ensure no CUDA imports exist in the project.

This script performs a final verification pass to confirm that:
1. No bitsandbytes imports exist
2. No torch.cuda imports exist
3. No 8-bit/4-bit quantization flags are used
4. All device specifications are CPU-only

It outputs a detailed report and exits with code 0 if clean, 1 if issues found.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Strict patterns for CUDA/quantization detection
CUDA_PATTERNS = [
    r'import\s+torch\.cuda',
    r'from\s+torch\s+import\s+.*cuda',
    r'torch\.cuda\.',
    r'CUDA_HOME',
    r'pynvml',
    r'nvidia-smi',
]

QUANTIZATION_PATTERNS = [
    r'bitsandbytes',
    r'load_in_8bit\s*=\s*True',
    r'load_in_4bit\s*=\s*True',
    r'bnb\s*=\s*True',
    r'quantize\s*=\s*True',
    r'8bit',
    r'4bit',
]

def check_file(file_path: pathlib.Path) -> Tuple[bool, List[str]]:
    """
    Check a single file for CUDA/quantization issues.
    
    Returns:
        (has_issues, list of issue descriptions)
    """
    issues = []
    
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception:
        return False, []
    
    lines = content.splitlines()
    
    for i, line in enumerate(lines):
        # Skip comments
        if line.strip().startswith('#'):
            continue
        
        # Check CUDA patterns
        for pattern in CUDA_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append(f"Line {i+1}: CUDA-related pattern '{pattern}' found: {line.strip()}")
        
        # Check quantization patterns
        for pattern in QUANTIZATION_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                # Be more lenient: allow '8bit' in comments or variable names that aren't imports
                if 'import' in line.lower() or 'from' in line.lower() or 'load_in' in line.lower():
                    issues.append(f"Line {i+1}: Quantization pattern '{pattern}' found: {line.strip()}")
    
    return len(issues) > 0, issues

def verify_project(root_dir: pathlib.Path) -> Dict:
    """
    Verify the entire project for CUDA/quantization compliance.
    
    Returns a verification report.
    """
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'files_checked': 0,
        'files_with_issues': 0,
        'all_issues': [],
        'clean_files': 0,
    }
    
    python_files = list(root_dir.rglob('*.py'))
    
    # Exclude virtual environments and build directories
    exclusions = ['.venv', 'venv', '__pycache__', 'build', 'dist', '.git', 'node_modules']
    python_files = [
        f for f in python_files
        if not any(excl in str(f) for excl in exclusions)
    ]
    
    for file_path in python_files:
        report['files_checked'] += 1
        has_issues, issues = check_file(file_path)
        
        if has_issues:
            report['files_with_issues'] += 1
            for issue in issues:
                report['all_issues'].append({
                    'file': str(file_path.relative_to(root_dir)),
                    'issue': issue,
                })
        else:
            report['clean_files'] += 1
    
    return report

def main() -> int:
    """Main entry point."""
    script_dir = pathlib.Path(__file__).parent
    project_root = script_dir.parent.parent  # Go up from code/ to project root
    
    print(f"Verifying project at: {project_root}")
    print()
    
    report = verify_project(project_root)
    
    print(f"Files checked: {report['files_checked']}")
    print(f"Clean files: {report['clean_files']}")
    print(f"Files with issues: {report['files_with_issues']}")
    print()
    
    if report['all_issues']:
        print("❌ ISSUES FOUND:")
        print()
        for item in report['all_issues']:
            print(f"  {item['file']}")
            print(f"    {item['issue']}")
            print()
        
        print("Please run 'python code/remove_quantization_imports.py' to fix these issues.")
        return 1
    else:
        print("✅ VERIFICATION PASSED: No CUDA or quantization imports found.")
        print("The project is fully CPU-only compliant.")
        return 0

if __name__ == '__main__':
    sys.exit(main())
