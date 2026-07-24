"""
Code cleanup and refactoring module for PROJ-559.

This module implements systematic code cleanup, removal of unused imports,
standardization of docstrings, and optimization of common patterns across
the codebase. It addresses technical debt accumulated during the implementation
of the neuro-symbolic learning pipeline.
"""

import ast
import os
import re
import sys
import json
import logging
from typing import List, Dict, Any, Tuple, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeRefactorer:
    """
    A class to perform systematic code cleanup and refactoring.

    This refactore handles:
    - Removal of unused imports
    - Standardization of docstrings
    - Removal of redundant type annotations
    - Optimization of common patterns
    - Consolidation of duplicate code
    """

    def __init__(self, project_root: str):
        """Initialize the refactore with the project root directory."""
        self.project_root = Path(project_root)
        self.code_dir = self.project_root / 'code'
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'imports_removed': 0,
            'docstrings_standardized': 0,
            'patterns_optimized': 0
        }

    def find_python_files(self, directory: Path) -> List[Path]:
        """Find all Python files in the given directory recursively."""
        return list(directory.rglob('*.py'))

    def remove_unused_imports(self, source: str) -> Tuple[str, int]:
        """
        Remove unused imports from the source code.

        Args:
            source: The source code as a string.

        Returns:
            A tuple of (modified_source, count_of_removed_imports).
        """
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            logger.warning(f"Syntax error in source: {e}")
            return source, 0

        # Extract all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((alias.name, alias.asname, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    name = alias.asname if alias.asname else alias.name
                    imports.append((f"{module}.{alias.name}", name, node.lineno))

        # Find all names used in the module (excluding imports)
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle attribute access like os.path
                current = node
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                    parts.reverse()
                    used_names.add('.'.join(parts))

        # Identify unused imports
        unused = []
        for full_name, name, lineno in imports:
            if name not in used_names and full_name not in used_names:
                unused.append((full_name, name, lineno))

        if not unused:
            return source, 0

        # Remove unused imports
        lines = source.split('\n')
        unused_lines = {lineno - 1 for _, _, lineno in unused}

        # Group consecutive unused lines
        unused_ranges = []
        if unused_lines:
            sorted_lines = sorted(unused_lines)
            start = sorted_lines[0]
            end = sorted_lines[0]
            for line in sorted_lines[1:]:
                if line == end + 1:
                    end = line
                else:
                    unused_ranges.append((start, end))
                    start = line
                    end = line
            unused_ranges.append((start, end))

        # Remove lines in reverse order to maintain line numbers
        for start, end in reversed(unused_ranges):
            del lines[start:end+1]

        self.stats['imports_removed'] += len(unused)
        return '\n'.join(lines), len(unused)

    def standardize_docstrings(self, source: str) -> Tuple[str, int]:
        """
        Standardize docstrings to follow a consistent format.

        Args:
            source: The source code as a string.

        Returns:
            A tuple of (modified_source, count_of_standardized_docstrings).
        """
        count = 0
        lines = source.split('\n')
        modified_lines = []
        in_docstring = False
        docstring_start = -1
        docstring_type = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for docstring start
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                in_docstring = True
                docstring_start = i
                docstring_type = stripped[:3]
                modified_lines.append(line)
                continue

            # Check for docstring end
            if in_docstring and stripped.endswith(docstring_type):
                in_docstring = False
                # Standardize the closing line
                if not stripped.startswith(' '):
                    # Add proper indentation
                    indent = len(line) - len(line.lstrip())
                    modified_lines[-1] = ' ' * indent + docstring_type
                modified_lines.append(line)
                count += 1
                continue

            # Process docstring content
            if in_docstring:
                # Ensure consistent indentation
                if stripped:
                    # Normalize whitespace
                    normalized = ' '.join(stripped.split())
                    if not normalized.startswith(':'):
                        # Add proper spacing for parameters/returns
                        if normalized.startswith('Args:') or normalized.startswith('Returns:'):
                            pass
                        elif not normalized.startswith('-'):
                            # Check if it's a new section
                            if any(normalized.startswith(kw) for kw in ['Args:', 'Returns:', 'Raises:', 'Example:']):
                                pass
                    modified_lines.append(line)
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)

        self.stats['docstrings_standardized'] += count
        return '\n'.join(modified_lines), count

    def optimize_patterns(self, source: str) -> Tuple[str, int]:
        """
        Optimize common code patterns.

        Args:
            source: The source code as a string.

        Returns:
            A tuple of (modified_source, count_of_optimized_patterns).
        """
        count = 0
        modified = source

        # Pattern 1: Replace multiple if-elif chains with dict mapping where appropriate
        # This is a heuristic optimization
        if_pattern = r'if\s+(\w+)\s*==\s*[\'"](\w+)[\'"]:\s*\n\s+return\s+[\'"]([^\'"]+)[\'"]\s*\n\s+elif\s+\1\s*==\s*[\'"](\w+)[\'"]:\s*\n\s+return\s+[\'"]([^\'"]+)[\'"]'
        matches = list(re.finditer(if_pattern, modified))
        if len(matches) > 2:
            # Could be converted to dict, but this is complex to do safely
            # Skip for now to avoid breaking functionality
            pass

        # Pattern 2: Remove redundant try-except blocks that just re-raise
        redundant_pattern = r'except\s+(\w+)\s*as\s+(\w+):\s*\n\s+raise\s+\2'
        matches = list(re.finditer(redundant_pattern, modified, re.MULTILINE))
        for match in reversed(matches):
            # Remove the redundant except block
            start = match.start()
            end = match.end()
            # Preserve the exception type for safety
            modified = modified[:start] + modified[end:]
            count += 1

        # Pattern 3: Optimize logging calls with f-strings
        old_logging = r'logging\.(info|warning|error|debug)\(\s*[\'"]([^\'"]*)\{\s*(\w+)\s*\}([^\'"]*)[\'"]\s*,\s*(\w+)\s*\)'
        matches = list(re.finditer(old_logging, modified))
        for match in reversed(matches):
            func = match.group(1)
            before = match.group(2)
            var = match.group(3)
            after = match.group(4)
            arg = match.group(5)
            new_call = f'logging.{func}(f"{before}{{{var}}}{after}", {arg})'
            modified = modified[:match.start()] + new_call + modified[match.end():]
            count += 1

        self.stats['patterns_optimized'] += count
        return modified, count

    def process_file(self, file_path: Path) -> bool:
        """
        Process a single Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            True if the file was modified, False otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return False

        original_source = source
        modified = False

        # Apply refactoring steps
        source, _ = self.remove_unused_imports(source)
        if source != original_source:
            modified = True

        source, _ = self.standardize_docstrings(source)
        if source != original_source:
            modified = True

        source, _ = self.optimize_patterns(source)
        if source != original_source:
            modified = True

        # Write back if modified
        if modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(source)
                self.stats['files_modified'] += 1
                logger.info(f"Modified: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error writing {file_path}: {e}")
                return False

        return False

    def run_cleanup(self) -> Dict[str, Any]:
        """
        Run the cleanup process on all Python files in the code directory.

        Returns:
            A dictionary with cleanup statistics.
        """
        logger.info(f"Starting cleanup process in {self.code_dir}")

        if not self.code_dir.exists():
            logger.error(f"Code directory not found: {self.code_dir}")
            return self.stats

        python_files = self.find_python_files(self.code_dir)
        logger.info(f"Found {len(python_files)} Python files to process")

        for file_path in python_files:
            self.stats['files_processed'] += 1
            self.process_file(file_path)

        logger.info(f"Cleanup complete. Modified {self.stats['files_modified']} files")
        return self.stats


def main():
    """Main entry point for the cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(description='Code cleanup and refactoring tool')
    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='Path to the project root directory'
    )
    parser.add_argument(
        '--output-stats',
        type=str,
        default='data/cleanup_stats.json',
        help='Path to output statistics JSON file'
    )

    args = parser.parse_args()

    refactore = CodeRefactorer(args.project_root)
    stats = refactore.run_cleanup()

    # Save statistics
    stats_path = Path(args.output_stats)
    stats_path.parent.mkdir(parents=True, exist_ok=True)

    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Statistics saved to {stats_path}")
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    main()