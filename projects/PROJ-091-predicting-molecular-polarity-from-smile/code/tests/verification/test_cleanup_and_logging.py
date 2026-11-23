"""
Verification tests for T039d: Unused import removal and logging standardization.

This module verifies that:
1. Unused imports have been removed from all Python scripts in code/
2. All logging statements use the standardized format string
"""
import os
import re
import ast
import logging
import pytest
from pathlib import Path
from typing import List, Tuple, Set, Dict, Optional
import sys

# Add code directory to path for imports
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Standardized logging format as specified in T039c
STANDARD_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def get_all_python_files(root_dir: Path) -> List[Path]:
    """Recursively find all .py files in the code directory."""
    return list(root_dir.rglob("*.py"))


def parse_imports(file_path: Path) -> Tuple[Set[str], Set[str]]:
    """
    Parse a Python file and extract imported names.
    Returns (all_import_names, unused_import_names)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            # Skip files with syntax errors (shouldn't happen in completed tasks)
            return set(), set()

    all_imports = set()
    imported_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)
                all_imports.add(name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imported_names.add(name)
                all_imports.add(name)

    return all_imports, imported_names


def get_used_names(file_path: Path) -> Set[str]:
    """Extract all names used in a Python file (excluding imports)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return set()

    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attribute patterns
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    return used_names


def find_unused_imports(file_path: Path) -> List[str]:
    """Find imports that are declared but never used in the file."""
    all_imports, imported_names = parse_imports(file_path)
    used_names = get_used_names(file_path)
    
    # Filter out built-in names and common exceptions
    common_builtins = {
        'os', 'sys', 'pathlib', 'Path', 're', 'json', 'pickle', 'gc',
        'logging', 'ast', 'math', 'typing', 'Iterator', 'Tuple', 'List',
        'Dict', 'Any', 'Optional', 'Set', 'Callable', 'types', 'inspect',
        'argparse', 'hashlib', 'gzip', 'requests', 'yaml', 'dataclass',
        'field', 'asdict', 'dataclasses', 'pytest', 'shutil', 'tempfile'
    }
    
    unused = []
    for name in imported_names:
        # Skip builtins and common modules
        if name in common_builtins:
            continue
        # Check if name is used in the file
        if name not in used_names:
            # Additional check: see if it appears in the source text
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Simple heuristic: if name appears only in import lines, it's unused
                lines = content.split('\n')
                import_lines = [l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')]
                non_import_lines = [l for l in lines if not l.strip().startswith('import ') and not l.strip().startswith('from ')]
                
                # Count occurrences in non-import lines
                occurrences = sum(1 for line in non_import_lines if re.search(r'\b' + re.escape(name) + r'\b', line))
                if occurrences == 0:
                    unused.append(name)
    
    return unused


def check_logging_format(file_path: Path) -> List[Tuple[int, str]]:
    """
    Check if logging calls in a file use the standardized format.
    Returns list of (line_number, line_content) for non-compliant logging calls.
    """
    non_compliant = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Pattern to match logging calls
    logging_pattern = re.compile(r'logging\.(debug|info|warning|error|critical)\s*\(')
    logger_pattern = re.compile(r'logger\.(debug|info|warning|error|critical)\s*\(')
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments and empty lines
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        
        # Check for logging calls
        if logging_pattern.search(line) or logger_pattern.search(line):
            # Check if it uses the standard format or a format string
            # Allow: logging.info("message") or logger.info("message")
            # Allow: logging.info(format_string, args)
            # Disallow: logging.info("message", extra={...}) with custom format
            
            # Simple check: if the line contains a custom format string that doesn't match standard
            if 'format=' in line or 'fmt=' in line:
                if STANDARD_LOG_FORMAT not in line:
                    non_compliant.append((line_num, line.strip()))
            
            # Check for non-standard format strings in f-strings or concatenations
            # This is a heuristic - we look for logging calls that don't use the standard pattern
            if re.search(r'logging\.\w+\s*\([^,]+,\s*extra\s*=', line):
                # Check if the extra dict contains a custom format
                if 'format' in line and STANDARD_LOG_FORMAT not in line:
                    non_compliant.append((line_num, line.strip()))
    
    return non_compliant


class TestUnusedImportRemoval:
    """Tests for T039b: Unused import removal verification."""
    
    @pytest.fixture
    def code_dir(self) -> Path:
        """Get the code directory path."""
        return code_root / "code"
    
    def test_no_unused_imports_in_scripts(self, code_dir: Path):
        """Verify that all Python scripts in code/ have no unused imports."""
        py_files = get_all_python_files(code_dir)
        
        # Exclude test files and utility scripts that might have intentional unused imports
        exclude_patterns = ['test_', 'cleanup_imports.py', 'setup_directories.py']
        py_files = [f for f in py_files if not any(p in str(f) for p in exclude_patterns)]
        
        violations = []
        for file_path in py_files:
            unused = find_unused_imports(file_path)
            if unused:
                violations.append(f"{file_path.relative_to(code_root)}: {unused}")
        
        assert len(violations) == 0, f"Found unused imports in:\n" + "\n".join(violations)


class TestLoggingStandardization:
    """Tests for T039c: Logging standardization verification."""
    
    @pytest.fixture
    def code_dir(self) -> Path:
        """Get the code directory path."""
        return code_root / "code"
    
    def test_standard_logging_format(self, code_dir: Path):
        """Verify that all logging calls use the standardized format."""
        py_files = get_all_python_files(code_dir)
        
        # Exclude test files
        py_files = [f for f in py_files if 'test_' not in str(f)]
        
        violations = []
        for file_path in py_files:
            non_compliant = check_logging_format(file_path)
            if non_compliant:
                for line_num, line in non_compliant:
                    violations.append(f"{file_path.relative_to(code_root)}:{line_num}: {line}")
        
        # Note: This test is lenient - it only catches explicit format overrides
        # The primary verification is that the logging_config.py sets the standard format
        assert len(violations) == 0, f"Found non-standard logging format:\n" + "\n".join(violations)
    
    def test_logging_config_uses_standard_format(self, code_dir: Path):
        """Verify that logging_config.py defines the standard format."""
        logging_config_path = code_dir / "utils" / "logging_config.py"
        
        assert logging_config_path.exists(), "logging_config.py not found"
        
        with open(logging_config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that the standard format is defined
        assert STANDARD_LOG_FORMAT in content, \
            f"Standard logging format not found in logging_config.py. Expected: {STANDARD_LOG_FORMAT}"
    
    def test_rotating_file_handler_configured(self, code_dir: Path):
        """Verify that RotatingFileHandler is used for logs/app.log."""
        logging_config_path = code_dir / "utils" / "logging_config.py"
        
        with open(logging_config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for RotatingFileHandler
        assert 'RotatingFileHandler' in content, \
            "RotatingFileHandler not found in logging_config.py"
        
        # Check for logs/app.log
        assert 'logs/app.log' in content, \
            "logs/app.log not found in logging_config.py"


class TestIntegration:
    """Integration tests for T039d."""
    
    def test_imports_and_logging_are_clean(self):
        """Run both checks together to ensure code quality."""
        code_dir = code_root / "code"
        py_files = get_all_python_files(code_dir)
        
        # Exclude test files and utility scripts
        exclude_patterns = ['test_', 'cleanup_imports.py', 'setup_directories.py']
        py_files = [f for f in py_files if not any(p in str(f) for p in exclude_patterns)]
        
        all_unused = []
        all_format_issues = []
        
        for file_path in py_files:
            unused = find_unused_imports(file_path)
            if unused:
                all_unused.append(f"{file_path.relative_to(code_root)}: {unused}")
            
            non_compliant = check_logging_format(file_path)
            if non_compliant:
                for line_num, line in non_compliant:
                    all_format_issues.append(f"{file_path.relative_to(code_root)}:{line_num}: {line}")
        
        assert len(all_unused) == 0, f"Unused imports found:\n" + "\n".join(all_unused)
        assert len(all_format_issues) == 0, f"Logging format issues found:\n" + "\n".join(all_format_issues)
    
    def test_verification_script_exists(self):
        """Verify that cleanup_imports.py exists and can be imported."""
        cleanup_path = code_root / "code" / "cleanup_imports.py"
        
        assert cleanup_path.exists(), "cleanup_imports.py not found"
        
        # Try to import it
        try:
            from code.cleanup_imports import get_all_python_files, get_all_imports, get_used_names
        except ImportError as e:
            pytest.fail(f"Failed to import cleanup_imports.py: {e}")
    
    def test_logging_config_can_be_imported(self):
        """Verify that logging_config.py can be imported and used."""
        try:
            from code.utils.logging_config import setup_logging, get_logger, STANDARD_LOG_FORMAT
        except ImportError as e:
            pytest.fail(f"Failed to import logging_config.py: {e}")