import ast
import os
import sys
from pathlib import Path
from typing import List, Set, Tuple, Dict
import re

def get_all_imports(tree: ast.AST) -> List[str]:
    """Extract all imported module names from an AST."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split('.')[0])
    return list(set(imports))

def get_used_names(tree: ast.AST) -> Set[str]:
    """Extract all names used in the code (excluding definitions)."""
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    return used_names

def find_unused_imports(file_path: str) -> List[str]:
    """Find imports that are not used in the file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    all_imports = get_all_imports(tree)
    used_names = get_used_names(tree)

    # Also consider names from __all__ if present
    all_export = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant):
                                all_export.add(elt.value)

    unused = []
    for imp in all_imports:
        # Check if the import name or any alias is used
        if imp not in used_names and imp not in all_export:
            unused.append(imp)

    return unused

def remove_unused_imports(file_path: str, unused_imports: List[str]) -> str:
    """Remove unused imports from the file content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines that follow an import removal
        if stripped == '' and skip_next:
            skip_next = False
            continue

        # Check if this line contains an unused import
        is_unused = False
        for imp in unused_imports:
            # Match 'import imp' or 'from imp import ...'
            if re.match(rf'^import\s+{re.escape(imp)}(\s*,|\s*$)', stripped):
                is_unused = True
                break
            if re.match(rf'^from\s+{re.escape(imp)}\s+import', stripped):
                is_unused = True
                break

        if not is_unused:
            new_lines.append(line)
        else:
            skip_next = True

    return ''.join(new_lines)

def clean_file(file_path: str) -> bool:
    """Clean a single file by removing unused imports."""
    unused = find_unused_imports(file_path)
    if not unused:
        return False

    cleaned_content = remove_unused_imports(file_path, unused)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    return True

def get_all_python_files(root_dir: str) -> List[str]:
    """Recursively find all Python files in a directory."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main entry point for the cleanup script."""
    root_dir = 'code'
    if not os.path.exists(root_dir):
        print(f"Error: Directory '{root_dir}' not found.")
        sys.exit(1)

    py_files = get_all_python_files(root_dir)
    cleaned_count = 0

    for file_path in py_files:
        if clean_file(file_path):
            print(f"Cleaned: {file_path}")
            cleaned_count += 1
        else:
            print(f"No changes: {file_path}")

    print(f"\nTotal files cleaned: {cleaned_count}")

if __name__ == '__main__':
    main()
