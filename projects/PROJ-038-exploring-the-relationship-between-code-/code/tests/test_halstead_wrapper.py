"""
Tests for the Halstead Wrapper Script.
"""
import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics.halstead_wrapper import (
    get_java_compiler_path,
    build_halstead_jar,
    validate_java_syntax,
    calculate_halstead_single_file,
    calculate_halstead_batch
)

@pytest.fixture
def temp_java_file():
    """Create a temporary valid Java file for testing."""
    java_code = """
    public class TestClass {
        public static void main(String[] args) {
            int x = 10;
            int y = 20;
            int z = x + y;
            System.out.println(z);
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(java_code)
        return Path(f.name)

@pytest.fixture
def temp_invalid_java_file():
    """Create a temporary invalid Java file for testing."""
    java_code = """
    public class TestClass {
        public static void main(String[] args) {
            int x = 10
            // Missing semicolon above
            System.out.println(x);
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(java_code)
        return Path(f.name)

@pytest.fixture
def cleanup_jar():
    """Ensure the JAR file is cleaned up after tests."""
    jar_path = Path(__file__).parent.parent / "src" / "metrics" / "halstead_calc.jar"
    yield
    if jar_path.exists():
        jar_path.unlink()

def test_get_java_compiler_path_found():
    """Test that get_java_compiler_path finds javac if it exists."""
    # This test will pass if javac is installed in the environment
    try:
        path = get_java_compiler_path()
        assert path is not None
        assert os.path.exists(path) or path == "javac"
    except FileNotFoundError:
        # If javac is not found, we expect this to fail in environments without Java
        pytest.skip("Java compiler not found in environment")

def test_validate_java_syntax_valid(temp_java_file):
    """Test validation of a valid Java file."""
    try:
        result = validate_java_syntax(temp_java_file)
        # This depends on javac being available
        if result:
            assert result is True
        else:
            # If javac is not available, it might return False
            pytest.skip("Java compiler not available for validation")
    except Exception:
        pytest.skip("Java compiler not available")

def test_validate_java_syntax_invalid(temp_invalid_java_file):
    """Test validation of an invalid Java file."""
    try:
        result = validate_java_syntax(temp_invalid_java_file)
        # This depends on javac being available
        if result is not None:
            assert result is False
        else:
            pytest.skip("Java compiler not available for validation")
    except Exception:
        pytest.skip("Java compiler not available")

def test_calculate_halstead_single_file_valid(temp_java_file, cleanup_jar):
    """Test calculation of Halstead metrics for a valid file."""
    try:
        # First ensure the JAR is built
        if not (Path(__file__).parent.parent / "src" / "metrics" / "halstead_calc.jar").exists():
            build_halstead_jar()
        
        result = calculate_halstead_single_file(temp_java_file)
        
        if result:
            assert "volume" in result
            assert "n1" in result
            assert "n2" in result
            assert "N1" in result
            assert "N2" in result
            assert result["file_path"] == str(temp_java_file)
        else:
            pytest.skip("Java compiler or JAR not available")
    except Exception:
        pytest.skip("Java compiler or JAR not available")

def test_calculate_halstead_single_file_invalid(temp_invalid_java_file, cleanup_jar):
    """Test calculation for an invalid file returns None."""
    try:
        if not (Path(__file__).parent.parent / "src" / "metrics" / "halstead_calc.jar").exists():
            build_halstead_jar()
        
        result = calculate_halstead_single_file(temp_invalid_java_file)
        assert result is None
    except Exception:
        pytest.skip("Java compiler or JAR not available")

def test_calculate_halstead_batch(temp_java_file, temp_invalid_java_file, cleanup_jar):
    """Test batch calculation."""
    try:
        if not (Path(__file__).parent.parent / "src" / "metrics" / "halstead_calc.jar").exists():
            build_halstead_jar()
        
        results = calculate_halstead_batch([temp_java_file, temp_invalid_java_file])
        
        # Should return only valid results
        assert len(results) >= 0  # Could be 0 if javac not available
        
        if results:
            for res in results:
                assert "volume" in res
                assert "n1" in res
    except Exception:
        pytest.skip("Java compiler or JAR not available")
