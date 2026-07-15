"""
Unit tests for refactoring utilities.

Tests ensure that the refactoring tools correctly analyze module structure,
validate exports, organize imports, and detect issues.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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

    def test_get_module_functions_returns_correct_structure(self):
        """Test that the function returns a dict with functions, classes, and constants."""
        result = get_module_functions('utils.refactor_utils')
        
        assert isinstance(result, dict)
        assert 'functions' in result
        assert 'classes' in result
        assert 'constants' in result
        
        # Should find at least some functions
        assert len(result['functions']) > 0

    def test_get_module_functions_finds_main_function(self):
        """Test that the main function is found."""
        result = get_module_functions('utils.refactor_utils')
        
        function_names = [f['name'] for f in result['functions']]
        assert 'main' in function_names

    def test_get_module_functions_handles_nonexistent_module(self):
        """Test graceful handling of non-existent modules."""
        result = get_module_functions('nonexistent.module.path')
        
        assert result == {'functions': [], 'classes': [], 'constants': []}


class TestValidateModuleExports:
    """Tests for validate_module_exports."""

    def test_validate_module_exports_all_present(self):
        """Test validation when all expected exports are present."""
        result = validate_module_exports(
            'utils.refactor_utils',
            ['get_module_functions', 'main']
        )
        
        assert result['valid'] is True
        assert len(result['missing']) == 0

    def test_validate_module_exports_missing_items(self):
        """Test validation when some exports are missing."""
        result = validate_module_exports(
            'utils.refactor_utils',
            ['nonexistent_function', 'another_missing']
        )
        
        assert result['valid'] is False
        assert 'nonexistent_function' in result['missing']
        assert 'another_missing' in result['missing']

    def test_validate_module_exports_handles_nonexistent_module(self):
        """Test graceful handling of non-existent modules."""
        result = validate_module_exports(
            'nonexistent.module',
            ['some_function']
        )
        
        assert result['valid'] is False
        assert result['missing'] == ['some_function']


class TestOrganizeImports:
    """Tests for organize_imports."""

    def test_organize_imports_returns_string(self):
        """Test that the function returns a string."""
        result = organize_imports('utils/refactor_utils.py')
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_organize_imports_preserves_content(self):
        """Test that the function preserves the original content."""
        result = organize_imports('utils/refactor_utils.py')
        
        # Should still contain the main function definition
        assert 'def main()' in result or 'def main(' in result
        assert 'if __name__' in result

    def test_organize_imports_handles_nonexistent_file(self):
        """Test graceful handling of non-existent files."""
        result = organize_imports('nonexistent/file.py')
        
        assert result is None

    def test_organize_imports_with_temp_file(self):
        """Test import organization with a temporary file."""
        test_content = """
import sys
import os
from utils.logger import get_logger
import pandas as pd
from pathlib import Path

def test_func():
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            result = organize_imports(temp_path)
            
            assert isinstance(result, str)
            # Should have organized imports
            lines = result.split('\n')
            import_lines = [l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')]
            
            # Should have at least some import lines
            assert len(import_lines) > 0
        finally:
            os.unlink(temp_path)


class TestExtractConstants:
    """Tests for extract_constants."""

    def test_extract_constants_returns_list(self):
        """Test that the function returns a list."""
        result = extract_constants('utils/refactor_utils.py')
        
        assert isinstance(result, list)

    def test_extract_constants_finds_uppercase_constants(self):
        """Test that uppercase constants are detected."""
        # Create a temp file with constants
        test_content = """
MAX_VALUE = 100
DEFAULT_TIMEOUT = 30
PI = 3.14

def func():
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            result = extract_constants(temp_path)
            
            names = [c['name'] for c in result]
            assert 'MAX_VALUE' in names
            assert 'DEFAULT_TIMEOUT' in names
            assert 'PI' in names
        finally:
            os.unlink(temp_path)


class TestCheckCircularDependencies:
    """Tests for check_circular_dependencies."""

    def test_check_circular_dependencies_returns_list(self):
        """Test that the function returns a list."""
        result = check_circular_dependencies(['utils/refactor_utils.py'])
        
        assert isinstance(result, list)

    def test_check_circular_dependencies_no_cycles_in_single_module(self):
        """Test that a single module has no circular dependencies."""
        result = check_circular_dependencies(['utils/refactor_utils.py'])
        
        # Should have no cycles
        assert len(result) == 0

    def test_check_circular_dependencies_with_multiple_modules(self):
        """Test circular dependency detection with multiple modules."""
        modules = [
            'utils/refactor_utils.py',
            'utils/logger.py',
            'config.py'
        ]
        result = check_circular_dependencies(modules)
        
        assert isinstance(result, list)
        # If there are cycles, they should be detected
        for cycle in result:
            assert len(cycle) >= 2


class TestGenerateModuleDocumentation:
    """Tests for generate_module_documentation."""

    def test_generate_module_documentation_returns_string(self):
        """Test that the function returns a string."""
        result = generate_module_documentation('utils/refactor_utils.py')
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_module_documentation_contains_module_name(self):
        """Test that the documentation contains the module name."""
        result = generate_module_documentation('utils/refactor_utils.py')
        
        assert 'refactor_utils' in result
        assert '# Module:' in result

    def test_generate_module_documentation_handles_nonexistent_module(self):
        """Test graceful handling of non-existent modules."""
        result = generate_module_documentation('nonexistent/module.py')
        
        assert '*Documentation generation failed*' in result


class TestRunRefactoringChecks:
    """Tests for run_refactoring_checks."""

    def test_run_refactoring_checks_returns_dict(self):
        """Test that the function returns a dictionary."""
        result = run_refactoring_checks('.', ['code/utils'])
        
        assert isinstance(result, dict)
        assert 'modules_analyzed' in result
        assert 'issues_found' in result
        assert 'recommendations' in result

    def test_run_refactoring_checks_analyzes_modules(self):
        """Test that modules are analyzed."""
        result = run_refactoring_checks('.', ['code/utils'])
        
        # Should have analyzed at least some modules
        assert result['modules_analyzed'] > 0

    def test_run_refactoring_checks_with_empty_dir(self):
        """Test handling of empty directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_refactoring_checks(tmpdir, ['nonexistent'])
            
            assert result['modules_analyzed'] == 0
            assert len(result['issues_found']) == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_module(self):
        """Test analysis of an empty module."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = get_module_functions(temp_path.replace('/', '.').replace('\\', '.')[:-3])
            assert result == {'functions': [], 'classes': [], 'constants': []}
        finally:
            os.unlink(temp_path)

    def test_module_with_syntax_error(self):
        """Test handling of modules with syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(")  # Syntax error
            temp_path = f.name

        try:
            result = get_module_functions(temp_path.replace('/', '.').replace('\\', '.')[:-3])
            assert result == {'functions': [], 'classes': [], 'constants': []}
        finally:
            os.unlink(temp_path)

    def test_large_module(self):
        """Test analysis of a large module."""
        content = "\n".join([f"def func_{i}(): pass" for i in range(100)])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = get_module_functions(temp_path.replace('/', '.').replace('\\', '.')[:-3])
            assert len(result['functions']) == 100
        finally:
            os.unlink(temp_path)