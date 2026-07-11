"""
Validation module for code functions.

Validates syntax and imports of extracted functions.
"""

import ast
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any

from utils.logger import get_logger, log_stage_start, log_stage_complete, log_stage_error


def check_syntax(code: str) -> bool:
    """Check if code has valid Python syntax."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def mock_stdlib_imports(code: str) -> str:
    """Mock standard library imports to prevent actual imports during validation."""
    lines = code.split('\n')
    mocked_lines = []
    for line in lines:
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            mocked_lines.append(f"# MOCKED: {line.strip()}")
        else:
            mocked_lines.append(line)
    return '\n'.join(mocked_lines)


def count_external_imports(code: str) -> int:
    """Count non-stdlib imports in code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 999  # Invalid syntax, count as many to exclude
    
    external_count = 0
    stdlib_modules = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
        'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect',
        'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd',
        'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall',
        'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg',
        'cProfile', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime',
        'dbm', 'decimal', 'difflib', 'dis', 'distutils', 'doctest', 'email',
        'encodings', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
        'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
        'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac',
        'html', 'http', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io',
        'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache',
        'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math',
        'mimetypes', 'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
        'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib',
        'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib',
        'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats', 'pty', 'pwd',
        'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline',
        'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
        'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
        'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat',
        'statistics', 'string', 'stringprep', 'struct', 'subprocess', 'sunau',
        'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib',
        'tempfile', 'termios', 'test', 'textwrap', 'threading', 'time', 'timeit',
        'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty',
        'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib',
        'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
        'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
        'zipimport', 'zlib', '_thread'
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name.split('.')[0]
                if mod_name not in stdlib_modules:
                    external_count += 1
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod_name = node.module.split('.')[0]
                if mod_name not in stdlib_modules:
                    external_count += 1
    
    return external_count


def validate_function(code: str) -> Dict[str, Any]:
    """
    Validate a single function.
    
    Returns:
        Dictionary with validation result and reasons for exclusion
    """
    result = {
        "valid": True,
        "exclusion_reasons": []
    }
    
    if not check_syntax(code):
        result["valid"] = False
        result["exclusion_reasons"].append("syntax_error")
        return result
    
    external_imports = count_external_imports(code)
    if external_imports > 3:
        result["valid"] = False
        result["exclusion_reasons"].append(f"too_many_external_imports ({external_imports})")
    
    return result


def validate_parquet_file(input_path: str, output_path: str) -> Dict[str, int]:
    """Validate all functions in a JSONL file."""
    logger = get_logger("validate")
    total = 0
    valid = 0
    excluded = 0
    
    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            total += 1
            func = json.loads(line)
            code = func.get('code', '')
            
            validation = validate_function(code)
            
            if validation["valid"]:
                valid += 1
                outfile.write(json.dumps(func) + '\n')
            else:
                excluded += 1
                func['exclusion_reasons'] = validation["exclusion_reasons"]
                # Log exclusion for debugging
                logger.debug(f"Excluded function {func.get('name', 'unknown')}: {validation['exclusion_reasons']}")
    
    return {
        "total": total,
        "valid": valid,
        "excluded": excluded
    }

def run_validation(input_path: str, output_dir: str) -> Dict[str, int]:
    """Run validation on extracted functions."""
    logger = get_logger("validate")
    log_stage_start(logger, "validate", "Starting function validation")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    stats = validate_parquet_file(input_path, str(output_path / "validated_functions.jsonl"))
    
    log_stage_complete(logger, "validate", f"Validated {stats['valid']} functions, excluded {stats['excluded']}")
    
    return stats

def main():
    """Entry point for command-line execution."""
    if len(sys.argv) < 3:
        print("Usage: python -m data.validate <input_path> <output_dir>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        result = run_validation(input_path, output_dir)
        print(f"Validation complete: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"Validation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
