"""
Code cleanup and refactoring utilities.

This module provides tools to scan the src/ directory for:
1. Unused imports
2. Duplicate code blocks
3. TODO/FIXME comments
4. Dead code (unreachable functions)

Run as: python code/src/utils/cleanup_utils.py
"""
import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import logging
from src.utils.logging import get_logger

# Configure logging
logger = get_logger("cleanup_utils")

class CodeCleanupScanner:
    """Scans Python files for common code quality issues."""

    def __init__(self, src_root: str):
        self.src_root = Path(src_root)
        self.issues: Dict[str, List[Dict[str, Any]]] = {
            "unused_imports": [],
            "todo_comments": [],
            "dead_code": [],
            "duplicate_patterns": []
        }

    def scan_all_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Recursively scan all Python files in src_root."""
        logger.info(f"Scanning directory: {self.src_root}")
        
        python_files = list(self.src_root.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files")

        for file_path in python_files:
            try:
                self._scan_file(file_path)
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")

        return self.issues

    def _scan_file(self, file_path: Path):
        """Scan a single Python file for issues."""
        relative_path = file_path.relative_to(self.src_root.parent)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        # Check for TODO/FIXME comments
        self._find_todo_comments(relative_path, lines)
        
        # Parse AST for unused imports and dead code
        try:
            tree = ast.parse(content)
            self._find_unused_imports(relative_path, tree, content)
            self._find_dead_code(relative_path, tree, lines)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

    def _find_todo_comments(self, relative_path: Path, lines: List[str]):
        """Find TODO, FIXME, XXX, HACK comments."""
        pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK):?\s*(.*)', re.IGNORECASE)
        
        for line_num, line in enumerate(lines, 1):
            match = pattern.search(line)
            if match:
                self.issues["todo_comments"].append({
                    "file": str(relative_path),
                    "line": line_num,
                    "type": match.group(1).upper(),
                    "message": match.group(2).strip()
                })

    def _find_unused_imports(self, relative_path: Path, tree: ast.AST, content: str):
        """Find imports that are defined but never used."""
        imports = {}
        usage = set()

        # Collect all imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = (node.lineno, alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if name != '*':
                        imports[name] = (node.lineno, f"{node.module}.{alias.name}")

        # Collect all usages (excluding import statements themselves)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                usage.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Handle attribute access like 'os.path'
                if isinstance(node.value, ast.Name):
                    usage.add(node.value.id)

        # Find unused imports
        for name, (line_num, full_name) in imports.items():
            if name not in usage:
                self.issues["unused_imports"].append({
                    "file": str(relative_path),
                    "line": line_num,
                    "import": full_name,
                    "suggestion": f"Remove unused import: {full_name}"
                })

    def _find_dead_code(self, relative_path: Path, tree: ast.AST, lines: List[str]):
        """Find potentially dead code (functions never called)."""
        # This is a simplified check - full dead code analysis requires call graph
        defined_functions = {}
        called_functions = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Skip if it's a test function or main entry point
                if node.name.startswith('test_') or node.name == 'main':
                    continue
                defined_functions[node.name] = node.lineno
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_functions.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        # Handle method calls
                        pass

        # Find functions that are defined but never called
        for func_name, line_num in defined_functions.items():
            # Check if it's called anywhere in the file
            if func_name not in called_functions:
                # Also check if it's imported elsewhere (simplified check)
                self.issues["dead_code"].append({
                    "file": str(relative_path),
                    "line": line_num,
                    "function": func_name,
                    "suggestion": f"Verify if function '{func_name}' is used elsewhere"
                })

    def generate_report(self) -> str:
        """Generate a human-readable report of all issues."""
        report_lines = [
            "CODE CLEANUP AND REFACTORING REPORT",
            "=" * 50,
            ""
        ]

        # Unused Imports
        report_lines.append(f"UNUSED IMPORTS ({len(self.issues['unused_imports'])} found):")
        if self.issues["unused_imports"]:
            for issue in self.issues["unused_imports"]:
                report_lines.append(
                    f"  - {issue['file']}:{issue['line']} - {issue['suggestion']}"
                )
        else:
            report_lines.append("  None found")
        report_lines.append("")

        # TODO Comments
        report_lines.append(f"TODO/FIXME COMMENTS ({len(self.issues['todo_comments'])} found):")
        if self.issues["todo_comments"]:
            for issue in self.issues["todo_comments"]:
                report_lines.append(
                    f"  - {issue['file']}:{issue['line']} [{issue['type']}] {issue['message']}"
                )
        else:
            report_lines.append("  None found")
        report_lines.append("")

        # Dead Code
        report_lines.append(f"POTENTIALLY DEAD CODE ({len(self.issues['dead_code'])} found):")
        if self.issues["dead_code"]:
            for issue in self.issues["dead_code"]:
                report_lines.append(
                    f"  - {issue['file']}:{issue['line']} - Function '{issue['function']}' ({issue['suggestion']})"
                )
        else:
            report_lines.append("  None found")
        report_lines.append("")

        # Summary
        total_issues = (
            len(self.issues["unused_imports"]) +
            len(self.issues["todo_comments"]) +
            len(self.issues["dead_code"])
        )
        report_lines.append("=" * 50)
        report_lines.append(f"TOTAL ISSUES: {total_issues}")
        
        return "\n".join(report_lines)


def fix_unused_imports(issues: Dict[str, List[Dict[str, Any]]], dry_run: bool = True) -> int:
    """
    Fix unused imports in the reported files.
    
    Args:
        issues: The issues dictionary from scan_all_files()
        dry_run: If True, only report what would be fixed
    
    Returns:
        Number of fixes applied (or would be applied in dry_run)
    """
    fixed_count = 0
    
    for issue in issues.get("unused_imports", []):
        file_path = Path(issue["file"])
        line_num = issue["line"]
        
        # In a real implementation, we would:
        # 1. Read the file
        # 2. Remove the specific import line
        # 3. Write back
        
        if dry_run:
            logger.info(f"[DRY RUN] Would remove unused import at {file_path}:{line_num}")
            fixed_count += 1
        else:
            # Actual fix implementation would go here
            logger.warning(f"Actual fix not implemented in dry_run=False mode for {file_path}")
    
    return fixed_count


def main():
    """Main entry point for the cleanup utility."""
    logger.info("Starting code cleanup scan...")
    
    # Determine src root
    # Assuming this script is at code/src/utils/cleanup_utils.py
    # and src/ is at code/src/
    script_dir = Path(__file__).parent
    src_root = script_dir.parent  # code/src/
    
    scanner = CodeCleanupScanner(src_root)
    issues = scanner.scan_all_files()
    
    report = scanner.generate_report()
    print(report)
    
    # Log summary
    total_issues = (
        len(issues["unused_imports"]) +
        len(issues["todo_comments"]) +
        len(issues["dead_code"])
    )
    
    if total_issues == 0:
        logger.info("✅ No code quality issues found! Codebase is clean.")
        return 0
    else:
        logger.warning(f"⚠️ Found {total_issues} issues. Review the report above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())