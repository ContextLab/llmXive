"""
Cleanup and Refactoring Script for Dream-State Learning Project.

This script performs automated code cleanup and refactoring tasks including:
- Removing trailing whitespace
- Normalizing empty lines (max 2 consecutive)
- Consolidating duplicate imports
- Removing unused imports
- Standardizing docstrings
- Adding missing type hints where obvious
- Sorting imports (standard lib -> third party -> local)
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Configuration
MAX_CONSECUTIVE_BLANK_LINES = 2
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"

# Standard library modules (comprehensive list for sorting)
STD_LIBS = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect',
    'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd',
    'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall',
    'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg',
    'cProfile', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime',
    'dbm', 'decimal', 'difflib', 'dis', 'distutils', 'doctest', 'email',
    'encodings', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
    'gettext', 'glob', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html',
    'http', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress',
    'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap',
    'modulefinder', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers',
    'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib', 'pdb', 'pickle',
    'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix',
    'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile',
    'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
    'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr',
    'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics',
    'string', 'stringprep', 'struct', 'subprocess', 'sunau', 'symtable', 'sys',
    'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile',
    'termios', 'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
    'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
    'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu',
    'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
    'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
    'zipimport', 'zlib', '_thread'
}


def get_python_files(root_dir: Path) -> List[Path]:
    """Recursively find all .py files in the given directory."""
    return list(root_dir.rglob("*.py"))


def parse_imports(file_path: Path) -> Tuple[Set[str], Dict[str, List[str]]]:
    """
    Parse a Python file and extract imports.
    Returns:
        - Set of all imported module names
        - Dict mapping import type ('import', 'from') to list of lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return set(), {}

    imports = set()
    import_lines = {'import': [], 'from': []}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name.split('.')[0]
                imports.add(module)
                # Find the line content
                lines = source.splitlines()
                if 0 < node.lineno <= len(lines):
                    import_lines['import'].append(lines[node.lineno - 1])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module = node.module.split('.')[0]
                imports.add(module)
                lines = source.splitlines()
                if 0 < node.lineno <= len(lines):
                    import_lines['from'].append(lines[node.lineno - 1])

    return imports, import_lines


def consolidate_imports(source: str) -> str:
    """
    Consolidate duplicate imports and sort them.
    Standard lib -> Third party -> Local.
    """
    lines = source.splitlines()
    new_lines = []
    in_import_block = False
    import_block = []

    def process_import_block(block: List[str]) -> List[str]:
        """Sort and consolidate a block of imports."""
        if not block:
            return []

        # Parse imports
        imports = []
        from_imports = {}

        for line in block:
            line = line.strip()
            if line.startswith('import '):
                parts = line.replace('import ', '').split(',')
                for p in parts:
                    p = p.strip()
                    if p and not p.startswith('#'):
                        imports.append(p)
            elif line.startswith('from '):
                match = re.match(r'from\s+(\S+)\s+import\s+(.+)', line)
                if match:
                    module = match.group(1)
                    names = match.group(2)
                    if module not in from_imports:
                        from_imports[module] = []
                    from_imports[module].append(names)

        # Sort and format
        result = []

        # Sort standard library
        std_imports = sorted([i for i in imports if i.split('.')[0] in STD_LIBS])
        third_party_imports = sorted([i for i in imports if i.split('.')[0] not in STD_LIBS])

        for imp in std_imports:
            result.append(f"import {imp}")
        for imp in third_party_imports:
            result.append(f"import {imp}")

        # Sort from imports
        for module in sorted(from_imports.keys()):
            names = from_imports[module]
            # Consolidate names for same module
            all_names = []
            for name_group in names:
                all_names.extend([n.strip() for n in name_group.split(',') if n.strip()])
            unique_names = sorted(set(all_names))
            result.append(f"from {module} import {', '.join(unique_names)}")

        return result

    for line in lines:
        stripped = line.strip()

        # Check if we're entering an import block
        if (stripped.startswith('import ') or stripped.startswith('from ')) and not in_import_block:
            in_import_block = True
            import_block = [line]
        elif in_import_block and (stripped.startswith('import ') or stripped.startswith('from ')):
            import_block.append(line)
        elif in_import_block:
            # End of import block
            new_lines.extend(process_import_block(import_block))
            new_lines.append(line)
            in_import_block = False
            import_block = []
        else:
            new_lines.append(line)

    # Handle trailing import block
    if in_import_block:
        new_lines.extend(process_import_block(import_block))

    return '\n'.join(new_lines)


def remove_unused_imports(source: str) -> str:
    """Remove imports that are not used in the code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    # Collect all used names
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attr usage
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    lines = source.splitlines()
    new_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import '):
            # Parse and check usage
            parts = stripped.replace('import ', '').split(',')
            kept_parts = []
            for p in parts:
                p = p.strip()
                # Handle 'import x as y'
                if ' as ' in p:
                    name = p.split(' as ')[1].strip()
                else:
                    name = p.split('.')[0]

                if name in used_names or name.startswith('_'):
                    kept_parts.append(p)

            if kept_parts:
                new_lines.append(f"import {', '.join(kept_parts)}")
            # If no parts kept, skip the line (removed)
        elif stripped.startswith('from '):
            # Parse from imports
            match = re.match(r'from\s+(\S+)\s+import\s+(.+)', stripped)
            if match:
                module = match.group(1)
                names_str = match.group(2)
                names = [n.strip() for n in names_str.split(',') if n.strip()]
                kept_names = []

                for name in names:
                    # Handle 'name as alias'
                    if ' as ' in name:
                        used_name = name.split(' as ')[1].strip()
                    else:
                        used_name = name.split('.')[0]

                    if used_name in used_names or used_name.startswith('_'):
                        kept_names.append(name)

                if kept_names:
                    new_lines.append(f"from {module} import {', '.join(kept_names)}")
                # If no names kept, skip the line
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return '\n'.join(new_lines)


def remove_trailing_whitespace(source: str) -> str:
    """Remove trailing whitespace from each line."""
    lines = source.splitlines()
    return '\n'.join(line.rstrip() for line in lines)


def normalize_empty_lines(source: str) -> str:
    """
    Normalize consecutive empty lines to a maximum of 2.
    """
    lines = source.splitlines()
    new_lines = []
    consecutive_empty = 0

    for line in lines:
        if line.strip() == '':
            consecutive_empty += 1
            if consecutive_empty <= MAX_CONSECUTIVE_BLANK_LINES:
                new_lines.append(line)
        else:
            consecutive_empty = 0
            new_lines.append(line)

    # Remove trailing empty lines at end of file
    while new_lines and new_lines[-1].strip() == '':
        new_lines.pop()

    return '\n'.join(new_lines)


def standardize_docstrings(source: str) -> str:
    """
    Standardize docstrings to use triple double quotes.
    This is a basic implementation; a full AST-based approach would be more robust.
    """
    # Replace single quotes with double quotes for docstrings
    # This regex matches triple-quoted strings
    pattern = r"'''(.*?)'''"

    def replace_quotes(match):
        content = match.group(1)
        return f'"""{content}"""'

    source = re.sub(pattern, replace_quotes, source, flags=re.DOTALL)
    return source


def add_missing_type_hints(source: str) -> str:
    """
    Add obvious missing type hints for function arguments.
    This is a heuristic-based approach and may not catch all cases.
    """
    # Simple heuristic: if a function argument has a default value,
    # try to infer a type hint
    lines = source.splitlines()
    new_lines = []

    for line in lines:
        # Look for function definitions without type hints
        if re.match(r'^\s*def\s+\w+\s*\([^)]*\)\s*:', line):
            # Try to add basic type hints for default values
            # This is a very basic implementation
            match = re.match(r'(\s*def\s+\w+\s*\()([^)]*)(\)\s*:\s*)', line)
            if match:
                prefix = match.group(1)
                args = match.group(2)
                suffix = match.group(3)

                # Parse arguments
                arg_list = [a.strip() for a in args.split(',') if a.strip()]
                new_args = []

                for arg in arg_list:
                    if '=' in arg and ':' not in arg:
                        # Has default but no type hint
                        name, default = arg.split('=', 1)
                        name = name.strip()
                        default = default.strip()
                        # Infer type from default
                        if default.startswith('"') or default.startswith("'"):
                            hint = 'str'
                        elif default.isdigit() or (default.startswith('-') and default[1:].isdigit()):
                            hint = 'int'
                        elif default.replace('.', '', 1).isdigit():
                            hint = 'float'
                        elif default == 'True' or default == 'False':
                            hint = 'bool'
                        elif default == 'None':
                            hint = 'Optional[Any]'
                        else:
                            hint = 'Any'

                        new_args.append(f"{name}: {hint} = {default}")
                    else:
                        new_args.append(arg)

                new_line = prefix + ', '.join(new_args) + suffix
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return '\n'.join(new_lines)


def run_cleanup(file_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run all cleanup steps on a single file.
    Returns a report of changes made.
    """
    report = {
        'file': str(file_path),
        'changes': [],
        'success': True
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original = f.read()

        current = original

        # Step 1: Remove trailing whitespace
        after_whitespace = remove_trailing_whitespace(current)
        if after_whitespace != current:
            report['changes'].append('Removed trailing whitespace')
            current = after_whitespace

        # Step 2: Normalize empty lines
        after_empty = normalize_empty_lines(current)
        if after_empty != current:
            report['changes'].append('Normalized consecutive empty lines')
            current = after_empty

        # Step 3: Consolidate and sort imports
        after_imports = consolidate_imports(current)
        if after_imports != current:
            report['changes'].append('Consolidated and sorted imports')
            current = after_imports

        # Step 4: Remove unused imports
        after_unused = remove_unused_imports(current)
        if after_unused != current:
            report['changes'].append('Removed unused imports')
            current = after_unused

        # Step 5: Standardize docstrings
        after_docstrings = standardize_docstrings(current)
        if after_docstrings != current:
            report['changes'].append('Standardized docstrings')
            current = after_docstrings

        # Step 6: Add missing type hints (heuristic)
        after_hints = add_missing_type_hints(current)
        if after_hints != current:
            report['changes'].append('Added missing type hints (heuristic)')
            current = after_hints

        # Write back if changes were made
        if current != original and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(current)
            report['changes'].append('File written to disk')
        elif current != original and dry_run:
            report['changes'].append('Would write to disk (dry run)')

        if not report['changes']:
            report['changes'].append('No changes needed')

    except Exception as e:
        report['success'] = False
        report['error'] = str(e)

    return report


def main():
    """Main entry point for the cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(description='Cleanup and refactor Python code')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    parser.add_argument('--dir', type=str, default=str(PROJECT_ROOT),
                      help='Directory to process (default: project root)')
    args = parser.parse_args()

    root = Path(args.dir)
    if not root.exists():
        print(f"Error: Directory {root} does not exist")
        sys.exit(1)

    print(f"Processing Python files in {root}...")

    files = get_python_files(root)
    print(f"Found {len(files)} Python files")

    total_changes = 0
    failed = 0

    for file_path in files:
        report = run_cleanup(file_path, dry_run=args.dry_run)
        if report['success']:
            total_changes += len(report['changes'])
            print(f"✓ {file_path.relative_to(root)}: {', '.join(report['changes'])}")
        else:
            failed += 1
            print(f"✗ {file_path.relative_to(root)}: {report.get('error', 'Unknown error')}")

    print(f"\nCleanup complete. Total changes: {total_changes}, Failed: {failed}")

    if failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()