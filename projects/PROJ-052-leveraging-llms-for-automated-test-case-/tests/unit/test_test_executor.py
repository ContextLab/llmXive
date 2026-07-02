"""
Unit tests for code/test_executor.py

These tests verify the core functionality of the test executor module,
including subprocess handling, timeout logic, and result formatting.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.test_executor import (
    _run_subprocess,
    _find_jacoco_agent,
    _compile_test_file,
    ExecutionResult,
    generate_coverage_csv
)
from code.config import get_timeout_compile

class TestRunSubprocess:
    def test_successful_execution(self):
        """Test that a successful command returns correct output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = ['echo', 'hello']
            returncode, stdout, stderr = _run_subprocess(cmd, timeout=10, cwd=tmpdir)
            assert returncode == 0
            assert 'hello' in stdout

    def test_timeout_handling(self):
        """Test that timeout raises TimeoutExpired."""
        # Create a command that sleeps
        cmd = ['sleep', '5']
        with pytest.raises(subprocess.TimeoutExpired):
            _run_subprocess(cmd, timeout=1)

    def test_non_zero_return_code(self):
        """Test handling of non-zero return codes."""
        cmd = ['false']
        returncode, stdout, stderr = _run_subprocess(cmd, timeout=10)
        assert returncode != 0

class TestFindJacocoAgent:
    def test_env_variable_path(self):
        """Test that JACOCO_CLI_PATH environment variable is respected."""
        with patch.dict(os.environ, {'JACOCO_CLI_PATH': '/fake/path/jacoco.jar'}):
            with patch('os.path.exists', return_value=True):
                result = _find_jacoco_agent()
                assert result == Path('/fake/path/jacoco.jar')

    def test_not_found(self):
        """Test that None is returned when agent is not found."""
        with patch('os.path.exists', return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                result = _find_jacoco_agent()
                assert result is None

class TestCompileTestFile:
    def test_valid_java_compilation(self):
        """Test compilation of a valid Java file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a simple valid Java file
            test_file = tmpdir_path / "SimpleTest.java"
            test_file.write_text("""
            public class SimpleTest {
                public static void main(String[] args) {
                    System.out.println("Hello");
                }
            }
            """)
            
            output_dir = tmpdir_path / "out"
            output_dir.mkdir()
            
            success, error_msg = _compile_test_file(
                test_file, 
                [], 
                output_dir
            )
            
            assert success is True
            assert error_msg == ""
            assert (output_dir / "SimpleTest.class").exists()

    def test_invalid_java_compilation(self):
        """Test compilation of an invalid Java file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create an invalid Java file
            test_file = tmpdir_path / "InvalidTest.java"
            test_file.write_text("""
            public class InvalidTest {
                public static void main(String[] args) {
                    // Missing semicolon
                    System.out.println("Hello")
                }
            }
            """)
            
            output_dir = tmpdir_path / "out"
            output_dir.mkdir()
            
            success, error_msg = _compile_test_file(
                test_file, 
                [], 
                output_dir
            )
            
            assert success is False
            assert len(error_msg) > 0

class TestExecutionResult:
    def test_result_creation(self):
        """Test creating an ExecutionResult object."""
        result = ExecutionResult(
            project_id="proj-1",
            test_type="generated",
            status="success",
            coverage_percentage=75.5
        )
        
        assert result.project_id == "proj-1"
        assert result.test_type == "generated"
        assert result.status == "success"
        assert result.coverage_percentage == 75.5
        assert result.error_msg is None

class TestGenerateCoverageCsv:
    def test_csv_generation(self):
        """Test generating a CSV file from results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "coverage.csv"
            
            results = [
                ExecutionResult("proj-1", "generated", "success", 80.0),
                ExecutionResult("proj-2", "generated", "failed", None, "Error")
            ]
            
            generate_coverage_csv(results, output_path)
            
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3  # Header + 2 rows
                assert 'project_id' in lines[0]
                assert 'proj-1' in lines[1]
                assert 'proj-2' in lines[2]