import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import ast
import json
import logging

from config import PROJECT_ROOT, RESULTS_DIR, DATA_DIR, CODE_DIR
from utils.logger import get_logger
from utils.exceptions import ConfigurationError

logger = get_logger(__name__)

# Patterns for hardcoded paths
HARDCODED_PATH_PATTERNS = [
    r'["\'](/tmp/|/var/tmp/|/home/\w+/|/Users/\w+/|C:\\Users\\|C:\\Program)',
    r'["\'](/absolute/path|/some/fixed/dir)',
    r'os\.path\.join\(\s*["\'][^"\']+["\']\s*,\s*["\'][^"\']+["\']\s*\)',
]

# Patterns for seed usage
SEED_PATTERNS = [
    r'np\.random\.seed\(\s*\d+\s*\)',
    r'random\.seed\(\s*\d+\s*\)',
    r'torch\.manual_seed\(\s*\d+\s*\)',
    r'random_state\s*=\s*\d+',
]

# Config variable patterns
CONFIG_USAGE = [
    r'from\s+config\s+import',
    r'config\.\w+',
    r'CONFIG\.\w+',
]

def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the given directory recursively."""
    py_files = []
    for root, _, files in os.walk(root_dir):
        # Skip hidden directories and __pycache__
        dirs_to_skip = {'.git', '__pycache__', '.pytest_cache', 'node_modules', 'venv', 'env'}
        root_path = Path(root)
        if any(dir_name in root_path.parts for dir_name in dirs_to_skip):
            continue
        
        for file in files:
            if file.endswith('.py'):
                py_files.append(Path(root) / file)
    return py_files

def check_hardcoded_paths(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check for hardcoded paths in a Python file."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            for pattern in HARDCODED_PATH_PATTERNS:
                if re.search(pattern, line):
                    issues.append((i, pattern, line.strip()))
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    
    return issues

def check_seed_consistency(file_path: Path) -> List[Tuple[int, str, str]]:
    """Check for hardcoded seed values that should use config."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Look for hardcoded numeric seeds
            if re.search(r'(\d{2,})', line) and any(p in line for p in ['seed', 'random_state']):
                # Skip if it's clearly a comment or string literal not related to seeding
                if 'seed' in line.lower() and not line.strip().startswith('#'):
                    issues.append((i, 'hardcoded_seed', line.strip()))
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    
    return issues

def check_config_usage(file_path: Path) -> Dict[str, bool]:
    """Check if a file properly imports and uses config."""
    result = {
        'imports_config': False,
        'uses_config_vars': False,
        'has_hardcoded_paths': False
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check imports
        if re.search(r'from\s+config\s+import', content):
            result['imports_config'] = True
        
        # Check usage
        if re.search(r'(CONFIG|config|PROJECT_ROOT|DATA_DIR|RESULTS_DIR)\.\w+', content):
            result['uses_config_vars'] = True
        
        # Check for hardcoded paths
        if any(re.search(p, content) for p in HARDCODED_PATH_PATTERNS):
            result['has_hardcoded_paths'] = True
            
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    
    return result

def generate_cleanup_report(issues: Dict[str, List[Tuple[Path, List[Tuple[int, str, str]]]]]) -> str:
    """Generate a detailed cleanup report."""
    report_lines = []
    report_lines.append("# Code Cleanup and Refactoring Report")
    report_lines.append(f"Generated at: {Path.cwd()}")
    report_lines.append("")
    
    if not any(issues.values()):
        report_lines.append("✅ No issues found. Codebase is clean!")
        return "\n".join(report_lines)
    
    if issues['hardcoded_paths']:
        report_lines.append("## ⚠️ Hardcoded Paths Found")
        for file_path, file_issues in issues['hardcoded_paths']:
            report_lines.append(f"\n### {file_path}")
            for line_num, pattern, line_content in file_issues:
                report_lines.append(f"  Line {line_num}: {line_content}")
                report_lines.append(f"    Pattern: {pattern}")
        
    if issues['seed_consistency']:
        report_lines.append("\n## ⚠️ Seed Consistency Issues")
        for file_path, file_issues in issues['seed_consistency']:
            report_lines.append(f"\n### {file_path}")
            for line_num, issue_type, line_content in file_issues:
                report_lines.append(f"  Line {line_num}: {line_content}")
    
    report_lines.append("\n## Recommendations")
    report_lines.append("1. Replace hardcoded paths with `config.PROJECT_ROOT`, `config.DATA_DIR`, etc.")
    report_lines.append("2. Use `config.SEED` for all random seed initializations.")
    report_lines.append("3. Ensure all data paths are relative to the project root.")
    
    return "\n".join(report_lines)

def apply_fixes(file_path: Path, fixes: Dict[str, List[Tuple[int, str]]]) -> bool:
    """Apply automatic fixes to a file."""
    if not fixes:
        return True
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort fixes by line number in reverse order to avoid index shifting
        all_fixes = []
        for fix_type, fix_list in fixes.items():
            all_fixes.extend(fix_list)
        
        all_fixes.sort(key=lambda x: x[0], reverse=True)
        
        for line_num, fix_desc in all_fixes:
            if line_num <= len(lines):
                # Mark for review - we don't auto-fix complex logic
                logger.info(f"Flagged line {line_num} in {file_path} for manual review: {fix_desc}")
        
        # For now, we only log issues rather than auto-modifying code
        # This is safer than potentially breaking logic
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply fixes to {file_path}: {e}")
        return False

def main():
    """Main entry point for the cleanup and refactor script."""
    logger.info("Starting code cleanup and refactoring analysis...")
    
    # Find all Python files
    py_files = find_python_files(str(CODE_DIR))
    logger.info(f"Found {len(py_files)} Python files to analyze.")
    
    # Initialize issue tracking
    issues = {
        'hardcoded_paths': [],
        'seed_consistency': [],
        'config_usage': []
    }
    
    # Analyze each file
    for file_path in py_files:
        # Check hardcoded paths
        path_issues = check_hardcoded_paths(file_path)
        if path_issues:
            issues['hardcoded_paths'].append((file_path, path_issues))
        
        # Check seed consistency
        seed_issues = check_seed_consistency(file_path)
        if seed_issues:
            issues['seed_consistency'].append((file_path, seed_issues))
        
        # Check config usage
        config_status = check_config_usage(file_path)
        if config_status['has_hardcoded_paths']:
            logger.warning(f"File {file_path} has hardcoded paths despite config usage check")
    
    # Generate report
    report = generate_cleanup_report(issues)
    
    # Save report
    report_path = RESULTS_DIR / "cleanup_refactor_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Cleanup report saved to {report_path}")
    
    # Summary
    total_issues = sum(len(v) for v in issues.values())
    if total_issues > 0:
        logger.warning(f"Found {total_issues} issues that need attention.")
        return 1
    else:
        logger.info("✅ All checks passed! Codebase is clean.")
        return 0

if __name__ == "__main__":
    sys.exit(main())