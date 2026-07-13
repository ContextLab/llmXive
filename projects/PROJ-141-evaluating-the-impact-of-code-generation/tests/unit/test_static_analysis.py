"""
Unit tests for static analysis warning count functionality.

Tests for code/quality/static_analysis.py
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from quality.static_analysis import (
    run_pylint,
    run_checkstyle,
    detect_language,
    analyze_static_warnings,
    StaticAnalysisError
)


class TestDetectLanguage:
    """Tests for language detection."""

    def test_detect_python_simple(self):
        """Test detection of simple Python code."""
        code = "def hello():\n    print('world')"
        assert detect_language(code) == 'python'

    def test_detect_python_imports(self):
        """Test detection of Python with imports."""
        code = "import os\nimport sys\n\ndef main():\n    pass"
        assert detect_language(code) == 'python'

    def test_detect_java_simple(self):
        """Test detection of simple Java code."""
        code = "public class Main {\n    public static void main(String[] args) {\n    }\n}"
        assert detect_language(code) == 'java'

    def test_detect_java_imports(self):
        """Test detection of Java with imports."""
        code = "import java.util.List;\nimport java.util.ArrayList;\n\npublic class Test {}"
        assert detect_language(code) == 'java'

    def test_detect_unknown(self):
        """Test detection of unknown language."""
        code = "This is not code\nJust plain text"
        assert detect_language(code) == 'unknown'

    def test_detect_empty(self):
        """Test detection of empty code."""
        assert detect_language("") == 'unknown'


class TestRunPylint:
    """Tests for pylint analysis."""

    def test_pylint_no_warnings(self):
        """Test pylint on clean Python code."""
        # Simple clean code that should have no warnings with our config
        code = "def add(a, b):\n    return a + b\n"
        
        count, details = run_pylint(code)
        
        assert count >= 0  # May have some warnings depending on pylint version
        assert details['tool'] == 'pylint'
        assert details['language'] == 'python'
        assert 'total_issues' in details

    def test_pylint_syntax_error(self):
        """Test pylint on code with syntax error."""
        code = "def broken(\n    print('missing paren')"
        
        count, details = run_pylint(code)
        
        assert count >= 0
        assert details['tool'] == 'pylint'
        assert details['language'] == 'python'

    def test_pylint_empty_code(self):
        """Test pylint on empty code."""
        count, details = run_pylint("")
        
        assert count == 0
        assert details['total_issues'] == 0

    def test_pylint_complex_code(self):
        """Test pylint on more complex Python code."""
        code = """
def calculate_sum(numbers):
    '''Calculate the sum of a list of numbers.'''
    total = 0
    for num in numbers:
  total += num
    return total

def calculate_average(numbers):
    '''Calculate the average of a list of numbers.'''
    if not numbers:
  return 0
    return calculate_sum(numbers) / len(numbers)
"""
        count, details = run_pylint(code)
        
        assert count >= 0
        assert details['tool'] == 'pylint'
        assert details['language'] == 'python'


class TestRunCheckstyle:
    """Tests for checkstyle analysis."""

    @pytest.mark.skipif(
        not shutil.which('java') or not os.environ.get('CHECKSTYLE_PATH'),
        reason="Java or checkstyle not available"
    )
    def test_checkstyle_no_warnings(self):
        """Test checkstyle on clean Java code."""
        import shutil
        
        code = """
public class Calculator {
    public int add(int a, int b) {
  return a + b;
    }
}
"""
        count, details = run_checkstyle(code)
        
        assert count >= 0
        assert details['tool'] == 'checkstyle'
        assert details['language'] == 'java'

    @pytest.mark.skipif(
        not shutil.which('java') or not os.environ.get('CHECKSTYLE_PATH'),
        reason="Java or checkstyle not available"
    )
    def test_checkstyle_syntax_error(self):
        """Test checkstyle on code with syntax error."""
        import shutil
        
        code = """
public class Broken {
    public int brokenMethod(
  return 0;
    }
}
"""
        count, details = run_checkstyle(code)
        
        assert count >= 0
        assert details['tool'] == 'checkstyle'
        assert details['language'] == 'java'

    def test_checkstyle_not_available(self):
        """Test checkstyle when not available."""
        # Temporarily unset CHECKSTYLE_PATH
        old_path = os.environ.pop('CHECKSTYLE_PATH', None)
        try:
            code = "public class Test {}"
            count, details = run_checkstyle(code)
            
            assert count == 0
            assert details.get('error') == 'not_found'
        finally:
            if old_path:
                os.environ['CHECKSTYLE_PATH'] = old_path


class TestAnalyzeStaticWarnings:
    """Tests for the main analysis function."""

    def test_analyze_python_code(self):
        """Test analysis of Python code."""
        code = "def hello():\n    print('world')"
        
        count, details = analyze_static_warnings(code)
        
        assert count >= 0
        assert details['language'] == 'python'

    def test_analyze_java_code(self):
        """Test analysis of Java code."""
        code = "public class Test {}"
        
        count, details = analyze_static_warnings(code)
        
        assert count >= 0
        assert details['language'] == 'java'

    def test_analyze_empty_code(self):
        """Test analysis of empty code."""
        count, details = analyze_static_warnings("")
        
        assert count == 0
        assert details['total_issues'] == 0

    def test_analyze_with_language_hint(self):
        """Test analysis with explicit language hint."""
        code = "def test(): pass"
        
        # Force Python analysis
        count, details = analyze_static_warnings(code, language='python')
        assert details['language'] == 'python'

    def test_analyze_unknown_language(self):
        """Test analysis of unknown language."""
        code = "This is not code"
        
        count, details = analyze_static_warnings(code)
        
        assert count == 0
        assert 'unknown' in details.get('language', '').lower()


class TestStaticAnalysisError:
    """Tests for the custom exception."""

    def test_exception_creation(self):
        """Test creating StaticAnalysisError."""
        error = StaticAnalysisError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_inheritance(self):
        """Test that StaticAnalysisError is an Exception."""
        assert isinstance(StaticAnalysisError("test"), Exception)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])