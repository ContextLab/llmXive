"""
Security hardening module to ensure no external API calls are made during synthetic data generation and execution.

This module provides:
1. A network isolation context manager that blocks outbound connections.
2. Validation logic to ensure no external dependencies are imported at runtime.
3. Audit logging for security violations.
"""
import os
import socket
import threading
import logging
from functools import wraps
from typing import Callable, Any, Optional
from pathlib import Path

# Configure logging for security events
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Add a handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[SECURITY] %(levelname)s: %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Global flag to track network isolation state
_isolation_active = threading.local()
_isolation_active.enabled = False

# Whitelist of allowed external modules that do not make network calls
ALLOWED_MODULES = {
    'json', 'os', 'sys', 'random', 'pathlib', 'typing', 'collections',
    'numpy', 'pandas', 'scipy', 'statsmodels', 'pytest', 'yaml',
    'tiktoken', 'argparse', 'hashlib', 'datetime', 'warnings', 'csv',
    'itertools', 'math', 'statistics', 'copy', 're', 'string', 'time',
    'uuid', 'base64', 'pickle', 'shutil', 'glob', 'fnmatch', 'tempfile',
    'io', 'struct', 'array', 'bisect', 'heapq', 'queue', 'weakref',
    'abc', 'contextlib', 'dataclasses', 'enum', 'graphlib', 'types',
    'inspect', 'dis', 'ast', 'codecs', 'locale', 'gettext', 'textwrap',
    'difflib', 'pprint', 'reprlib', 'numbers', 'cmath', 'decimal',
    'fractions', 'random', 'secrets', 'hashlib', 'hmac', 'ssl', 'ssl',
    'select', 'selectors', 'asyncio', 'concurrent', 'multiprocessing',
    'threading', 'signal', 'mmap', 'ctypes', 'subprocess', 'pipes',
    'shlex', 'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma', 'zlib',
    'zipimport', 'pkgutil', 'modulefinder', 'runpy', 'importlib',
    'builtins', '__future__', 'token', 'tokenize', 'keyword', 'tabnanny',
    'py_compile', 'compileall', 'formatter', 'pdb', 'profile', 'timeit',
    'trace', 'tracemalloc', 'unittest', 'doctest', 'venv', 'distutils',
    'ensurepip', 'netrc', 'nis', 'xdrlib', 'plistlib', 'crypt', 'spwd',
    'grp', 'pwd', 'termios', 'tty', 'pty', 'fcntl', 'pipes', 'resource',
    'syslog', 'aifc', 'sunau', 'wave', 'chunk', 'colorsys', 'imghdr',
    'sndhdr', 'ossaudiodev', 'turtle', 'curses', 'tkinter', 'idlelib',
    'test', 'zoneinfo'
}

# Blocked modules that typically make network calls
BLOCKED_MODULES = {
    'requests', 'urllib3', 'http.client', 'urllib.request', 'urllib.parse',
    'urllib.error', 'urllib.robotparser', 'ftplib', 'poplib', 'imaplib',
    'nntplib', 'smtplib', 'telnetlib', 'socketserver', 'xmlrpc',
    'ipaddress', 'email', 'mailbox', 'mimetypes', 'html', 'xml',
    'webbrowser', 'cgi', 'cgitb', 'wsgiref', 'http', 'urllib', 'asyncio',
    'twisted', 'aiohttp', 'httpx', 'httplib2', 'pycurl', 'paramiko',
    'fabric', 'scrapy', 'selenium', 'playwright', 'pyppeteer'
}

def _check_module_import(module_name: str) -> None:
    """
    Check if a module import is allowed.
    
    Args:
        module_name: Name of the module being imported.
        
    Raises:
        SecurityViolationError: If the module is blocked.
    """
    if _isolation_active.enabled:
        # Check if module is in blocked list
        if any(blocked in module_name for blocked in BLOCKED_MODULES):
            raise SecurityViolationError(
                f"Network isolation active: Import of '{module_name}' is blocked "
                "as it may make external API calls."
            )
        
        # Log warning for non-whitelisted modules
        if module_name not in ALLOWED_MODULES:
            logger.warning(
                f"Network isolation active: Import of '{module_name}' is not in "
                "the allowed list. This may be safe, but please verify."
            )

def _socket_connect_wrapper(*args, **kwargs):
    """Wrapper to block socket connections when isolation is active."""
    if _isolation_active.enabled:
        raise SecurityViolationError(
            "Network isolation active: Socket connections are blocked to prevent "
            "external API calls."
        )
    # Call original socket.connect
    return socket.socket.connect(*args, **kwargs)

class SecurityViolationError(Exception):
    """Exception raised when a security policy is violated."""
    pass

class NetworkIsolationContext:
    """
    Context manager that enforces network isolation.
    
    When active, this context:
    1. Blocks socket connections
    2. Validates module imports
    3. Logs security violations
    
    Usage:
        with NetworkIsolationContext():
            # Code here cannot make network calls
            from generators.synthetic_workflow import SyntheticWorkflowGenerator
            generator = SyntheticWorkflowGenerator(seed=42)
            workflows = generator.generate(num_workflows=10)
    """
    
    def __enter__(self):
        # Store original socket.connect
        self._original_socket_connect = socket.socket.connect
        
        # Enable isolation flag
        _isolation_active.enabled = True
        
        # Patch socket.connect to block connections
        socket.socket.connect = _socket_connect_wrapper
        
        # Patch import system to check modules
        self._original_import = __builtins__.__import__
        
        def _safe_import(name, *args, **kwargs):
            _check_module_import(name)
            return self._original_import(name, *args, **kwargs)
        
        __builtins__.__import__ = _safe_import
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original socket.connect
        socket.socket.connect = self._original_socket_connect
        
        # Restore original import
        __builtins__.__import__ = self._original_import
        
        # Disable isolation flag
        _isolation_active.enabled = False
        
        # Log exit
        logger.info("Network isolation context exited.")
        
        return False  # Don't suppress exceptions

def ensure_no_network_access(func: Callable) -> Callable:
    """
    Decorator to ensure a function runs in network-isolated mode.
    
    Usage:
        @ensure_no_network_access
        def generate_synthetic_data():
            # This function cannot make network calls
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with NetworkIsolationContext():
            return func(*args, **kwargs)
    return wrapper

def validate_no_external_calls(module_path: Path) -> bool:
    """
    Static analysis to check if a module file contains potential external calls.
    
    Args:
        module_path: Path to the Python module file.
        
    Returns:
        True if no external calls detected, False otherwise.
    """
    if not module_path.exists():
        logger.warning(f"Module not found: {module_path}")
        return False
    
    content = module_path.read_text()
    
    # Check for common patterns of external calls
    dangerous_patterns = [
        'requests.', 'urllib.request.', 'http.client.', 'socket.',
        'urllib3.', 'aiohttp.', 'httpx.', 'twisted.', 'selenium.',
        'webbrowser.open', 'subprocess.Popen', 'subprocess.call'
    ]
    
    found_issues = []
    for pattern in dangerous_patterns:
        if pattern in content:
            found_issues.append(pattern)
    
    if found_issues:
        logger.error(
            f"Potential external calls found in {module_path}: {found_issues}"
        )
        return False
    
    logger.info(f"No external calls detected in {module_path}")
    return True

def audit_all_modules(project_root: Path) -> dict:
    """
    Audit all Python modules in the project for potential external calls.
    
    Args:
        project_root: Root directory of the project.
        
    Returns:
        Dictionary with audit results.
    """
    results = {
        'audited_files': [],
        'safe_files': [],
        'unsafe_files': [],
        'errors': []
    }
    
    # Find all Python files
    python_files = list(project_root.rglob('*.py'))
    
    for py_file in python_files:
        # Skip test files and setup scripts
        if 'test' in str(py_file) or 'setup' in str(py_file):
            continue
        
        results['audited_files'].append(str(py_file))
        
        try:
            if validate_no_external_calls(py_file):
                results['safe_files'].append(str(py_file))
            else:
                results['unsafe_files'].append(str(py_file))
        except Exception as e:
            results['errors'].append({
                'file': str(py_file),
                'error': str(e)
            })
    
    return results

def main():
    """
    Main function to run security audit on the project.
    
    This function:
    1. Audits all Python modules for potential external calls
    2. Reports safe and unsafe files
    3. Provides recommendations for fixing unsafe files
    """
    project_root = Path(__file__).parent.parent.parent
    audit_results = audit_all_modules(project_root)
    
    print(f"\n{'='*60}")
    print("SECURITY AUDIT RESULTS")
    print(f"{'='*60}")
    print(f"Audited {len(audit_results['audited_files'])} files")
    print(f"Safe files: {len(audit_results['safe_files'])}")
    print(f"Unsafe files: {len(audit_results['unsafe_files'])}")
    print(f"Errors: {len(audit_results['errors'])}")
    
    if audit_results['unsafe_files']:
        print("\n⚠️  Unsafe files detected:")
        for file in audit_results['unsafe_files']:
            print(f"  - {file}")
        
        print("\n🔧 Recommendations:")
        print("  1. Review each unsafe file for external API calls")
        print("  2. Replace network calls with local alternatives")
        print("  3. Use the @ensure_no_network_access decorator for critical functions")
        print("  4. Run the audit again after fixes")
        return 1
    
    if audit_results['errors']:
        print("\n❌ Errors during audit:")
        for error in audit_results['errors']:
            print(f"  - {error['file']}: {error['error']}")
        return 1
    
    print("\n✅ All files passed security audit!")
    print("No external API calls detected in the codebase.")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
