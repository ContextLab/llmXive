"""
Module to detect and remove unused imports from Python scripts in the analysis package.
"""
import ast
import os
import sys
from pathlib import Path
from typing import Set, List, Tuple

# Standard library imports that are commonly used implicitly or by the environment
# but might appear unused in strict AST analysis if not explicitly referenced in a way AST catches.
# However, for this task, we stick to strict AST analysis.
STANDARD_LIBRARY = {
    'os', 'sys', 'logging', 'time', 'json', 'hashlib', 'subprocess', 'gc',
    'pathlib', 'typing', 'datetime', 'collections', 'itertools', 'functools',
    'warnings', 'copy', 'math', 're', 'csv', 'gzip', 'shutil'
}

def get_unused_imports(file_path: Path) -> List[str]:
    """
    Analyze a Python file and return a list of unused import names.
    
    Args:
        file_path: Path to the Python file.
        
    Returns:
        List of unused import names (module names or specific imports).
    """
    if not file_path.exists():
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except (IOError, UnicodeDecodeError):
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # If syntax is invalid, we can't analyze, return empty to avoid crash
        return []

    imports: Set[str] = set()
    import_aliases: dict[str, str] = {}  # maps alias to original name

    # Collect imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.add(name)
                import_aliases[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module:
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    # For 'from X import Y', we track Y (or its alias)
                    imports.add(name)
                    import_aliases[name] = f"{module}.{alias.name}"

    # Collect all names used in the code (excluding imports themselves)
    used_names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    # Determine unused imports
    # Note: This is a simplified check. It doesn't handle dynamic imports,
    # or imports used only in type hints (if Python < 3.9 with string annotations).
    # It assumes standard usage patterns.
    unused: List[str] = []
    for imp in imports:
        if imp not in used_names:
            # Check if it's a standard library module that might be used for side effects
            # or if it's truly unused. For safety, we flag it.
            # We exclude 'sys' and 'os' if they are used in standard ways like sys.path, but
            # our used_names check should catch 'sys' if 'sys.path' is accessed.
            # However, if 'import sys' is present and 'sys' is not in used_names, it's unused.
            unused.append(imp)

    return unused

def remove_unused_imports_from_file(file_path: Path, dry_run: bool = True) -> Tuple[int, List[str]]:
    """
    Remove unused imports from a file.
    
    Args:
        file_path: Path to the Python file.
        dry_run: If True, do not modify the file, just return stats.
        
    Returns:
        Tuple of (number of imports removed, list of removed import lines/names)
    """
    if not file_path.exists():
        return 0, []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError):
        return 0, []

    try:
        tree = ast.parse("".join(lines))
    except SyntaxError:
        return 0, []

    imports_to_remove: Set[int] = set() # line numbers to remove
    import_details: List[str] = []

    # We need to map AST nodes to line numbers to remove the correct lines
    # This is tricky because 'ast.walk' doesn't preserve line order perfectly for removal.
    # Instead, we will re-parse and identify specific import statements.
    
    unused_names = get_unused_imports(file_path)
    if not unused_names:
        return 0, []

    # Re-scan lines to find import statements corresponding to unused names
    # This is a heuristic: we look for lines containing 'import <name>' or 'from ... import <name>'
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith('import ') and not stripped.startswith('from '):
            continue
        
        # Check if this line contains any of the unused names
        removed_from_this_line = []
        for name in unused_names:
            # Simple check: is the name in the line?
            # Be careful with 'import os' vs 'import os.path'
            # We look for word boundaries or end of string
            if f" {name}" in stripped or stripped.endswith(f" {name}") or stripped.startswith(f"import {name}") or stripped.startswith(f"from ... import {name}"):
                removed_from_this_line.append(name)
        
        if removed_from_this_line:
            imports_to_remove.add(i + 1) # 1-based line number
            import_details.extend([f"Line {i+1}: {', '.join(removed_from_this_line)}"])

    if dry_run:
        return len(import_details), import_details

    # If not dry run, actually remove the lines
    new_lines = [line for i, line in enumerate(lines) if (i + 1) not in imports_to_remove]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    return len(import_details), import_details

def main():
    """
    Main entry point to clean unused imports from all scripts in code/analysis/.
    """
    analysis_dir = Path("code/analysis")
    if not analysis_dir.exists():
        print(f"Error: Directory {analysis_dir} not found.")
        sys.exit(1)

    scripts = list(analysis_dir.glob("*.py"))
    if not scripts:
        print("No Python scripts found in code/analysis/")
        sys.exit(0)

    total_removed = 0
    files_modified = 0

    print(f"Scanning {len(scripts)} scripts for unused imports...")

    for script in scripts:
        # Skip __init__.py if it exists and has specific import patterns we want to keep
        if script.name == "__init__.py":
            continue

        count, details = remove_unused_imports_from_file(script, dry_run=False)
        if count > 0:
            files_modified += 1
            total_removed += count
            print(f"  {script.name}: removed {count} unused import(s)")
            for d in details:
                print(f"    - {d}")
        else:
            print(f"  {script.name}: no unused imports found")

    print(f"\nSummary: Modified {files_modified} files, removed {total_removed} unused imports.")

if __name__ == "__main__":
    main()
