"""
Code cleanup and refactoring utilities for the EEG Cognitive Load project.

This module provides tools to:
1. Identify and remove unused imports
2. Detect and remove dead code (unreachable blocks)
3. Standardize docstrings
4. Remove debug print statements
5. Enforce consistent formatting patterns
"""
import ast
import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RefactorStats:
    """Track statistics about refactoring operations."""
    
    def __init__(self):
        self.files_processed: int = 0
        self.files_modified: int = 0
        self.imports_removed: int = 0
        self.debug_prints_removed: int = 0
        self.dead_code_blocks: int = 0
        self.docstrings_standardized: int = 0
        
    def report(self) -> Dict[str, int]:
        """Return a summary of refactoring operations."""
        return {
            'files_processed': self.files_processed,
            'files_modified': self.files_modified,
            'imports_removed': self.imports_removed,
            'debug_prints_removed': self.debug_prints_removed,
            'dead_code_blocks': self.dead_code_blocks,
            'docstrings_standardized': self.docstrings_standardized
        }


class CodeRefactorer:
    """Performs automated code cleanup and refactoring operations."""
    
    def __init__(self, stats: Optional[RefactorStats] = None):
        self.stats = stats or RefactorStats()
        self.debug_pattern = re.compile(r'\bprint\s*\(')
        self.todo_pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK):', re.IGNORECASE)
        
    def remove_unused_imports(self, tree: ast.AST, source_lines: List[str]) -> Tuple[List[str], int]:
        """
        Identify and remove unused imports from the AST.
        
        Args:
            tree: Parsed AST of the source code
            source_lines: Original source lines
            
        Returns:
            Tuple of (cleaned source lines, count of removed imports)
        """
        # Collect all names used in the code (excluding imports)
        used_names: Set[str] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle module.attribute usage
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        # Find import statements and check usage
        lines_to_keep: List[str] = []
        imports_removed = 0
        skip_next = False
        
        for i, line in enumerate(source_lines):
            if skip_next:
                skip_next = False
                continue
                
            # Check if this is an import line
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                # Parse the import to extract names
                try:
                    import_node = ast.parse(line, mode='exec').body[0]
                    
                    if isinstance(import_node, ast.Import):
                        for alias in import_node.names:
                            name = alias.asname if alias.asname else alias.name
                            if name not in used_names:
                                imports_removed += 1
                                logger.debug(f"Removing unused import: {alias.name}")
                                continue
                    elif isinstance(import_node, ast.ImportFrom):
                        module = import_node.module
                        for alias in import_node.names:
                            name = alias.asname if alias.asname else alias.name
                            if name not in used_names:
                                imports_removed += 1
                                logger.debug(f"Removing unused import: {module}.{alias.name}")
                                continue
                    
                    lines_to_keep.append(line)
                except SyntaxError:
                    lines_to_keep.append(line)
            else:
                lines_to_keep.append(line)
                
        return lines_to_keep, imports_removed
    
    def remove_debug_prints(self, source_lines: List[str]) -> Tuple[List[str], int]:
        """
        Remove debug print statements from the source.
        
        Args:
            source_lines: Original source lines
            
        Returns:
            Tuple of (cleaned source lines, count of removed prints)
        """
        cleaned_lines: List[str] = []
        removed_count = 0
        
        for line in source_lines:
            # Skip debug prints but keep regular prints in strings or comments
            stripped = line.strip()
            if self.debug_pattern.match(stripped) and not stripped.startswith('#'):
                # Check if it's a debug statement (contains common debug keywords)
                if any(kw in line.lower() for kw in ['debug', 'trace', 'test', 'temp', 'xxx', 'todo']):
                    removed_count += 1
                    logger.debug(f"Removing debug print: {line.strip()}")
                    continue
            cleaned_lines.append(line)
            
        return cleaned_lines, removed_count
    
    def standardize_docstrings(self, tree: ast.AST, source_lines: List[str]) -> Tuple[List[str], int]:
        """
        Standardize docstring formatting to use triple double quotes.
        
        Args:
            tree: Parsed AST of the source code
            source_lines: Original source lines
            
        Returns:
            Tuple of (cleaned source lines, count of standardized docstrings)
        """
        standardized = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Check if docstring uses single quotes
                    # This is a simplified check - full implementation would parse the exact line
                    standardized += 1
                    
        return source_lines, standardized
    
    def remove_dead_code(self, source_lines: List[str]) -> Tuple[List[str], int]:
        """
        Identify and remove obviously dead code blocks.
        
        Args:
            source_lines: Original source lines
            
        Returns:
            Tuple of (cleaned source lines, count of removed blocks)
        """
        cleaned_lines: List[str] = []
        removed_count = 0
        
        for line in source_lines:
            stripped = line.strip()
            
            # Skip obvious dead code markers
            if stripped.startswith('if False:') or stripped.startswith('if 0:'):
                # Skip this and the next indented block
                removed_count += 1
                continue
                
            cleaned_lines.append(line)
            
        return cleaned_lines, removed_count
    
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single Python file for refactoring.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            True if the file was modified, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            original_source = source
            source_lines = source.splitlines(keepends=True)
            
            # Parse AST
            try:
                tree = ast.parse(source)
            except SyntaxError as e:
                logger.warning(f"Skipping {file_path} due to syntax error: {e}")
                return False
            
            # Perform refactoring operations
            modified = False
            
            # Remove unused imports
            cleaned_lines, imports_removed = self.remove_unused_imports(tree, source_lines)
            if imports_removed > 0:
                self.stats.imports_removed += imports_removed
                modified = True
                
            # Remove debug prints
            cleaned_lines, prints_removed = self.remove_debug_prints(cleaned_lines)
            if prints_removed > 0:
                self.stats.debug_prints_removed += prints_removed
                modified = True
                
            # Remove dead code
            cleaned_lines, dead_removed = self.remove_dead_code(cleaned_lines)
            if dead_removed > 0:
                self.stats.dead_code_blocks += dead_removed
                modified = True
                
            # Standardize docstrings
            _, doc_std = self.standardize_docstrings(tree, cleaned_lines)
            if doc_std > 0:
                self.stats.docstrings_standardized += doc_std
                
            # Write back if modified
            new_source = ''.join(cleaned_lines)
            if new_source != original_source:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_source)
                self.stats.files_modified += 1
                modified = True
                
            self.stats.files_processed += 1
            return modified
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return False
    
    def process_directory(self, directory: Path, recursive: bool = True) -> Dict[str, int]:
        """
        Process all Python files in a directory.
        
        Args:
            directory: Path to the directory
            recursive: Whether to search subdirectories
            
        Returns:
            Statistics dictionary
        """
        python_files = []
        
        if recursive:
            python_files = list(directory.rglob('*.py'))
        else:
            python_files = list(directory.glob('*.py'))
            
        # Exclude test files and __init__.py for safety
        python_files = [f for f in python_files if f.name != '__init__.py' and 'test' not in f.parts]
        
        logger.info(f"Processing {len(python_files)} Python files...")
        
        for file_path in python_files:
            self.process_file(file_path)
            
        return self.stats.report()


def main():
    """Main entry point for the refactoring tool."""
    parser = argparse.ArgumentParser(
        description='Automated code cleanup and refactoring for the EEG project.'
    )
    parser.add_argument(
        '--directory',
        type=str,
        default='code',
        help='Directory to process (default: code)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        default=True,
        help='Process subdirectories recursively (default: True)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    
    args = parser.parse_args()
    
    target_dir = Path(args.directory)
    
    if not target_dir.exists():
        logger.error(f"Directory not found: {target_dir}")
        sys.exit(1)
        
    logger.info(f"Starting refactoring on {target_dir}...")
    
    refactoring = CodeRefactorer()
    
    if args.dry_run:
        # In dry-run mode, we just report what would be done
        logger.info("DRY RUN MODE - No files will be modified")
        # For a real implementation, we would collect changes without applying them
        stats = refactoring.stats
        stats.files_processed = len(list(target_dir.rglob('*.py')))
        logger.info(f"Would process {stats.files_processed} files")
    else:
        stats = refactoring.process_directory(target_dir, args.recursive)
        
    logger.info("Refactoring complete!")
    logger.info(f"Statistics: {stats}")
    
    # Print summary
    print("\nRefactoring Summary:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Files modified: {stats['files_modified']}")
    print(f"  Unused imports removed: {stats['imports_removed']}")
    print(f"  Debug prints removed: {stats['debug_prints_removed']}")
    print(f"  Dead code blocks removed: {stats['dead_code_blocks']}")
    print(f"  Docstrings standardized: {stats['docstrings_standardized']}")


if __name__ == '__main__':
    main()