"""
Code cleanup and refactoring module for PROJ-037.

This module implements automated cleanup tasks including:
- Removing unused imports
- Standardizing logging calls
- Enforcing PEP 8 style guidelines
- Consolidating duplicate functions
- Removing debug artifacts
"""

import os
import sys
import re
import ast
import logging
import subprocess
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Standard imports that are commonly used in the project
STANDARD_IMPORTS = {
    'os', 'sys', 're', 'ast', 'logging', 'subprocess', 'json', 'csv',
    'pathlib', 'typing', 'collections', 'itertools', 'functools',
    'warnings', 'math', 'random', 'datetime', 'time', 'hashlib',
    'pickle', 'gzip', 'bz2', 'zipfile', 'tarfile', 'tempfile',
    'shutil', 'glob', 'fnmatch', 'string', 'io', 'argparse',
    'dataclasses', 'enum', 'abc', 'copy', 'operator', 'statistics',
    'numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib', 'seaborn',
    'biom', 'skbio', 'biopython', 'requests'
}

# Patterns to identify debug artifacts
DEBUG_PATTERNS = [
    r'print\s*\([^)]*debug[^)]*\)',
    r'#\s*DEBUG',
    r'#\s*TODO',
    r'#\s*FIXME',
    r'#\s*XXX',
    r'#\s*HACK',
    r'logging\.debug\s*\(',
    r'logger\.debug\s*\('
]

# Patterns to identify placeholder code
PLACEHOLDER_PATTERNS = [
    r'pass\s*#\s*TODO',
    r'raise\s+NotImplementedError',
    r'raise\s+Exception\s*\(',
    r'#\s*implement\s+me',
    r'#\s*stub'
]

class CodeCleanup:
    """
    Main class for automated code cleanup and refactoring.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the CodeCleanup instance.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        self.code_dir = project_root / 'code'
        self.tests_dir = project_root / 'tests'
        self.stats = {
            'files_processed': 0,
            'imports_removed': 0,
            'debug_artifacts_removed': 0,
            'placeholders_found': 0,
            'style_violations_fixed': 0,
            'errors_encountered': 0
        }
    
    def find_python_files(self) -> List[Path]:
        """
        Find all Python files in the project.
        
        Returns:
            List of Path objects for all .py files
        """
        python_files = []
        for directory in [self.code_dir, self.tests_dir]:
            if directory.exists():
                python_files.extend(directory.rglob('*.py'))
        return python_files
    
    def remove_unused_imports(self, file_path: Path) -> Tuple[int, List[str]]:
        """
        Remove unused imports from a Python file.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            Tuple of (number of imports removed, list of removed imports)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Collect all imported names
            imported_names = set()
            import_nodes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imported_names.add(name)
                        import_nodes.append((node, alias))
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imported_names.add(name)
                        import_nodes.append((node, alias))
            
            # Collect all used names
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Handle attribute access like pandas.DataFrame
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Find unused imports
            unused = imported_names - used_names - {'__name__', '__doc__', '__file__'}
            removed_count = 0
            removed_list = []
            
            if unused:
                # Rebuild the file without unused imports
                lines = content.splitlines()
                new_lines = []
                skip_until_blank = False
                
                for i, line in enumerate(lines):
                    if skip_until_blank:
                        if line.strip() == '':
                            skip_until_blank = False
                        continue
                    
                    # Check if this line contains an unused import
                    is_unused_import = False
                    for unused_name in unused:
                        if re.search(rf'\b{re.escape(unused_name)}\b', line):
                            # Check if it's actually an import statement
                            if re.match(r'^\s*(from\s+\S+\s+)?import\s+', line):
                                is_unused_import = True
                                removed_count += 1
                                removed_list.append(unused_name)
                                break
                    
                    if not is_unused_import:
                        new_lines.append(line)
                
                # Write the cleaned file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
            
            return removed_count, removed_list
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors_encountered'] += 1
            return 0, []
    
    def remove_debug_artifacts(self, file_path: Path) -> int:
        """
        Remove debug artifacts from a Python file.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            Number of debug artifacts removed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            removed_count = 0
            
            for pattern in DEBUG_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                removed_count += len(matches)
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors_encountered'] += 1
            return 0
    
    def check_placeholders(self, file_path: Path) -> int:
        """
        Check for placeholder code in a Python file.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            Number of placeholders found
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            placeholder_count = 0
            
            for pattern in PLACEHOLDER_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                placeholder_count += len(matches)
            
            return placeholder_count
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors_encountered'] += 1
            return 0
    
    def standardize_logging(self, file_path: Path) -> int:
        """
        Standardize logging calls in a Python file.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            Number of logging statements standardized
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            standardized_count = 0
            
            # Replace common logging patterns with standard format
            patterns = [
                (r'print\s*\(\s*["\']([^"\']*)["\'].*\)', r'logger.info(\1)'),
                (r'print\s*\(\s*f["\']([^"\']*)["\'].*\)', r'logger.info(\1)'),
                (r'logging\.info\s*\(', r'logger.info('),
                (r'logging\.warning\s*\(', r'logger.warning('),
                (r'logging\.error\s*\(', r'logger.error('),
                (r'logging\.debug\s*\(', r'logger.debug('),
                (r'logging\.critical\s*\(', r'logger.critical('),
            ]
            
            for pattern, replacement in patterns:
                matches = re.findall(pattern, content)
                standardized_count += len(matches)
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return standardized_count
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats['errors_encountered'] += 1
            return 0
    
    def run_black_formatting(self, file_path: Path) -> bool:
        """
        Run black formatting on a Python file.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            True if formatting was successful, False otherwise
        """
        try:
            result = subprocess.run(
                ['black', '--quiet', str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Could not run black on {file_path}: {e}")
            return False
    
    def process_file(self, file_path: Path) -> Dict[str, int]:
        """
        Process a single Python file for cleanup.
        
        Args:
            file_path: Path to the Python file
        
        Returns:
            Dictionary of cleanup statistics for this file
        """
        file_stats = {
            'imports_removed': 0,
            'debug_artifacts_removed': 0,
            'placeholders_found': 0,
            'logging_standardized': 0
        }
        
        logger.info(f"Processing {file_path}")
        
        # Remove unused imports
        removed, _ = self.remove_unused_imports(file_path)
        file_stats['imports_removed'] = removed
        self.stats['imports_removed'] += removed
        
        # Remove debug artifacts
        debug_removed = self.remove_debug_artifacts(file_path)
        file_stats['debug_artifacts_removed'] = debug_removed
        self.stats['debug_artifacts_removed'] += debug_removed
        
        # Check for placeholders
        placeholders = self.check_placeholders(file_path)
        file_stats['placeholders_found'] = placeholders
        self.stats['placeholders_found'] += placeholders
        
        # Standardize logging
        logging_std = self.standardize_logging(file_path)
        file_stats['logging_standardized'] = logging_std
        self.stats['style_violations_fixed'] += logging_std
        
        # Run black formatting
        if self.run_black_formatting(file_path):
            self.stats['style_violations_fixed'] += 1
        
        self.stats['files_processed'] += 1
        
        return file_stats
    
    def run_cleanup(self) -> Dict[str, int]:
        """
        Run cleanup on all Python files in the project.
        
        Returns:
            Dictionary of overall cleanup statistics
        """
        logger.info("Starting code cleanup...")
        
        python_files = self.find_python_files()
        logger.info(f"Found {len(python_files)} Python files to process")
        
        for file_path in python_files:
            self.process_file(file_path)
        
        logger.info(f"Cleanup complete. Processed {self.stats['files_processed']} files.")
        logger.info(f"Removed {self.stats['imports_removed']} unused imports.")
        logger.info(f"Removed {self.stats['debug_artifacts_removed']} debug artifacts.")
        logger.info(f"Found {self.stats['placeholders_found']} placeholders.")
        logger.info(f"Fixed {self.stats['style_violations_fixed']} style violations.")
        
        if self.stats['errors_encountered'] > 0:
            logger.warning(f"Encountered {self.stats['errors_encountered']} errors during cleanup.")
        
        return self.stats.copy()

def main():
    """Main entry point for the cleanup script."""
    parser = argparse.ArgumentParser(description='Code cleanup and refactoring tool')
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path('.'),
        help='Path to the project root directory'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    cleanup = CodeCleanup(args.project_root)
    stats = cleanup.run_cleanup()
    
    print("\nCleanup Summary:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Imports removed: {stats['imports_removed']}")
    print(f"  Debug artifacts removed: {stats['debug_artifacts_removed']}")
    print(f"  Placeholders found: {stats['placeholders_found']}")
    print(f"  Style violations fixed: {stats['style_violations_fixed']}")
    print(f"  Errors encountered: {stats['errors_encountered']}")

if __name__ == '__main__':
    main()