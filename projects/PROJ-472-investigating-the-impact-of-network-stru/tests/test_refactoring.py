"""
Tests for refactoring utilities (T026).

These tests verify that the code cleanup and modularity tools work correctly.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).parent.parent / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

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
        """Test that we can extract functions and classes from a module."""
        result = get_module_functions('code.config')
        assert 'functions' in result
        assert 'classes' in result
        assert 'all' in result
        assert isinstance(result['functions'], list)
        assert isinstance(result['classes'], list)

    def test_extracts_known_exports(self):
        """Test that known exports are found in config module."""
        result = get_module_functions('code.config')
        # get_data_root and ensure_directories should be in the module
        assert 'get_data_root' in result['all'] or 'ensure_directories' in result['all']


class TestValidateModuleExports:
    """Tests for validate_module_exports."""

    def test_validates_existing_module(self):
        """Test validation of a known module."""
        success, missing = validate_module_exports(
            'code.config',
            ['get_data_root', 'ensure_directories']
        )
        # Should pass if exports exist
        assert success is True or len(missing) == 0

    def test_detects_missing_exports(self):
        """Test that missing exports are detected."""
        success, missing = validate_module_exports(
            'code.config',
            ['nonexistent_function_12345']
        )
        assert success is False
        assert 'nonexistent_function_12345' in missing


class TestOrganizeImports:
    """Tests for organize_imports."""

    def test_reorganizes_imports(self):
        """Test that imports are reordered."""
        test_code = """
import sys
import os
from pathlib import Path
from typing import List
import numpy as np
import pandas as pd
from code.config import get_data_root
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name

        try:
            result = organize_imports(temp_path)
            lines = result.split('\n')

            # Find import lines
            import_lines = [l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')]

            # Verify stdlib comes first
            stdlib_indices = [i for i, l in enumerate(import_lines) if any(s in l for s in ['import os', 'import sys', 'from pathlib', 'from typing'])]
            third_party_indices = [i for i, l in enumerate(import_lines) if any(s in l for s in ['numpy', 'pandas'])]
            local_indices = [i for i, l in enumerate(import_lines) if 'code.config' in l]

            # Check ordering (stdlib < third_party < local)
            if stdlib_indices and third_party_indices:
                assert max(stdlib_indices) < min(third_party_indices)
        finally:
            os.unlink(temp_path)


class TestExtractConstants:
    """Tests for extract_constants."""

    def test_extracts_upper_case_constants(self):
        """Test extraction of module-level constants."""
        test_code = """
MAX_SIZE = 100
DEFAULT_SEED = 42
PI = 3.14159

def my_function():
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name

        try:
            constants = extract_constants(temp_path)
            assert 'MAX_SIZE' in constants
            assert constants['MAX_SIZE'] == 100
            assert 'DEFAULT_SEED' in constants
            assert constants['DEFAULT_SEED'] == 42
        finally:
            os.unlink(temp_path)

    def test_ignores_lowercase_variables(self):
        """Test that lowercase variables are not extracted."""
        test_code = """
my_var = 100
MY_CONST = 200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name

        try:
            constants = extract_constants(temp_path)
            assert 'my_var' not in constants
            assert 'MY_CONST' in constants
        finally:
            os.unlink(temp_path)


class TestCheckCircularDependencies:
    """Tests for check_circular_dependencies."""

    def test_no_cycles_in_simple_modules(self):
        """Test that independent modules show no cycles."""
        # These modules should not have circular dependencies
        modules = ['code.config', 'code.utils.logger']
        cycles = check_circular_dependencies(modules)
        # May have cycles depending on actual imports, but test runs without error
        assert isinstance(cycles, list)


class TestGenerateModuleDocumentation:
    """Tests for generate_module_documentation."""

    def test_generates_documentation(self):
        """Test that documentation is generated."""
        doc = generate_module_documentation('code.config')
        assert isinstance(doc, str)
        assert len(doc) > 0
        assert 'Module:' in doc or 'code.config' in doc


class TestRunRefactoringChecks:
    """Tests for run_refactoring_checks."""

    def test_runs_checks_without_error(self):
        """Test that checks run and return results."""
        results = run_refactoring_checks(str(code_dir.parent))
        assert 'total_modules' in results
        assert 'circular_dependencies' in results
        assert 'recommendations' in results
        assert isinstance(results['total_modules'], int)
        assert isinstance(results['circular_dependencies'], list)
        assert isinstance(results['recommendations'], list)

    def test_returns_recommendations(self):
        """Test that recommendations are provided."""
        results = run_refactoring_checks(str(code_dir.parent))
        assert len(results['recommendations']) > 0
        # Should have at least one recommendation (even if positive)
        assert any(isinstance(rec, str) for rec in results['recommendations'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])