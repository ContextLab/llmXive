import ast
import os
import sys
from pathlib import Path
from typing import Set, List, Tuple

def get_unused_imports(file_path: Path) -> List[str]:
    """
    Parse a Python file and identify unused imports.
    Returns a list of unused import names.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            print(f"Syntax error in {file_path}, skipping.")
            return []

    imports = {}
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[0]
                imports[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if name != '*':
                    imports[name] = f"{node.module}.{name}"
        elif isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attr usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    unused = [name for name in imports if name not in used_names]
    return unused

def remove_unused_imports_from_file(file_path: Path) -> Tuple[bool, str]:
    """
    Remove unused imports from a file.
    Returns (success, message).
    """
    unused = get_unused_imports(file_path)
    if not unused:
        return True, "No unused imports found."

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip_next = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            # Check if this line contains any unused import
            is_unused_line = False
            for u in unused:
                if u in stripped:
                    is_unused_line = True
                    break
            if is_unused_line:
                continue
        new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return True, f"Removed unused imports: {unused}"

def main():
    """Main entry point to clean all scripts in code/analysis/."""
    analysis_dir = Path('code/analysis')
    if not analysis_dir.exists():
        print(f"Directory {analysis_dir} not found.")
        sys.exit(1)

    for py_file in analysis_dir.glob('*.py'):
        if py_file.name == '__init__.py':
            continue
        success, msg = remove_unused_imports_from_file(py_file)
        print(f"{py_file.name}: {msg}")

    print("Cleanup complete.")

if __name__ == '__main__':
    main()
