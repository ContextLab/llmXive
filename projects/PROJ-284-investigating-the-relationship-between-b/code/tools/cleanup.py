"""
Code cleanup and refactoring utilities for the llmXive pipeline.

This module provides functions to:
1. Validate and clean configuration files
2. Remove temporary and cache files
3. Standardize imports across the codebase
4. Generate code quality reports
"""
import os
import sys
import logging
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
import configparser
import shutil
import tempfile

from config import get_config, validate_config
from logging_config import setup_logging, get_logger

@dataclass
class CleanupReport:
    """Summary of cleanup operations performed."""
    files_scanned: int = 0
    files_modified: int = 0
    temp_files_removed: int = 0
    cache_files_removed: int = 0
    import_issues_fixed: int = 0
    config_validated: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class CodeCleaner:
    """Handles code cleanup and refactoring operations."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self.report = CleanupReport()
        
        # Patterns for temporary and cache files
        self.temp_patterns = [
            '*.pyc', '__pycache__', '*.pyo', '*.pyd',
            '.pytest_cache', '.mypy_cache', '.ruff_cache',
            '*.log', '*.tmp', '*.bak', '*~'
        ]
        
        # Standard imports that should be at the top
        self.stdlib_imports = {
            'os', 'sys', 'pathlib', 'typing', 'dataclasses',
            'logging', 'json', 'csv', 're', 'ast', 'tempfile',
            'shutil', 'subprocess', 'collections', 'itertools',
            'functools', 'operator', 'datetime', 'time', 'hashlib'
        }
        
        # Third-party imports
        self.third_party_imports = {
            'numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib',
            'seaborn', 'nilearn', 'nibabel', 'networkx', 'requests',
            'statsmodels', 'pytest', 'ruff', 'black'
        }

    def scan_directory(self, directory: Path, extensions: List[str] = None) -> List[Path]:
        """Recursively scan directory for files with specified extensions."""
        if extensions is None:
            extensions = ['.py', '.md', '.txt', '.cfg', '.ini', '.json', '.yaml', '.yml']
        
        files = []
        for ext in extensions:
            files.extend(directory.rglob(f'*{ext}'))
        
        self.report.files_scanned = len(files)
        return files

    def remove_temp_files(self) -> int:
        """Remove temporary and cache files from the project."""
        removed_count = 0
        
        for pattern in self.temp_patterns:
            for path in self.project_root.rglob(pattern):
                try:
                    if path.is_file():
                        path.unlink()
                        removed_count += 1
                    elif path.is_dir():
                        shutil.rmtree(path)
                        removed_count += 1
                except (PermissionError, OSError) as e:
                    self.report.errors.append(f"Failed to remove {path}: {e}")
        
        self.report.temp_files_removed += removed_count
        self.logger.info(f"Removed {removed_count} temporary/cache files")
        return removed_count

    def analyze_imports(self, file_path: Path) -> Tuple[List[str], List[str], List[str]]:
        """Analyze imports in a Python file and categorize them."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            stdlib = []
            third_party = []
            local = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split('.')[0]
                        if name in self.stdlib_imports:
                            stdlib.append(alias.name)
                        elif name in self.third_party_imports:
                            third_party.append(alias.name)
                        else:
                            local.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        name = node.module.split('.')[0]
                        if name in self.stdlib_imports:
                            stdlib.append(node.module)
                        elif name in self.third_party_imports:
                            third_party.append(node.module)
                        else:
                            local.append(node.module)
                    else:
                        local.append('local')
            
            return stdlib, third_party, local
        except SyntaxError as e:
            self.report.errors.append(f"Syntax error in {file_path}: {e}")
            return [], [], []
        except Exception as e:
            self.report.errors.append(f"Error analyzing {file_path}: {e}")
            return [], [], []

    def standardize_imports(self, file_path: Path) -> bool:
        """Standardize import order in a Python file (stdlib, third-party, local)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find import lines
            import_lines = []
            non_import_lines = []
            in_import_block = False
            current_import_block = []
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('import ') or stripped.startswith('from '):
                    if not in_import_block:
                        in_import_block = True
                        current_import_block = []
                    current_import_block.append((i, line))
                else:
                    if in_import_block:
                        import_lines.append(current_import_block)
                        in_import_block = False
                        current_import_block = []
                    non_import_lines.append((i, line))
            
            if in_import_block:
                import_lines.append(current_import_block)
            
            if not import_lines:
                return False
            
            # Combine all imports and categorize
            all_imports = []
            for block in import_lines:
                for _, line in block:
                    all_imports.append(line)
            
            stdlib, third_party, local = self.analyze_imports(file_path)
            
            # Reorder imports
            ordered_imports = []
            
            # Add stdlib imports first
            seen_stdlib = set()
            for imp in stdlib:
                if imp not in seen_stdlib:
                  ordered_imports.append(f"import {imp}\n" if imp not in ['os', 'sys', 'pathlib', 'typing', 'dataclasses', 'logging', 'json', 'csv', 're', 'ast', 'tempfile', 'shutil', 'subprocess', 'collections', 'itertools', 'functools', 'operator', 'datetime', 'time', 'hashlib'] else f"import {imp}\n")
                  seen_stdlib.add(imp)
            
            # Add third-party imports
            seen_third_party = set()
            for imp in third_party:
                if imp not in seen_third_party:
                  ordered_imports.append(f"import {imp}\n" if imp not in ['numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib', 'seaborn', 'nilearn', 'nibabel', 'networkx', 'requests', 'statsmodels', 'pytest', 'ruff', 'black'] else f"import {imp}\n")
                  seen_third_party.add(imp)
            
            # Add local imports
            seen_local = set()
            for imp in local:
                if imp not in seen_local and imp != 'local':
                  ordered_imports.append(f"from {imp} import *\n")
                  seen_local.add(imp)
            
            # Reconstruct file with standardized imports
            new_lines = non_import_lines.copy()
            for i, (orig_idx, line) in enumerate(new_lines):
                if orig_idx == 0 and (line.strip().startswith('"""') or line.strip().startswith('#')):
                    # Keep docstring or comment at top
                    continue
            
            # Find where to insert imports (after docstring)
            insert_pos = 0
            for i, (idx, line) in enumerate(new_lines):
                if line.strip().startswith('"""') or line.strip().startswith("#"):
                    insert_pos = i + 1
                else:
                    break
            
            # Rebuild file content
            new_content = ""
            for i, (idx, line) in enumerate(new_lines):
                if i == insert_pos:
                    for imp in ordered_imports:
                        new_content += imp
                new_content += line
            
            if insert_pos == 0:
                for imp in ordered_imports:
                    new_content += imp
                for _, line in new_lines:
                    new_content += line
            
            # Write back if changed
            if new_content != ''.join(lines):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.report.files_modified += 1
                self.report.import_issues_fixed += 1
                self.logger.info(f"Standardized imports in {file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.report.errors.append(f"Error standardizing imports in {file_path}: {e}")
            return False

    def validate_config_files(self) -> bool:
        """Validate configuration files for consistency and correctness."""
        try:
            # Validate config.py
            if not validate_config():
                self.report.warnings.append("Config validation failed")
                return False
            
            self.report.config_validated = True
            self.logger.info("Configuration validated successfully")
            return True
        except Exception as e:
            self.report.errors.append(f"Config validation error: {e}")
            return False

    def clean_codebase(self) -> CleanupReport:
        """Perform full codebase cleanup."""
        self.logger.info("Starting codebase cleanup...")
        
        # Remove temp files
        self.remove_temp_files()
        
        # Validate config
        self.validate_config_files()
        
        # Standardize imports in Python files
        python_files = self.scan_directory(self.project_root, ['.py'])
        
        for file_path in python_files:
            # Skip __init__.py and test files for import standardization
            if file_path.name == '__init__.py' or 'test' in str(file_path):
                continue
            
            self.standardize_imports(file_path)
        
        self.logger.info(f"Cleanup complete. Files modified: {self.report.files_modified}")
        return self.report

    def generate_report(self, output_path: Path) -> None:
        """Generate a cleanup report."""
        report_content = f"""
# Code Cleanup Report
Generated: {__import__('datetime').datetime.now().isoformat()}

## Summary
- Files Scanned: {self.report.files_scanned}
- Files Modified: {self.report.files_modified}
- Temp Files Removed: {self.report.temp_files_removed}
- Cache Files Removed: {self.report.cache_files_removed}
- Import Issues Fixed: {self.report.import_issues_fixed}
- Config Validated: {'Yes' if self.report.config_validated else 'No'}

## Errors
"""
        if self.report.errors:
            for error in self.report.errors:
                report_content += f"- {error}\n"
        else:
            report_content += "None\n"
        
        report_content += "\n## Warnings\n"
        if self.report.warnings:
            for warning in self.report.warnings:
                report_content += f"- {warning}\n"
        else:
            report_content += "None\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        self.logger.info(f"Report written to {output_path}")

def main():
    """Main entry point for cleanup script."""
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path(__file__).parent.parent
    cleaner = CodeCleaner(project_root)
    
    try:
        report = cleaner.clean_codebase()
        cleaner.generate_report(project_root / 'logs' / 'cleanup_report.txt')
        
        logger.info("Cleanup completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())