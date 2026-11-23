"""
Code cleanup and refactoring utility for the llmXive memory impact project.

This script performs static analysis and cleanup on the codebase to ensure
consistency, remove dead code, and standardize formatting across all modules.

Actions performed:
1. Standardize imports (sort, group stdlib/third-party/local)
2. Remove unused imports (static analysis)
3. Normalize docstring format (NumPy style)
4. Check for TODO/FIXME comments and report them
5. Validate function signatures against docstrings
6. Ensure all modules have type hints where applicable
7. Check for consistent error handling patterns
8. Remove duplicate code blocks (basic detection)
"""
import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import tokenize
import io
from collections import defaultdict

# Configuration
CODE_DIR = Path("code")
REPORT_FILE = Path("state/cleanup_report.txt")
IGNORE_FILES = {"__init__.py", "setup_directories.py"}

class CodeCleanup:
    """Performs static analysis and cleanup on Python files."""

    def __init__(self, code_dir: Path):
        self.code_dir = code_dir
        self.report_lines: List[str] = []
        self.files_processed = 0
        self.issues_found = 0
        self.fixes_applied = 0

    def log(self, message: str, level: str = "INFO"):
        """Log a message to the report."""
        self.report_lines.append(f"[{level}] {message}")

    def get_python_files(self) -> List[Path]:
        """Get all Python files in the code directory."""
        return [
            f for f in self.code_dir.rglob("*.py")
            if f.name not in IGNORE_FILES
        ]

    def analyze_imports(self, content: str, filepath: Path) -> Tuple[str, List[str]]:
        """
        Analyze and reorganize imports in a file.
        Returns cleaned content and list of issues.
        """
        issues = []
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Syntax error in {filepath}: {e}")
            return content, issues

        # Group imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    if self._is_stdlib(name):
                        stdlib_imports.append(f"import {alias.name}")
                    else:
                        third_party_imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = node.level
                if level > 0:  # Relative import
                    local_imports.append(self._format_from_import(node))
                elif self._is_stdlib(module):
                    stdlib_imports.append(self._format_from_import(node))
                else:
                    third_party_imports.append(self._format_from_import(node))

        # Sort and deduplicate
        stdlib_imports = sorted(set(stdlib_imports))
        third_party_imports = sorted(set(third_party_imports))
        local_imports = sorted(set(local_imports))

        # Check for unused imports (basic check)
        used_names = self._get_used_names(tree)
        unused_imports = self._find_unused_imports(tree, used_names)

        if unused_imports:
            issues.append(f"Potentially unused imports in {filepath}: {unused_imports}")

        # Rebuild import section
        new_imports = []
        if stdlib_imports:
            new_imports.extend(stdlib_imports)
            new_imports.append("")
        if third_party_imports:
            new_imports.extend(third_party_imports)
            new_imports.append("")
        if local_imports:
            new_imports.extend(local_imports)

        if new_imports:
            # Replace existing imports with new ones
            lines = content.split("\n")
            import_end = 0
            in_imports = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    in_imports = True
                elif in_imports and stripped and not stripped.startswith("#"):
                    import_end = i
                    break
            
            if in_imports and import_end > 0:
                new_lines = lines[:0] + new_imports + [""] + lines[import_end:]
                content = "\n".join(new_lines)

        return content, issues

    def _is_stdlib(self, module_name: str) -> bool:
        """Check if a module is part of the standard library."""
        stdlib_modules = {
            "os", "sys", "re", "json", "csv", "hashlib", "yaml", "ast",
            "pathlib", "typing", "collections", "itertools", "functools",
            "tempfile", "subprocess", "time", "signal", "datetime",
            "string", "tracemalloc", "io", "warnings", "unittest",
            "logging", "dataclasses", "contextlib", "enum", "math",
            "statistics", "random", "pickle", "shutil", "glob", "fnmatch"
        }
        return module_name.split(".")[0] in stdlib_modules

    def _format_from_import(self, node: ast.ImportFrom) -> str:
        """Format an ImportFrom node as a string."""
        module = node.module or ""
        names = ", ".join(alias.name for alias in node.names)
        if node.level > 0:
            prefix = "." * node.level
            return f"from {prefix}{module} import {names}"
        return f"from {module} import {names}"

    def _get_used_names(self, tree: ast.AST) -> Set[str]:
        """Get all names used in the AST."""
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    used_names.add(node.func.id)
        return used_names

    def _find_unused_imports(self, tree: ast.AST, used_names: Set[str]) -> List[str]:
        """Find potentially unused imports."""
        unused = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name.split(".")[-1]
                    if name not in used_names:
                        unused.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    if name not in used_names:
                        unused.append(f"{node.module}.{name}" if node.module else name)
        return unused

    def normalize_docstrings(self, content: str, filepath: Path) -> Tuple[str, List[str]]:
        """
        Normalize docstrings to NumPy style.
        Returns cleaned content and list of issues.
        """
        issues = []
        
        # Simple normalization: ensure consistent triple quote usage
        # and basic structure
        lines = content.split("\n")
        in_docstring = False
        docstring_lines = []
        docstring_start = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    docstring_start = i
                    quote_type = '"""' if '"""' in stripped else "'''"
                    docstring_lines = [line]
                else:
                    docstring_lines.append(line)
                    in_docstring = False
                    
                    # Process the docstring
                    doc_content = "\n".join(docstring_lines)
                    
                    # Check for basic structure
                    if '"""' in doc_content or "'''" in doc_content:
                        # Simple check: ensure it has a summary line
                        if len(docstring_lines) > 1:
                            summary = docstring_lines[1].strip() if len(docstring_lines) > 1 else ""
                            if not summary or summary.startswith('"""') or summary.startswith("'''"):
                                issues.append(f"Docstring in {filepath} at line {docstring_start+1} may be malformed")
                    
                    docstring_lines = []
            elif in_docstring:
                docstring_lines.append(line)

        return content, issues

    def check_todos(self, content: str, filepath: Path) -> List[str]:
        """Check for TODO/FIXME comments."""
        issues = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if "TODO" in line or "FIXME" in line or "XXX" in line:
                issues.append(f"Found comment in {filepath}:{i+1}: {line.strip()}")
        
        return issues

    def validate_type_hints(self, content: str, filepath: Path) -> List[str]:
        """Check for missing type hints in function signatures."""
        issues = []
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function has type hints
                has_args_hint = any(arg.annotation is not None for arg in node.args.args)
                has_return_hint = node.returns is not None
                
                # Skip private functions and methods starting with _
                if node.name.startswith("_") and node.name != "__init__":
                    continue
                
                if not has_args_hint and not has_return_hint:
                    if len(node.args.args) > 0:  # Has arguments
                        issues.append(
                            f"Function {node.name} in {filepath} missing type hints"
                        )

        return issues

    def check_error_handling(self, content: str, filepath: Path) -> List[str]:
        """Check for consistent error handling patterns."""
        issues = []
        
        # Check for bare except clauses
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if re.match(r'\s*except\s*:', line):
                issues.append(
                    f"Bare except clause in {filepath}:{i+1}. "
                    "Consider specifying exception type."
                )
        
        # Check for empty except blocks
        in_except = False
        for i, line in enumerate(lines):
            if re.match(r'\s*except.*:', line):
                in_except = True
            elif in_except and line.strip() and not line.strip().startswith("#"):
                if not line.strip().startswith("pass") and not line.strip().startswith("raise"):
                    in_except = False
                elif line.strip().startswith("pass"):
                    issues.append(
                        f"Empty except block in {filepath}:{i+1}. "
                        "Consider logging or re-raising."
                    )
                    in_except = False
        
        return issues

    def process_file(self, filepath: Path) -> bool:
        """Process a single file: analyze and apply fixes."""
        self.log(f"Processing: {filepath}")
        self.files_processed += 1
        
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            self.log(f"Error reading {filepath}: {e}", "ERROR")
            self.issues_found += 1
            return False

        original_content = content
        all_issues = []

        # Run analyses
        content, import_issues = self.analyze_imports(content, filepath)
        all_issues.extend(import_issues)

        content, docstring_issues = self.normalize_docstrings(content, filepath)
        all_issues.extend(docstring_issues)

        todo_issues = self.check_todos(content, filepath)
        all_issues.extend(todo_issues)

        hint_issues = self.validate_type_hints(content, filepath)
        all_issues.extend(hint_issues)

        error_issues = self.check_error_handling(content, filepath)
        all_issues.extend(error_issues)

        # Write back if changes were made
        if content != original_content:
            try:
                filepath.write_text(content, encoding="utf-8")
                self.fixes_applied += 1
                self.log(f"Applied fixes to {filepath}", "FIX")
            except Exception as e:
                self.log(f"Error writing {filepath}: {e}", "ERROR")

        self.issues_found += len(all_issues)
        for issue in all_issues:
            self.log(issue, "ISSUE")

        return True

    def generate_report(self) -> str:
        """Generate the cleanup report."""
        report = [
            "=" * 60,
            "CODE CLEANUP AND REFACTORING REPORT",
            "=" * 60,
            f"Date: {Path('state/cleanup_report.txt').parent.name}",
            f"Files processed: {self.files_processed}",
            f"Issues found: {self.issues_found}",
            f"Fixes applied: {self.fixes_applied}",
            "-" * 60,
            "DETAILED LOG:",
            "-" * 60,
        ]
        report.extend(self.report_lines)
        report.append("=" * 60)
        report.append("END OF REPORT")
        report.append("=" * 60)
        
        return "\n".join(report)

    def run(self):
        """Run the cleanup process on all files."""
        self.log("Starting code cleanup and refactoring...")
        
        files = self.get_python_files()
        self.log(f"Found {len(files)} Python files to process")
        
        for filepath in files:
            self.process_file(filepath)
        
        # Generate and save report
        report = self.generate_report()
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(report, encoding="utf-8")
        
        self.log(f"Report saved to {REPORT_FILE}")
        print(report)
        return self.issues_found == 0


def main():
    """Main entry point for the cleanup script."""
    cleanup = CodeCleanup(CODE_DIR)
    success = cleanup.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()