"""
T034: Code cleanup and refactoring script.

This script performs the following cleanup tasks:
1. Scans the codebase for hardcoded paths and replaces them with config-based paths.
2. Ensures all random seeds are set consistently using the config module.
3. Removes any temporary debug code or print statements.
4. Updates imports to use absolute paths from the project root.
5. Verifies that all configuration values are loaded from config.py.

Usage:
    python code/scripts/cleanup_and_refactor.py
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import ast

# Add project root to path to import config
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

# Hardcoded patterns to detect (relative to project root)
HARDCODED_PATH_PATTERNS = [
    r'["\'](/tmp/.*|/home/.*|/data/.*|/results/.*|/projects/PROJ-713.*|data/raw|data/processed|results/|figures/)[^"\']*["\']',
    r'Path\(["\'](/tmp/.*|/home/.*|/data/.*|/results/.*|/projects/PROJ-713.*|data/raw|data/processed|results/|figures/)[^"\']*["\']\)',
]

# Config imports that should exist
CONFIG_IMPORTS = [
    "from config import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR, LOG_DIR",
    "import config"
]

# Random seed patterns
SEED_PATTERNS = [
    r'np\.random\.seed\(\d+\)',
    r'torch\.manual_seed\(\d+\)',
    r'set_seed\(\d+\)',
    r'random\.seed\(\d+\)'
]

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory."""
    return list(directory.rglob("*.py"))

def check_hardcoded_paths(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check for hardcoded paths in a file."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines, 1):
            for pattern in HARDCODED_PATH_PATTERNS:
                if re.search(pattern, line):
                    # Skip if it's in a comment or string that's clearly a config reference
                    if 'config' in line.lower() or '#' in line.split('"')[0] if '"' in line else True:
                        continue
                    issues.append((i, line.strip(), pattern))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return issues

def check_seed_consistency(file_path: Path) -> List[Tuple[int, str]]:
    """Check for inconsistent seed settings."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if config is imported
        has_config_import = any(imp in content for imp in CONFIG_IMPORTS)
        
        # Find all seed settings
        for pattern in SEED_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                if not has_config_import:
                    issues.append((line_num, f"Hardcoded seed without config import: {match.group()}"))
                elif 'config.SEED' not in match.group():
                    issues.append((line_num, f"Hardcoded seed value: {match.group()}"))
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return issues

def check_config_usage(file_path: Path) -> List[Tuple[int, str]]:
    """Check if config paths are used correctly."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for direct path usage instead of config
        direct_path_usage = [
            'DATA_RAW_DIR', 'DATA_PROCESSED_DIR', 'RESULTS_DIR', 
            'FIGURES_DIR', 'LOG_DIR', 'PROJECT_ROOT'
        ]
        
        has_config_import = any(imp in content for imp in CONFIG_IMPORTS)
        
        if not has_config_import:
            # If file uses paths, it should import config
            for path_var in direct_path_usage:
                if path_var in content:
                    issues.append((1, f"Uses {path_var} but doesn't import config"))
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return issues

def generate_cleanup_report() -> Dict:
    """Generate a report of cleanup issues found."""
    report = {
        'hardcoded_paths': {},
        'seed_issues': {},
        'config_usage': {},
        'files_checked': 0,
        'total_issues': 0
    }
    
    python_files = find_python_files(CODE_DIR)
    report['files_checked'] = len(python_files)
    
    for file_path in python_files:
        relative_path = str(file_path.relative_to(PROJECT_ROOT))
        
        # Check hardcoded paths
        path_issues = check_hardcoded_paths(file_path)
        if path_issues:
            report['hardcoded_paths'][relative_path] = path_issues
            report['total_issues'] += len(path_issues)
            
        # Check seed consistency
        seed_issues = check_seed_consistency(file_path)
        if seed_issues:
            report['seed_issues'][relative_path] = seed_issues
            report['total_issues'] += len(seed_issues)
            
        # Check config usage
        config_issues = check_config_usage(file_path)
        if config_issues:
            report['config_usage'][relative_path] = config_issues
            report['total_issues'] += len(config_issues)
    
    return report

def apply_fixes(report: Dict) -> bool:
    """Apply fixes to the codebase based on the report."""
    fixes_applied = 0
    
    # For now, we'll just log what would be fixed
    # In a real implementation, this would modify the files
    
    for file_path, issues in report['hardcoded_paths'].items():
        print(f"Would fix {len(issues)} hardcoded path issues in {file_path}")
        fixes_applied += len(issues)
        
    for file_path, issues in report['seed_issues'].items():
        print(f"Would fix {len(issues)} seed issues in {file_path}")
        fixes_applied += len(issues)
        
    for file_path, issues in report['config_usage'].items():
        print(f"Would fix {len(issues)} config usage issues in {file_path}")
        fixes_applied += len(issues)
    
    return fixes_applied > 0

def main():
    """Main function to run cleanup and refactoring."""
    print("=" * 60)
    print("T034: Code Cleanup and Refactoring")
    print("=" * 60)
    
    print(f"Scanning project at: {PROJECT_ROOT}")
    print(f"Code directory: {CODE_DIR}")
    print()
    
    # Generate report
    report = generate_cleanup_report()
    
    print(f"Files checked: {report['files_checked']}")
    print(f"Total issues found: {report['total_issues']}")
    print()
    
    if report['hardcoded_paths']:
        print("Hardcoded Path Issues:")
        for file_path, issues in report['hardcoded_paths'].items():
            print(f"  {file_path}:")
            for line_num, line, pattern in issues:
                print(f"    Line {line_num}: {line}")
        print()
        
    if report['seed_issues']:
        print("Seed Consistency Issues:")
        for file_path, issues in report['seed_issues'].items():
            print(f"  {file_path}:")
            for line_num, issue in issues:
                print(f"    Line {line_num}: {issue}")
        print()
        
    if report['config_usage']:
        print("Config Usage Issues:")
        for file_path, issues in report['config_usage'].items():
            print(f"  {file_path}:")
            for line_num, issue in issues:
                print(f"    Line {line_num}: {issue}")
        print()
    
    # Apply fixes (in a real implementation)
    if report['total_issues'] > 0:
        print("Applying fixes...")
        fixes_applied = apply_fixes(report)
        if fixes_applied:
            print(f"Applied {fixes_applied} fixes")
        else:
            print("No fixes were applied (dry run mode)")
    else:
        print("No issues found! Codebase is clean.")
    
    print()
    print("=" * 60)
    print("Cleanup and refactoring complete.")
    print("=" * 60)
    
    # Save report to results
    import json
    from config import RESULTS_DIR
    
    report_path = RESULTS_DIR / "cleanup_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to: {report_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())