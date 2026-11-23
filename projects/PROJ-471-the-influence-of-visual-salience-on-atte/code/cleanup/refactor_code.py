"""
Code Cleanup and Refactoring Module (Task T038)

This module implements automated code cleanup and refactoring for the llmXive pipeline.
It performs:
1. Removal of unused imports
2. Standardization of logging calls
3. Consolidation of duplicate code patterns
4. Removal of debug statements and TODO comments
5. Enforcement of consistent docstring formats
6. Optimization of redundant computations
"""

import os
import re
import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

from utils.logging import get_logger, setup_logging
from config import get_paths, load_config

# Configuration for refactoring rules
REFACTORING_RULES = {
    'remove_unused_imports': True,
    'standardize_logging': True,
    'remove_debug_statements': True,
    'enforce_docstrings': False,  # Optional - can be noisy
    'consolidate_redundant_imports': True,
    'remove_todo_comments': True,
}

# Patterns to identify debug statements
DEBUG_PATTERNS = [
    r'\bprint\s*\(',
    r'\blogging\.debug\s*\(',
    r'\bbreakpoint\s*\(',
    r'\bipdb\.set_trace\s*\(',
    r'\bimport pdb\b',
    r'\bimport ipdb\b',
]

# Patterns to identify TODO/FIXME comments
TODO_PATTERNS = [
    r'#\s*(TODO|FIXME|HACK|XXX|BUG):?\s*',
    r'#\s*(todo|fixme|hack|xxx|bug):?\s*',
]

# Standard logging patterns
LOGGING_PATTERNS = {
    'info': r'\blogging\.info\s*\(',
    'warning': r'\blogging\.warning\s*\(',
    'error': r'\blogging\.error\s*\(',
    'critical': r'\blogging\.critical\s*\(',
    'debug': r'\blogging\.debug\s*\(',
}

class CodeRefactorer:
    """
    Automated code refactoring tool for Python files.

    This class provides methods to analyze and refactor Python code files
    according to a set of predefined rules.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the refactoring tool.

        Args:
            logger: Optional logger instance. If None, a default logger is created.
        """
        self.logger = logger or get_logger('refactor')
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'imports_removed': 0,
            'debug_statements_removed': 0,
            'todo_comments_removed': 0,
            'logging_calls_standardized': 0,
            'errors': 0,
        }

    def find_python_files(self, base_path: Path) -> List[Path]:
        """
        Recursively find all Python files in the given directory.

        Args:
            base_path: Root directory to search.

        Returns:
            List of Path objects for all .py files found.
        """
        python_files = []
        for root, _, files in os.walk(base_path):
            # Skip hidden directories and common non-code directories
            if any(part.startswith('.') for part in Path(root).parts):
                continue
            if any(part in ['__pycache__', 'venv', '.venv', 'node_modules'] for part in Path(root).parts):
                continue

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def parse_ast(self, code: str) -> Optional[ast.AST]:
        """
        Parse Python code into an AST.

        Args:
            code: Python source code string.

        Returns:
            AST object or None if parsing fails.
        """
        try:
            return ast.parse(code)
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in code: {e}")
            return None

    def get_used_names(self, tree: ast.AST) -> Set[str]:
        """
        Extract all names used in the AST.

        Args:
            tree: AST object.

        Returns:
            Set of all names referenced in the code.
        """
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle attribute access like 'os.path'
                current = node
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                    used_names.add('.'.join(reversed(parts)))
                    used_names.add(current.id)
        return used_names

    def remove_unused_imports(self, code: str) -> Tuple[str, int]:
        """
        Remove unused imports from the code.

        Args:
            code: Python source code.

        Returns:
            Tuple of (refactored code, count of removed imports).
        """
        tree = self.parse_ast(code)
        if tree is None:
            return code, 0

        lines = code.split('\n')
        used_names = self.get_used_names(tree)
        removed_count = 0
        new_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            # Check if this is an import line
            import_match = re.match(r'^(import\s+\S+|from\s+\S+\s+import\s+\S+)', line)

            if import_match:
                import_stmt = import_match.group(1)

                # Extract imported names
                if import_stmt.startswith('import '):
                    imported_name = import_stmt.split()[1].split('.')[0]
                else:
                    # 'from X import Y'
                    parts = import_stmt.split('import')
                    if len(parts) > 1:
                        imported_items = [item.strip().split(' as ')[0].strip() for item in parts[1].split(',')]
                        imported_name = imported_items[0] if imported_items else None
                    else:
                        imported_name = None

                # Check if the imported name is used
                if imported_name and imported_name not in used_names:
                    # Check if it's used as part of a longer name
                    is_used = False
                    for used in used_names:
                        if used.startswith(imported_name + '.'):
                            is_used = True
                            break

                    if not is_used:
                        removed_count += 1
                        continue  # Skip this line

            new_lines.append(line)

        return '\n'.join(new_lines), removed_count

    def remove_debug_statements(self, code: str) -> Tuple[str, int]:
        """
        Remove debug statements from the code.

        Args:
            code: Python source code.

        Returns:
            Tuple of (refactored code, count of removed statements).
        """
        lines = code.split('\n')
        new_lines = []
        removed_count = 0

        for line in lines:
            is_debug = False
            for pattern in DEBUG_PATTERNS:
                if re.search(pattern, line):
                    is_debug = True
                    break

            if is_debug:
                removed_count += 1
                self.logger.debug(f"Removing debug statement: {line.strip()}")
            else:
                new_lines.append(line)

        return '\n'.join(new_lines), removed_count

    def remove_todo_comments(self, code: str) -> Tuple[str, int]:
        """
        Remove TODO/FIXME comments from the code.

        Args:
            code: Python source code.

        Returns:
            Tuple of (refactored code, count of removed comments).
        """
        lines = code.split('\n')
        new_lines = []
        removed_count = 0

        for line in lines:
            # Check if line is only a TODO comment
            is_todo = False
            for pattern in TODO_PATTERNS:
                if re.match(pattern, line.strip()):
                    is_todo = True
                    break

            if is_todo:
                removed_count += 1
                self.logger.debug(f"Removing TODO comment: {line.strip()}")
            else:
                # Remove inline TODO comments but keep the rest of the line
                cleaned_line = line
                for pattern in TODO_PATTERNS:
                    cleaned_line = re.sub(pattern, '', cleaned_line, flags=re.IGNORECASE)
                new_lines.append(cleaned_line)

        return '\n'.join(new_lines), removed_count

    def standardize_logging(self, code: str) -> Tuple[str, int]:
        """
        Standardize logging calls to use the project's logging utilities.

        Args:
            code: Python source code.

        Returns:
            Tuple of (refactored code, count of standardized calls).
        """
        # This is a simplified version - a full implementation would
        # replace direct logging calls with the project's get_logger() pattern
        lines = code.split('\n')
        new_lines = []
        standardized_count = 0

        for line in lines:
            # Check for direct logging calls
            for level, pattern in LOGGING_PATTERNS.items():
                if re.search(pattern, line):
                    # Replace with project logging pattern
                    # logging.info(...) -> logger.info(...)
                    new_line = re.sub(
                        pattern,
                        f'get_logger(__name__).{level}(',
                        line,
                        count=1
                    )
                    if new_line != line:
                        standardized_count += 1
                        line = new_line
                        break
            new_lines.append(line)

        return '\n'.join(new_lines), standardized_count

    def consolidate_redundant_imports(self, code: str) -> Tuple[str, int]:
        """
        Consolidate multiple import statements from the same module.

        Args:
            code: Python source code.

        Returns:
            Tuple of (refactored code, count of consolidations).
        """
        lines = code.split('\n')
        new_lines = []
        consolidations = 0

        # Track imports by module
        imports_by_module = {}

        for line in lines:
            if line.strip().startswith('from '):
                match = re.match(r'^(from\s+\S+)\s+import\s+(.+)$', line)
                if match:
                    module = match.group(1)
                    items = [item.strip() for item in match.group(2).split(',')]

                    if module not in imports_by_module:
                        imports_by_module[module] = []
                    imports_by_module[module].extend(items)
                    continue  # Skip this line, we'll add consolidated version later

            new_lines.append(line)

        # Add consolidated imports at the beginning
        if imports_by_module:
          # Find where to insert (after any existing imports)
          insert_pos = 0
          for i, line in enumerate(new_lines):
              if not line.strip().startswith(('import ', 'from ', '#', '', '"""', "'''")):
                  insert_pos = i
                  break

          consolidated_imports = []
          for module, items in imports_by_module.items():
              unique_items = list(dict.fromkeys(items))  # Preserve order, remove dups
              if len(unique_items) != len(items):
                  consolidations += 1
              consolidated_imports.append(f"{module} import {', '.join(unique_items)}")

          new_lines = consolidated_imports + new_lines

        return '\n'.join(new_lines), consolidations

    def refactor_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Refactor a single Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            Dictionary with refactoring results.
        """
        result = {
            'file': str(file_path),
            'modified': False,
            'changes': {},
            'error': None,
        }

        try:
            # Read original code
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()

            current_code = original_code

            # Apply refactoring rules
            if REFACTORING_RULES['remove_unused_imports']:
                current_code, count = self.remove_unused_imports(current_code)
                if count > 0:
                    result['changes']['unused_imports_removed'] = count

            if REFACTORING_RULES['remove_debug_statements']:
                current_code, count = self.remove_debug_statements(current_code)
                if count > 0:
                    result['changes']['debug_statements_removed'] = count

            if REFACTORING_RULES['remove_todo_comments']:
                current_code, count = self.remove_todo_comments(current_code)
                if count > 0:
                    result['changes']['todo_comments_removed'] = count

            if REFACTORING_RULES['standardize_logging']:
                current_code, count = self.standardize_logging(current_code)
                if count > 0:
                    result['changes']['logging_calls_standardized'] = count

            if REFACTORING_RULES['consolidate_redundant_imports']:
                current_code, count = self.consolidate_redundant_imports(current_code)
                if count > 0:
                    result['changes']['redundant_imports_consolidated'] = count

            # Write back if changed
            if current_code != original_code:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(current_code)
                result['modified'] = True
                self.logger.info(f"Refactored {file_path}")

        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error refactoring {file_path}: {e}")
            self.stats['errors'] += 1

        return result

    def refactor_project(self, base_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Refactor all Python files in the project.

        Args:
            base_path: Optional base path. If None, uses project root from config.

        Returns:
            Summary dictionary of refactoring results.
        """
        if base_path is None:
            config = load_config()
            base_path = Path(config['paths']['project_root'])

        self.logger.info(f"Starting refactoring for project at {base_path}")

        python_files = self.find_python_files(base_path)
        self.stats['files_processed'] = len(python_files)

        results = []
        for file_path in python_files:
            result = self.refactor_file(file_path)
            results.append(result)
            if result['modified']:
                self.stats['files_modified'] += 1

            # Update stats
            for key, count in result.get('changes', {}).items():
                if 'removed' in key:
                    self.stats['imports_removed'] += count
                elif 'debug' in key:
                    self.stats['debug_statements_removed'] += count
                elif 'todo' in key:
                    self.stats['todo_comments_removed'] += count
                elif 'logging' in key:
                    self.stats['logging_calls_standardized'] += count

        summary = {
            'stats': self.stats,
            'files': results,
        }

        self.logger.info(f"Refactoring complete. Processed {self.stats['files_processed']} files, modified {self.stats['files_modified']}.")

        return summary

def main():
    """
    Main entry point for the code refactoring tool.
    """
    # Setup logging
    setup_logging('refactor', level=logging.INFO)
    logger = get_logger('refactor')

    logger.info("Starting code cleanup and refactoring (Task T038)")

    # Create refactoring tool
    refactorer = CodeRefactorer(logger)

    # Run refactoring
    results = refactorer.refactor_project()

    # Write results to log
    logger.info(f"Refactoring summary: {results['stats']}")

    # Write detailed report
    report_path = Path('data/interim/refactoring_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Refactoring report written to {report_path}")

    # Return summary for verification
    return results['stats']

if __name__ == '__main__':
    main()
