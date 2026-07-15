"""
Unit tests for refactoring utilities.

Tests ensure that refactoring tools correctly analyze module structure,
validate exports, organize imports, and detect issues.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.refactor_utils import (
    get_module_functions,
    validate_module_exports,
    organize_imports,
    extract_constants,
    check_circular_dependencies,
    generate_module_documentation,
    run_refactoring_checks
)


class TestGetModuleFunctions:
    """Tests for get_module_functions."""

    def test_returns_functions_and_classes(self):
        """Test that function returns both functions and classes."""
        result = get_module_functions('code.config')
        assert 'functions' in result
        assert 'classes' in result
        assert isinstance(result['functions'], list)
        assert isinstance(result['classes'], list)

    def test_handles_missing_module(self):
        """Test that missing module returns error."""
        result = get_module_functions('nonexistent.module')
        assert 'error' in result
        assert result['functions'] == []
        assert result['classes'] == []


class TestValidateModuleExports:
    """Tests for validate_module_exports."""

    def test_validates_existing_exports(self):
        """Test validation with existing exports."""
        result = validate_module_exports('code.config', ['get_data_root', 'ensure_directories'])
        assert result['valid'] is True
        assert result['missing'] == []

    def test_detects_missing_exports(self):
        """Test detection of missing exports."""
        result = validate_module_exports('code.config', ['nonexistent_function'])
        assert result['valid'] is False
        assert 'nonexistent_function' in result['missing']

    def test_handles_missing_module(self):
        """Test validation with missing module."""
        result = validate_module_exports('nonexistent.module', ['func'])
        assert result['valid'] is False
        assert 'error' in result


class TestOrganizeImports:
    """Tests for organize_imports."""

    def test_organizes_imports(self):
        """Test that imports are organized."""
        # Create a temporary file with unorganized imports
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import sys
import os
from typing import List
from pathlib import Path
import numpy as np
""")
            temp_path = f.name

        try:
            result = organize_imports(temp_path)
            assert 'import os' in result
            assert 'import sys' in result
            assert 'from pathlib' in result
            assert 'from typing' in result
        finally:
            os.unlink(temp_path)

    def test_handles_syntax_error(self):
        """Test that syntax errors return original content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(")  # Syntax error
            temp_path = f.name

        try:
            result = organize_imports(temp_path)
            assert result == "def broken("
        finally:
            os.unlink(temp_path)


class TestExtractConstants:
    """Tests for extract_constants."""

    def test_extracts_constants(self):
        """Test extraction of module constants."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
MAX_SIZE = 100
DEFAULT_VALUE = 42
CONSTANT_NAME = "test"
normal_var = "should not be extracted"
""")
            temp_path = f.name

        try:
            result = extract_constants(temp_path)
            assert 'MAX_SIZE' in result
            assert result['MAX_SIZE'] == 100
            assert 'DEFAULT_VALUE' in result
            assert result['DEFAULT_VALUE'] == 42
            assert 'normal_var' not in result
        finally:
            os.unlink(temp_path)

    def test_handles_syntax_error(self):
        """Test that syntax errors return empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("CONST = ")  # Syntax error
            temp_path = f.name

        try:
            result = extract_constants(temp_path)
            assert result == {}
        finally:
            os.unlink(temp_path)


class TestCheckCircularDependencies:
    """Tests for check_circular_dependencies."""

    def test_no_circular_deps(self):
        """Test with modules that have no circular dependencies."""
        result = check_circular_dependencies(['code.config', 'code.utils.logger'])
        # Should not raise or return unexpected results
        assert isinstance(result, list)

    def test_handles_missing_modules(self):
        """Test with non-existent modules."""
        result = check_circular_dependencies(['nonexistent.module'])
        assert isinstance(result, list)


class TestGenerateModuleDocumentation:
    """Tests for generate_module_documentation."""

    def test_generates_documentation(self):
        """Test that documentation is generated."""
        result = generate_module_documentation('code.config')
        assert 'Module: code.config' in result
        assert '## Public Functions' in result

    def test_handles_missing_module(self):
        """Test with non-existent module."""
        result = generate_module_documentation('nonexistent.module')
        assert 'Error loading module' in result


class TestRunRefactoringChecks:
    """Tests for run_refactoring_checks."""

    def test_runs_checks(self):
        """Test that checks run without errors."""
        result = run_refactoring_checks(str(PROJECT_ROOT))
        assert 'modules_analyzed' in result
        assert 'circular_dependencies' in result
        assert isinstance(result['modules_analyzed'], list)
        assert isinstance(result['circular_dependencies'], list)

    def test_handles_invalid_directory(self):
        """Test with invalid directory."""
        result = run_refactoring_checks('/nonexistent/path')
        assert 'modules_analyzed' in result
        assert result['modules_analyzed'] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])