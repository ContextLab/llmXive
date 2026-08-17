"""
Utility module to scan Python files and remove unused imports.
Implements a simple AST-based visitor to detect unused imports.
"""

import ast
import os
import sys
import argparse
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional


class ImportUsageVisitor(ast.NodeVisitor):
    """AST visitor to track imported names and their usage."""

    def __init__(self):
        self.imports: Dict[str, str] = {}  # alias -> original_name
        self.names: Dict[str, str] = {}    # name -> source (import or assign)
        self.used_names: Set[str] = set()
        self.import_nodes: List[ast.Import | ast.ImportFrom] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = alias.name
            self.names[name] = f"import {alias.name}"
            self.import_nodes.append(node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = f"{module}.{alias.name}"
            self.names[name] = f"import {module}.{alias.name}"
            self.import_nodes.append(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Record function definitions as used names
        self.used_names.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Record class definitions as used names
        self.used_names.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.used_names.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.names[target.id] = f"assign {target.id}"
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.names[node.target.id] = f"assign {node.target.id}"
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        if isinstance(node.target, ast.Name):
            self.names[node.target.id] = f"loop {node.target.id}"
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self.names[item.optional_vars.id] = f"with {item.optional_vars.id}"
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if node.name:
            self.names[node.name] = f"except {node.name}"
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension):
        if isinstance(node.target, ast.Name):
            self.names[node.target.id] = f"comprehension {node.target.id}"
        self.generic_visit(node)


def get_imports_and_usage(file_path: Path) -> Tuple[List[str], Set[str], Dict[str, str]]:
    """
    Parse a Python file and return:
    - List of import lines (for removal)
    - Set of used names
    - Dict mapping alias to full import path
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return [], set(), {}

    visitor = ImportUsageVisitor()
    visitor.visit(tree)

    # Get all top-level names defined in the file (functions, classes, variables)
    # These are implicitly "used" by the file itself
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined_names.add(node.target.id)

    # Merge defined names into used names (they are valid in the file context)
    used_names = visitor.used_names | defined_names

    # Identify unused imports
    unused_imports = []
    for alias, full_import in visitor.imports.items():
        if alias not in used_names:
            unused_imports.append(alias)

    return unused_imports, visitor.used_names, visitor.imports


def remove_unused_imports(file_path: Path) -> bool:
    """
    Remove unused imports from a Python file.
    Returns True if changes were made, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    try:
        tree = ast.parse("".join(lines), filename=str(file_path))
    except SyntaxError:
        return False

    visitor = ImportUsageVisitor()
    visitor.visit(tree)

    # Collect all names that are used or defined
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined_names.add(node.target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                visitor.imports[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                visitor.imports[name] = f"{module}.{alias.name}"

    used_names = visitor.used_names | defined_names

    # Identify lines to remove
    lines_to_remove = set()
    for node in visitor.import_nodes:
        start_line = node.lineno - 1  # 0-indexed
        end_line = node.end_lineno  # exclusive, 1-indexed in AST, so 0-indexed is end_lineno
        if end_line is None:
            end_line = start_line + 1

        # Check if any import in this node is unused
        imports_in_node = []
        if isinstance(node, ast.Import):
            imports_in_node = [alias.asname if alias.asname else alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports_in_node = [
                alias.asname if alias.asname else f"{module}.{alias.name}"
                for alias in node.names
            ]

        has_unused = False
        for imp in imports_in_node:
            # For ImportFrom, the alias is the name used, but the full path is in visitor.imports
            # We check if the alias (or the full path key) is unused
            key = imp.split(".")[-1] if "." in imp else imp
            if key not in used_names:
                has_unused = True
                break

        if has_unused:
            for i in range(start_line, end_line):
                lines_to_remove.add(i)

    if not lines_to_remove:
        return False

    # Remove lines in reverse order to preserve indices
    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True


def scan_code_directory(directory: Path) -> List[Path]:
    """Scan a directory for Python files."""
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(Path(root) / file)
    return py_files


def main():
    parser = argparse.ArgumentParser(
        description="Remove unused imports from Python files in a directory."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing Python files to clean.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making changes.",
    )
    args = parser.parse_args()

    if not args.directory.is_dir():
        print(f"Error: {args.directory} is not a directory.")
        sys.exit(1)

    py_files = scan_code_directory(args.directory)
    print(f"Found {len(py_files)} Python files.")

    cleaned_count = 0
    for file_path in py_files:
        if args.dry_run:
            unused, _, _ = get_imports_and_usage(file_path)
            if unused:
                print(f"[DRY RUN] Would clean unused imports in {file_path}: {unused}")
                cleaned_count += 1
        else:
            if remove_unused_imports(file_path):
                print(f"Cleaned unused imports in {file_path}")
                cleaned_count += 1

    if args.dry_run:
        print(f"Would clean {cleaned_count} files.")
    else:
        print(f"Cleaned {cleaned_count} files.")


if __name__ == "__main__":
    main()
