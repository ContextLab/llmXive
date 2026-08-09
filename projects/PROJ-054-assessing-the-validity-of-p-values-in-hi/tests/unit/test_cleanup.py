"""
Unit tests for cleanup and refactoring module (T036).
"""

import pytest
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from cleanup_refactor import (
    extract_imports_from_file,
    analyze_file_for_cleanup,
    refactor_file,
    validate_apis,
    run_cleanup,
    CodeCleanupError
)

class TestExtractImports:
    """Tests for extract_imports_from_file function."""

    def test_extract_imports_simple(self):
        """Test extracting simple imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys\n")
            temp_path = Path(f.name)
        
        try:
            imports = extract_imports_from_file(temp_path)
            assert "import os" in imports
            assert "import sys" in imports
        finally:
            os.unlink(temp_path)

    def test_extract_imports_from(self):
        """Test extracting from imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from numpy import array\nfrom scipy.stats import ks_2samp\n")
            temp_path = Path(f.name)
        
        try:
            imports = extract_imports_from_file(temp_path)
            assert any("from numpy import" in imp for imp in imports)
            assert any("from scipy.stats import" in imp for imp in imports)
        finally:
            os.unlink(temp_path)

    def test_extract_imports_invalid_syntax(self):
        """Test that invalid syntax raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys\nthis is not valid python\n")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(CodeCleanupError):
                extract_imports_from_file(temp_path)
        finally:
            os.unlink(temp_path)

class TestAnalyzeFile:
    """Tests for analyze_file_for_cleanup function."""

    def test_analyze_blank_lines(self):
        """Test counting of blank lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n\nimport sys\n\n")
            temp_path = Path(f.name)
        
        try:
            analysis = analyze_file_for_cleanup(temp_path)
            assert analysis['blank_lines'] == 2
            assert analysis['lines'] == 4
        finally:
            os.unlink(temp_path)

    def test_analyze_comments(self):
        """Test counting of comment lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# This is a comment\nimport os\n# Another comment\n")
            temp_path = Path(f.name)
        
        try:
            analysis = analyze_file_for_cleanup(temp_path)
            assert analysis['comment_lines'] == 2
        finally:
            os.unlink(temp_path)

    def test_analyze_todo_comments(self):
        """Test detection of TODO comments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n# TODO: Fix this\nimport sys\n")
            temp_path = Path(f.name)
        
        try:
            analysis = analyze_file_for_cleanup(temp_path)
            todo_issues = [i for i in analysis['issues'] if i['type'] == 'TODO/FIXME']
            assert len(todo_issues) == 1
        finally:
            os.unlink(temp_path)

    def test_analyze_long_lines(self):
        """Test detection of long lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n" + "x" * 130 + "\n")
            temp_path = Path(f.name)
        
        try:
            analysis = analyze_file_for_cleanup(temp_path)
            long_line_issues = [i for i in analysis['issues'] if i['type'] == 'line_length']
            assert len(long_line_issues) == 1
        finally:
            os.unlink(temp_path)

    def test_analyze_print_statements(self):
        """Test detection of print statements."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nprint('hello')\n")
            temp_path = Path(f.name)
        
        try:
            analysis = analyze_file_for_cleanup(temp_path)
            print_issues = [i for i in analysis['issues'] if i['type'] == 'print_statement']
            assert len(print_issues) == 1
        finally:
            os.unlink(temp_path)

class TestRefactorFile:
    """Tests for refactor_file function."""

    def test_refactor_trailing_whitespace(self):
        """Test removal of trailing whitespace."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os   \nimport sys\n")
            temp_path = Path(f.name)
        
        try:
            result = refactor_file(temp_path, dry_run=False)
            assert result['changes_made'] is True
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert '   \n' not in content
        finally:
            os.unlink(temp_path)

    def test_refactor_dry_run(self):
        """Test dry run mode."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os   \nimport sys\n")
            temp_path = Path(f.name)
            original_content = f.read()
        
        try:
            result = refactor_file(temp_path, dry_run=True)
            assert result['changes_made'] is True
            
            # File should not be modified in dry run
            with open(temp_path, 'r') as f:
                assert f.read() == original_content
        finally:
            os.unlink(temp_path)

    def test_refactor_print_to_logging(self):
        """Test conversion of print to logging."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import logging\nlogger = logging.getLogger()\nprint('hello')\n")
            temp_path = Path(f.name)
        
        try:
            result = refactor_file(temp_path, dry_run=False)
            assert result['changes_made'] is True
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "logger.info('hello')" in content
                assert "print('hello')" not in content
        finally:
            os.unlink(temp_path)

class TestValidateAPIs:
    """Tests for validate_apis function."""

    def test_validate_valid_imports(self):
        """Test validation with valid imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys\nfrom numpy import array\n")
            temp_path = Path(f.name)
        
        try:
            errors = validate_apis(temp_path)
            # Should not have errors for known modules
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_syntax_error(self):
        """Test validation with syntax error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nthis is invalid\n")
            temp_path = Path(f.name)
        
        try:
            errors = validate_apis(temp_path)
            assert len(errors) > 0
            assert any("Syntax error" in e for e in errors)
        finally:
            os.unlink(temp_path)

class TestRunCleanup:
    """Tests for run_cleanup function."""

    def test_run_cleanup_on_temp_dir(self):
        """Test running cleanup on a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create a test file
            test_file = tmp_path / "test.py"
            test_file.write_text("import os\nprint('hello')\n")
            
            results = run_cleanup(tmp_path, dry_run=True)
            
            assert results['files_processed'] == 1
            assert results['dry_run'] is True
            assert len(results['files']) == 1

    def test_run_cleanup_skips_cache(self):
        """Test that cleanup skips __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create __pycache__ directory with a file
            cache_dir = tmp_path / "__pycache__"
            cache_dir.mkdir()
            cache_file = cache_dir / "test.cpython-311.pyc"
            cache_file.write_text("fake")
            
            # Create a regular file
            test_file = tmp_path / "test.py"
            test_file.write_text("import os\n")
            
            results = run_cleanup(tmp_path, dry_run=True)
            
            # Should only process the regular file, not the cache
            assert results['files_processed'] == 1