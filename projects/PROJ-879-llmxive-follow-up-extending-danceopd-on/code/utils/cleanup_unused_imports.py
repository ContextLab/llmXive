"""
Script to detect and remove unused imports from all Python modules in the code/ directory.
This implements T035b: Remove dead code and unused imports.

Usage:
    python code/utils/cleanup_unused_imports.py --dry-run
    python code/utils/cleanup_unused_imports.py --fix
"""
import ast
import os
import sys
import argparse
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
import re


class ImportUsageVisitor(ast.NodeVisitor):
    """AST visitor that tracks used names in a module."""

    def __init__(self):
        self.used_names: Set[str] = set()
        self.imported_names: Dict[str, Tuple[str, str]] = {}  # name -> (import_type, original_name)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Track attribute access like `module.submodule.func`
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            parts.reverse()
            # The base name is the first part
            self.used_names.add(parts[0])
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            # For `import a.b.c`, we track 'a' as the used name
            base_name = name.split('.')[0]
            self.imported_names[base_name] = ('import', alias.name)
            # Also track the full name if it's used with aliases
            if alias.asname:
                self.imported_names[alias.asname] = ('import', alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ''
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imported_names[name] = ('from', module)
        self.generic_visit(node)


def get_imports_and_usage(file_path: Path) -> Tuple[Dict[str, Tuple[str, str]], Set[str]]:
    """Parse a Python file and return imports and used names."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return {}, set()
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return {}, set()

    visitor = ImportUsageVisitor()
    visitor.visit(tree)
    return visitor.imported_names, visitor.used_names


def remove_unused_imports(file_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Remove unused imports from a Python file.
    Returns (number_of_removed_imports, list_of_removed_import_names).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        source = ''.join(lines)
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, []

    imports, used_names = get_imports_and_usage(file_path)
    
    if not imports:
        return 0, []

    # Identify unused imports
    unused_imports = []
    for name, (import_type, original) in imports.items():
        if name not in used_names:
            unused_imports.append((name, import_type, original))

    if not unused_imports:
        return 0, []

    # Build regex patterns to remove unused import lines
    removed_count = 0
    removed_names = []
    new_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        is_import_line = (
            line_stripped.startswith('import ') or 
            line_stripped.startswith('from ') or
            line_stripped.startswith('#') and ('import' in line_stripped.lower())
        )
        
        if not is_import_line:
            new_lines.append(line)
            continue

        # Check if this line contains any unused imports
        should_remove_line = False
        line_imports = []
        
        if line_stripped.startswith('import '):
            # Handle: import a, b, c
            imports_part = line_stripped[7:].split('#')[0].strip()
            if imports_part:
                for item in imports_part.split(','):
                    item = item.strip()
                    base = item.split('.')[0].split(' as ')[0].strip()
                    line_imports.append(base)
                    
        elif line_stripped.startswith('from '):
            # Handle: from module import a, b, c
            match = re.match(r'from\s+(\S+)\s+import\s+(.+)', line_stripped)
            if match:
                module = match.group(1)
                imports_part = match.group(2).split('#')[0].strip()
                for item in imports_part.split(','):
                    item = item.strip()
                    name = item.split(' as ')[0].strip()
                    line_imports.append(name)

        # Check if any import in this line is unused
        imports_to_keep = []
        for imp in line_imports:
            if imp in [u[0] for u in unused_imports]:
                removed_names.append(imp)
                removed_count += 1
            else:
                imports_to_keep.append(imp)

        if len(imports_to_keep) == 0 and len(line_imports) > 0:
            # Remove the entire line
            should_remove_line = True
        elif len(imports_to_keep) < len(line_imports):
            # Modify the line to keep only used imports
            if line_stripped.startswith('import '):
                new_imports = ', '.join(imports_to_keep)
                # Preserve comments and indentation
                indent = line[:len(line) - len(line.lstrip())]
                comment = ''
                if '#' in line:
                    comment = line.split('#', 1)[1]
                new_line = f"{indent}import {new_imports}{comment}\n"
                new_lines.append(new_line)
                should_remove_line = False
            elif line_stripped.startswith('from '):
                match = re.match(r'(from\s+\S+\s+import\s+)(.+)', line_stripped)
                if match:
                    prefix = match.group(1)
                    comment = ''
                    if '#' in line:
                        comment = line.split('#', 1)[1]
                    indent = line[:len(line) - len(line.lstrip())]
                    new_imports = ', '.join(imports_to_keep)
                    new_line = f"{indent}{prefix}{new_imports}{comment}\n"
                    new_lines.append(new_line)
                    should_remove_line = False

        if not should_remove_line:
            new_lines.append(line)

    if not dry_run and removed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return removed_count, removed_names


def scan_code_directory(code_dir: Path, dry_run: bool = False) -> Dict[str, Tuple[int, List[str]]]:
    """Scan all Python files in the code directory and remove unused imports."""
    results = {}
    
    for py_file in code_dir.rglob('*.py'):
        if py_file.name.startswith('_') and 'test' not in str(py_file):
            # Skip private modules and test files
            continue
        
        removed_count, removed_names = remove_unused_imports(py_file, dry_run)
        if removed_count > 0:
            results[str(py_file.relative_to(code_dir))] = (removed_count, removed_names)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Remove unused imports from Python files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without making changes')
    parser.add_argument('--fix', action='store_true', help='Actually remove unused imports')
    parser.add_argument('--code-dir', type=str, default='code', help='Path to the code directory')
    
    args = parser.parse_args()
    
    code_dir = Path(args.code_dir)
    if not code_dir.exists():
        print(f"Error: Code directory '{code_dir}' does not exist")
        sys.exit(1)

    if not args.fix and not args.dry_run:
        print("Please specify --dry-run or --fix")
        sys.exit(1)

    mode = "DRY RUN" if args.dry_run else "FIX"
    print(f"Starting {mode} for unused imports in {code_dir}/")
    print("-" * 50)

    results = scan_code_directory(code_dir, dry_run=args.dry_run)

    if not results:
        print("No unused imports found.")
        return

    total_removed = 0
    for file_path, (count, names) in results.items():
        total_removed += count
        action = "Would remove" if args.dry_run else "Removed"
        print(f"{action} {count} unused import(s) from {file_path}:")
        for name in names:
            print(f"  - {name}")
        print()

    print("-" * 50)
    print(f"Total unused imports {action.lower()}: {total_removed}")
    
    if args.dry_run:
        print("\nRun with --fix to actually remove these imports.")


if __name__ == '__main__':
    main()
