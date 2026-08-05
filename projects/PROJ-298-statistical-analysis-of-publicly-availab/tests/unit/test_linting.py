"""
Unit tests for linting and cleanup utilities.

Tests the linting configuration and cleanup functions
in code/analysis/linting_config.py
"""
import pytest
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.linting_config import (
    get_module_path,
    check_imports,
    check_docstrings,
    check_line_length,
    check_complexity,
    run_lint_checks,
    generate_lint_report,
    cleanup_analysis_modules,
    LINTING_RULES,
    ANALYSIS_MODULES,
)


class TestGetModulePath:
    """Tests for get_module_path function."""
    
    def test_get_module_path_default(self):
        """Test getting module path with default project root."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_dir = tmpdir_path / "analysis"
            analysis_dir.mkdir()
            
            # Create a dummy module
            dummy_module = analysis_dir / "test_module.py"
            dummy_module.write_text("# test")
            
            # Test path generation
            module_path = get_module_path("test_module.py", tmpdir_path)
            assert module_path == analysis_dir / "test_module.py"
            assert module_path.exists()
    
    def test_get_module_path_custom_root(self):
        """Test getting module path with custom project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            custom_analysis = tmpdir_path / "custom_analysis"
            custom_analysis.mkdir()
            
            module_path = get_module_path("test.py", tmpdir_path)
            assert module_path.parent == tmpdir_path / "analysis"


class TestCheckImports:
    """Tests for check_imports function."""
    
    def test_no_imports(self):
        """Test file with no imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# No imports here\n")
            f.write("def hello():\n    pass\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_imports(temp_path)
            assert len(issues) == 0
        finally:
            temp_path.unlink()
    
    def test_wildcard_import(self):
        """Test detection of wildcard imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from math import *\n")
            f.write("def hello():\n    return sqrt(4)\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_imports(temp_path)
            assert len(issues) > 0
            assert any("Wildcard import" in issue for issue in issues)
        finally:
            temp_path.unlink()
    
    def test_normal_import(self):
        """Test file with normal imports."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n")
            f.write("from pathlib import Path\n")
            f.write("def hello():\n    return os.getcwd()\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_imports(temp_path)
            # Should not report wildcard imports
            assert not any("Wildcard import" in issue for issue in issues)
        finally:
            temp_path.unlink()
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        issues = check_imports(Path("/nonexistent/file.py"))
        assert len(issues) == 1
        assert "File not found" in issues[0]


class TestCheckDocstrings:
    """Tests for check_docstrings function."""
    
    def test_missing_module_docstring(self):
        """Test detection of missing module docstring."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# No docstring\n")
            f.write("def hello():\n    pass\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_docstrings(temp_path)
            assert len(issues) > 0
            assert any("Missing module docstring" in issue for issue in issues)
        finally:
            temp_path.unlink()
    
    def test_missing_function_docstring(self):
        """Test detection of missing function docstring."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('"""Module docstring."""\n')
            f.write("def hello():\n    pass\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_docstrings(temp_path)
            assert len(issues) > 0
            assert any("Missing docstring in hello" in issue for issue in issues)
        finally:
            temp_path.unlink()
    
    def test_all_docstrings_present(self):
        """Test file with all required docstrings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('"""Module docstring."""\n\n')
            f.write('def hello():\n    """Function docstring."""\n    pass\n')
            f.write('\n')
            f.write('class MyClass:\n    """Class docstring."""\n    pass\n')
            temp_path = Path(f.name)
        
        try:
            issues = check_docstrings(temp_path)
            # Should not report missing docstrings
            assert len(issues) == 0
        finally:
            temp_path.unlink()


class TestCheckLineLength:
    """Tests for check_line_length function."""
    
    def test_short_lines(self):
        """Test file with all short lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Short line\n")
            f.write("def hello():\n")
            f.write("    return 42\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_line_length(temp_path, max_length=100)
            assert len(issues) == 0
        finally:
            temp_path.unlink()
    
    def test_long_lines(self):
        """Test detection of long lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Short line\n")
            f.write("x = " + "a" * 100 + "\n")  # Line longer than 100 chars
            f.write("def hello():\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_line_length(temp_path, max_length=100)
            assert len(issues) > 0
            assert any("exceeds 100 characters" in issue for issue in issues)
        finally:
            temp_path.unlink()


class TestCheckComplexity:
    """Tests for check_complexity function."""
    
    def test_simple_function(self):
        """Test function with low complexity."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('"""Module doc."""\n')
            f.write("def simple():\n")
            f.write("    return 42\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_complexity(temp_path, max_complexity=15)
            assert len(issues) == 0
        finally:
            temp_path.unlink()
    
    def test_complex_function(self):
        """Test function with high complexity."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('"""Module doc."""\n')
            f.write("def complex_func(x):\n")
            f.write("    if x > 0:\n")
            f.write("        if x > 10:\n")
            f.write("            if x > 20:\n")
            f.write("                if x > 30:\n")
            f.write("                    return 'very large'\n")
            f.write("                return 'large'\n")
            f.write("            return 'medium'\n")
            f.write("        return 'small'\n")
            f.write("    return 'negative'\n")
            temp_path = Path(f.name)
        
        try:
            issues = check_complexity(temp_path, max_complexity=5)
            assert len(issues) > 0
            assert any("complexity" in issue.lower() for issue in issues)
        finally:
            temp_path.unlink()


class TestRunLintChecks:
    """Tests for run_lint_checks function."""
    
    def test_run_checks_on_temp_modules(self):
        """Test running lint checks on temporary modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_dir = tmpdir_path / "analysis"
            analysis_dir.mkdir()
            
            # Create a valid module
            valid_module = analysis_dir / "valid.py"
            valid_module.write_text('"""Valid module."""\n\ndef hello():\n    """Hello."""\n    return 42\n')
            
            # Create a module with issues
            bad_module = analysis_dir / "bad.py"
            bad_module.write_text("from math import *\n")  # Wildcard import
            bad_module.write_text("def bad():\n")  # Missing docstring
            bad_module.write_text("    x = " + "a" * 100 + "\n")  # Long line
            
            results = run_lint_checks(tmpdir_path)
            
            assert "valid.py" in results
            assert "bad.py" in results
            
            # Valid module should have no issues
            assert len(results["valid.py"]) == 0
            
            # Bad module should have issues
            assert len(results["bad.py"]) > 0


class TestGenerateLintReport:
    """Tests for generate_lint_report function."""
    
    def test_report_with_issues(self):
        """Test report generation with issues."""
        results = {
            "module1.py": ["Issue 1", "Issue 2"],
            "module2.py": [],
        }
        
        report = generate_lint_report(results)
        
        assert "module1.py" in report
        assert "module2.py" in report
        assert "Total issues found: 2" in report
    
    def test_report_no_issues(self):
        """Test report generation with no issues."""
        results = {
            "module1.py": [],
            "module2.py": [],
        }
        
        report = generate_lint_report(results)
        
        assert "No issues" in report
        assert "All modules pass linting checks" in report


class TestCleanupAnalysisModules:
    """Tests for cleanup_analysis_modules function."""
    
    def test_cleanup_creates_report(self):
        """Test that cleanup creates a report file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            analysis_dir = tmpdir_path / "analysis"
            analysis_dir.mkdir()
            
            # Create a dummy module
            dummy_module = analysis_dir / "dummy.py"
            dummy_module.write_text('"""Dummy module."""\n')
            
            report = cleanup_analysis_modules(tmpdir_path)
            
            # Check report was created
            report_path = analysis_dir / "linting_report.txt"
            assert report_path.exists()
            
            # Check report content
            with open(report_path, 'r') as f:
                content = f.read()
                assert "Linting Report" in content
                assert "dummy.py" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])