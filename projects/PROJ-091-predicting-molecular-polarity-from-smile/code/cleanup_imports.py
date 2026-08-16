"""
Script to identify and remove unused imports from all Python scripts in the code/ directory.

This script scans all .py files in the code/ directory, parses them using the ast module,
identifies unused imports, removes them, and reports the changes.

Usage:
    python code/cleanup_imports.py
"""
import ast
import os
import sys
from pathlib import Path
from typing import List, Set, Tuple, Dict
import re

# Standard library modules that are commonly used
STANDARD_LIBS = {
    'os', 'sys', 'json', 'logging', 'pickle', 'gc', 'math', 'random', 'time',
    'datetime', 'collections', 'itertools', 'functools', 'pathlib', 'typing',
    'dataclasses', 'warnings', 'copy', 'hashlib', 'gzip', 'gzip', 'requests',
    'argparse', 'unittest', 'pytest', 're', 'string', 'io', 'tempfile',
    'shutil', 'subprocess', 'threading', 'multiprocessing', 'concurrent',
    'contextlib', 'abc', 'inspect', 'types', 'enum', 'numbers', 'statistics',
    'operator', 'array', 'bisect', 'heapq', 'queue', 'pprint', 'textwrap',
    'difflib', 'stringprep', 'readline', 'rlcompleter', 'struct', 'codecs',
    'unicodedata', 'string', 'locale', 'gettext', 'base64', 'binascii',
    'quopri', 'uu', 'html', 'xml', 'urllib', 'email', 'mailbox', 'mimetypes',
    'cgi', 'cgitb', 'wsgiref', 'ftplib', 'poplib', 'imaplib', 'nntplib',
    'smtplib', 'telnetlib', 'uuid', 'socket', 'ssl', 'select', 'selectors',
    'asyncio', 'signal', 'mmap', 'errno', 'ctypes', 'importlib', 'pkgutil',
    'modulefinder', 'runpy', 'code', 'codeop', 'compileall', 'py_compile',
    'distutils', 'ensurepip', 'venv', 'zipimport', 'zipfile', 'tarfile',
    'csv', 'configparser', 'netrc', 'xdrlib', 'plistlib', 'crypt', 'tty',
    'pty', 'fcntl', 'pipes', 'resource', 'grp', 'pwd', 'spwd', 'posix',
    'posixpath', 'ntpath', 'genericpath', 'fnmatch', 'glob', 'shlex',
    'getpass', 'curses', 'readline', 'rlcompleter', 'platform', 'sysconfig',
    'builtins', '__future__', 'atexit', 'traceback', 'linecache', 'tokenize',
    'token', 'keyword', 'symbol', 'parser', 'symtable', 'ast', 'dis',
    'pickletools', 'gc', 'weakref', 'final', 'contextvars', 'dataclasses',
    'graphlib', 'zoneinfo', 'calendar', 'timeit', 'trace', 'cProfile',
    'profile', 'pstats', 'time', 'datetime', 'zoneinfo', 'tzinfo'
}

def get_all_imports(tree: ast.AST) -> Dict[str, Set[str]]:
    """
    Extract all imports from an AST node.
    
    Returns a dictionary with keys:
    - 'names': set of imported names (e.g., 'os', 'sys', 'load_batch')
    - 'modules': set of imported modules (e.g., 'os', 'sys', 'pathlib')
    - 'aliases': dict mapping alias names to their full import path
    """
    imports = {
        'names': set(),
        'modules': set(),
        'aliases': {}
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                imports['modules'].add(module_name)
                if alias.asname:
                    imports['names'].add(alias.asname)
                    imports['aliases'][alias.asname] = alias.name
                else:
                    imports['names'].add(alias.name)
                    
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module:
                module_name = module.split('.')[0]
                imports['modules'].add(module_name)
            
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports['names'].add(name)
                if alias.asname:
                    imports['aliases'][alias.asname] = f"{module}.{alias.name}"
                else:
                    imports['aliases'][name] = f"{module}.{alias.name}"
                    
    return imports

def get_used_names(tree: ast.AST) -> Set[str]:
    """
    Extract all names used in the code (excluding import statements).
    """
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
                
    return used_names

def find_unused_imports(file_path: Path) -> List[Tuple[str, str]]:
    """
    Find unused imports in a Python file.
    
    Returns a list of tuples: (import_type, import_name)
    where import_type is 'module' or 'name'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Get all imports
        imports = get_all_imports(tree)
        
        # Get all used names
        used_names = get_used_names(tree)
        
        unused = []
        
        # Check module imports
        for module in imports['modules']:
            if module not in used_names and module not in STANDARD_LIBS:
                # Check if it's used as an alias
                if module not in imports['aliases']:
                    unused.append(('module', module))
        
        # Check specific names
        for name in imports['names']:
            if name not in used_names:
                # Check if it's a standard lib module used directly
                if name in STANDARD_LIBS and name not in imports['modules']:
                    continue
                unused.append(('name', name))
        
        return unused
        
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def remove_unused_imports(file_path: Path, unused_imports: List[Tuple[str, str]]) -> bool:
    """
    Remove unused imports from a Python file.
    
    Returns True if changes were made, False otherwise.
    """
    if not unused_imports:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Track which lines to remove
        lines_to_remove = set()
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for import statements
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Extract imported names
                if stripped.startswith('import '):
                    # Simple import: import os, sys, json
                    import_part = stripped[7:].split('#')[0].strip()
                    names = [n.strip() for n in import_part.split(',')]
                    for name in names:
                        # Remove alias if present
                        name = name.split(' as ')[0].strip()
                        if any(unused[1] == name for unused in unused_imports):
                            lines_to_remove.add(i)
                
                elif stripped.startswith('from '):
                    # From import: from os import path, walk
                    match = re.match(r'from\s+(\S+)\s+import\s+(.+)', stripped)
                    if match:
                        module = match.group(1)
                        names_str = match.group(2).split('#')[0].strip()
                        names = [n.strip() for n in names_str.split(',')]
                        
                        # Check each imported name
                        for name in names:
                            # Remove alias if present
                            clean_name = name.split(' as ')[0].strip()
                            if any(unused[1] == clean_name for unused in unused_imports):
                                lines_to_remove.add(i)
                                break
        
        if not lines_to_remove:
            return False
        
        # Remove lines in reverse order to maintain line numbers
        for i in sorted(lines_to_remove, reverse=True):
            lines.pop(i)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"Error modifying {file_path}: {e}")
        return False

def clean_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Clean a single file and return the number of unused imports found and their names.
    """
    unused = find_unused_imports(file_path)
    if unused:
        changed = remove_unused_imports(file_path, unused)
        if changed:
            return len(unused), [name for _, name in unused]
    return 0, []

def main():
    """
    Main function to clean up unused imports in all Python files in code/ directory.
    """
    code_dir = Path('code')
    
    if not code_dir.exists():
        print("Error: code/ directory not found")
        sys.exit(1)
    
    total_cleaned = 0
    files_processed = 0
    files_changed = 0
    
    print("Scanning for unused imports in code/ directory...")
    print("-" * 60)
    
    for py_file in code_dir.rglob('*.py'):
        # Skip test files and __pycache__
        if '__pycache__' in str(py_file) or py_file.name.startswith('test_'):
            continue
        
        files_processed += 1
        count, unused_names = clean_file(py_file)
        
        if count > 0:
            files_changed += 1
            total_cleaned += count
            print(f"Cleaned {py_file}:")
            for name in unused_names:
                print(f"  - Removed: {name}")
            print()
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  Files processed: {files_processed}")
    print(f"  Files changed: {files_changed}")
    print(f"  Total unused imports removed: {total_cleaned}")
    
    if files_changed > 0:
        print("\nCleanup complete! Please review the changes and run tests.")
    else:
        print("\nNo unused imports found. All files are clean.")

if __name__ == '__main__':
    main()