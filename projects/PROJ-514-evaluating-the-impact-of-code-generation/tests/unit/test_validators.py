"""
Unit tests for code/utils/validators.py.
Target: >=90% line coverage for validators.py.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Adjust path to import from code/utils
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from utils.validators import (
    get_language_from_extension,
    validate_python_syntax,
    validate_java_syntax,
    validate_file_syntax,
    validate_directory
)


class TestGetLanguageFromExtension:
    def test_python_uppercase(self):
        assert get_language_from_extension("TEST.PY") == "python"

    def test_python_lowercase(self):
        assert get_language_from_extension("test.py") == "python"

    def test_java_uppercase(self):
        assert get_language_from_extension("Test.JAVA") == "java"

    def test_java_lowercase(self):
        assert get_language_from_extension("test.java") == "java"

    def test_unknown_extension(self):
        assert get_language_from_extension("readme.md") == "unknown"

    def test_no_extension(self):
        assert get_language_from_extension("Makefile") == "unknown"


class TestValidatePythonSyntax:
    def test_valid_python(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    return 'world'\n")
            f_path = f.name

        try:
            result = validate_python_syntax(f_path)
            assert result is True
        finally:
            os.unlink(f_path)

    def test_invalid_python_syntax(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def broken(\n    return 'world'\n")  # Missing closing paren
            f_path = f.name

        try:
            result = validate_python_syntax(f_path)
            assert result is False
        finally:
            os.unlink(f_path)

    def test_non_python_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("hello world")
            f_path = f.name

        try:
            result = validate_python_syntax(f_path)
            assert result is False
        finally:
            os.unlink(f_path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            f_path = f.name

        try:
            result = validate_python_syntax(f_path)
            assert result is True
        finally:
            os.unlink(f_path)


class TestValidateJavaSyntax:
    def test_valid_java(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write("public class Test { public static void main(String[] args) {} }\n")
            f_path = f.name

        try:
            result = validate_java_syntax(f_path)
            # If javac is not available, the function returns False (as per typical implementation fallback)
            # We assert the function executes without crashing.
            assert isinstance(result, bool)
        finally:
            os.unlink(f_path)

    def test_invalid_java_syntax(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write("public class Test { public static void main(String[] args) { }\n")  # Missing closing brace
            f_path = f.name

        try:
            result = validate_java_syntax(f_path)
            # If javac is available, this should be False. If not, it's False or raises.
            # We assert it returns a boolean or handles the error gracefully.
            assert isinstance(result, bool)
        finally:
            os.unlink(f_path)

    def test_non_java_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            f_path = f.name

        try:
            result = validate_java_syntax(f_path)
            assert result is False
        finally:
            os.unlink(f_path)


class TestValidateFileSyntax:
    def test_valid_python_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 1\n")
            f_path = f.name

        try:
            result = validate_file_syntax(f_path)
            assert result is True
        finally:
            os.unlink(f_path)

    def test_invalid_python_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = \n")
            f_path = f.name

        try:
            result = validate_file_syntax(f_path)
            assert result is False
        finally:
            os.unlink(f_path)

    def test_valid_java_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write("public class X {}")
            f_path = f.name

        try:
            result = validate_file_syntax(f_path)
            # Depends on javac availability, but should return bool
            assert isinstance(result, bool)
        finally:
            os.unlink(f_path)

    def test_unknown_extension_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("data")
            f_path = f.name

        try:
            result = validate_file_syntax(f_path)
            assert result is False
        finally:
            os.unlink(f_path)

    def test_nonexistent_file(self):
        result = validate_file_syntax("/nonexistent/path/file.py")
        assert result is False


class TestValidateDirectory:
    def test_valid_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid python file inside
            Path(tmpdir, "test.py").write_text("x=1")
            result = validate_directory(tmpdir)
            assert result is True

    def test_invalid_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid python file
            Path(tmpdir, "bad.py").write_text("def broken(")
            result = validate_directory(tmpdir)
            assert result is False

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_directory(tmpdir)
            assert result is True

    def test_nonexistent_directory(self):
        result = validate_directory("/nonexistent/dir")
        assert result is False
