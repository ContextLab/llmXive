"""
Unit tests for the cleanup_refactor module.

Tests the code analysis and refactoring utilities implemented in T036.
"""

import ast
import os
import tempfile
from pathlib import Path
import pytest

from code.cleanup_refactor import (
    CodeCleanupError,
    extract_imports_from_file,
    analyze_file_for_cleanup,
    refactor_file,
    validate_apis,
    run_cleanup
)


class TestExtractImports:
    """Tests for import extraction functionality."""

    def test_extract_simple_imports(self):
        """Test extraction of simple import statements."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import numpy as np
import pandas
from scipy import stats
from utils.exceptions import AnalysisError
""")
            f.flush()
            file_path = Path(f.name)

        try:
            imports = extract_imports_from_file(file_path)
            assert 'numpy' in imports
            assert 'np' in imports['numpy']
            assert 'pandas' in imports
            assert 'scipy' in imports
            assert 'stats' in imports['scipy']
            assert 'utils' in imports
            assert 'AnalysisError' in imports['utils']
        finally:
            os.unlink(file_path)

    def test_extract_no_imports(self):
        """Test file with no imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def hello():
    return "world"
""")
            f.flush()
            file_path = Path(f.name)

        try:
            imports = extract_imports_from_file(file_path)
            assert len(imports) == 0
        finally:
            os.unlink(file_path)

    def test_extract_invalid_syntax(self):
        """Test handling of invalid Python syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import numpy
def broken(:
    pass
""")
            f.flush()
            file_path = Path(f.name)

        try:
            with pytest.raises(CodeCleanupError):
                extract_imports_from_file(file_path)
        finally:
            os.unlink(file_path)


class TestAnalyzeFileForCleanup:
    """Tests for file analysis functionality."""

    def test_count_functions_and_classes(self):
        """Test counting of functions and classes."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
class MyClass:
    pass

def func1():
    pass

def func2():
    pass

class AnotherClass:
    pass
""")
            f.flush()
            file_path = Path(f.name)

        try:
            analysis = analyze_file_for_cleanup(file_path)
            assert analysis['function_count'] == 2
            assert analysis['class_count'] == 2
        finally:
            os.unlink(file_path)

    def test_detect_missing_docstrings(self):
        """Test detection of missing docstrings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
class GoodClass:
    \"\"\"This class has a docstring.\"\"\"
    pass

def good_function():
    \"\"\"This function has a docstring.\"\"\"
    pass

class BadClass:
    pass

def bad_function():
    pass
""")
            f.flush()
            file_path = Path(f.name)

        try:
            analysis = analyze_file_for_cleanup(file_path)
            assert len(analysis['docstring_issues']) == 2
            assert any('BadClass' in issue for issue in analysis['docstring_issues'])
            assert any('bad_function' in issue for issue in analysis['docstring_issues'])
        finally:
            os.unlink(file_path)

    def test_detect_long_lines(self):
        """Test detection of lines exceeding 100 characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
short = 1
this_is_a_very_long_line_that_exceeds_the_hundred_character_limit_and_should_be_flagged_by_the_analyzer = 2
another_short = 3
""")
            f.flush()
            file_path = Path(f.name)

        try:
            analysis = analyze_file_for_cleanup(file_path)
            assert len(analysis['long_lines']) == 1
            assert 2 in analysis['long_lines']  # Line 2 is the long one
        finally:
            os.unlink(file_path)

    def test_detect_unused_imports(self):
        """Test detection of unused imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import numpy as np
import pandas
from scipy import stats

def use_numpy():
    return np.array([1, 2, 3])
""")
            f.flush()
            file_path = Path(f.name)

        try:
            analysis = analyze_file_for_cleanup(file_path)
            assert any('pandas' in unused for unused in analysis['unused_imports'])
            assert any('stats' in unused for unused in analysis['unused_imports'])
        finally:
            os.unlink(file_path)

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        file_path = Path('/nonexistent/file.py')
        with pytest.raises(CodeCleanupError):
            analyze_file_for_cleanup(file_path)


class TestRefactorFile:
    """Tests for file refactoring functionality."""

    def test_refactor_dry_run(self):
        """Test dry run mode doesn't modify file."""
        original_content = """
import numpy as np
import unused_module

def hello():
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_content)
            f.flush()
            file_path = Path(f.name)

        try:
            success, message = refactor_file(file_path, dry_run=True)
            assert success
            assert "Dry run" in message

            # Verify file unchanged
            with open(file_path, 'r') as f:
                assert f.read() == original_content
        finally:
            os.unlink(file_path)

    def test_refactor_real_run(self):
        """Test actual refactoring modifies file."""
        original_content = """
import numpy as np
import unused_module

def hello():
    pass
"""
        expected_content = """
import numpy as np

def hello():
    pass
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(original_content)
            f.flush()
            file_path = Path(f.name)

        try:
            success, message = refactor_file(file_path, dry_run=False)
            assert success

            with open(file_path, 'r') as f:
                content = f.read()
                # Should have removed unused import
                assert 'unused_module' not in content
                assert 'import numpy' in content
        finally:
            os.unlink(file_path)


class TestValidateAPIs:
    """Tests for API validation functionality."""

    def test_validate_all_present(self):
        """Test validation when all expected names are present."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def public_function():
    pass

class PublicClass:
    pass

def _private_function():
    pass
""")
            f.flush()
            file_path = Path(f.name)

        try:
            success, missing = validate_apis(
                file_path,
                {'public_function', 'PublicClass'}
            )
            assert success
            assert len(missing) == 0
        finally:
            os.unlink(file_path)

    def test_validate_missing_names(self):
        """Test validation when some expected names are missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def only_one_function():
    pass
""")
            f.flush()
            file_path = Path(f.name)

        try:
            success, missing = validate_apis(
                file_path,
                {'only_one_function', 'missing_function', 'missing_class'}
            )
            assert not success
            assert 'missing_function' in missing
            assert 'missing_class' in missing
        finally:
            os.unlink(file_path)


class TestRunCleanup:
    """Tests for the main cleanup runner."""

    def test_run_cleanup_dry_run(self):
        """Test cleanup dry run on a temporary project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a test file
            code_dir = project_root / 'code'
            code_dir.mkdir()
            test_file = code_dir / 'test_module.py'
            test_file.write_text("""
import unused_import

def test_func():
    pass
""")

            results = run_cleanup(project_root, dry_run=True)

            assert results['files_processed'] == 1
            assert results['files_modified'] == 0  # Dry run shouldn't modify
            assert results['issues_found'] > 0

    def test_run_cleanup_real(self):
        """Test actual cleanup modifies files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a test file
            code_dir = project_root / 'code'
            code_dir.mkdir()
            test_file = code_dir / 'test_module.py'
            test_file.write_text("""
import unused_import

def test_func():
    pass
""")

            results = run_cleanup(project_root, dry_run=False)

            assert results['files_processed'] == 1
            assert results['files_modified'] == 1
            assert results['issues_found'] > 0

            # Verify file was modified
            content = test_file.read_text()
            assert 'unused_import' not in content