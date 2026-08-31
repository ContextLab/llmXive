import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import subprocess
import xml.etree.ElementTree as ET

# Import the module under test
from src.metrics_pmd import (
    get_pmd_path,
    validate_java_syntax,
    calculate_cc_single_file,
    calculate_cc_batch,
    calculate_cc_for_directory,
    save_results
)

@pytest.fixture
def temp_java_file():
    """Create a temporary valid Java file."""
    content = """
    public class TestClass {
        public void simpleMethod() {
            int x = 1;
            if (x > 0) {
                System.out.println("Positive");
            } else {
                System.out.println("Non-positive");
            }
        }
        
        public void complexMethod(int a, int b) {
            if (a > 0) {
                if (b > 0) {
                    return;
                }
            } else if (a < 0) {
                return;
            }
            // More logic
            while (a > 0) {
                a--;
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_invalid_java_file():
    """Create a temporary invalid Java file (syntax error)."""
    content = """
    public class InvalidClass {
        public void brokenMethod() {
            if (x > 0 { // Missing closing parenthesis
                System.out.println("Error");
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        f.flush()
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_dir_with_java(temp_java_file):
    """Create a temporary directory containing a Java file."""
    dir_path = tempfile.mkdtemp()
    file_name = os.path.basename(temp_java_file)
    dest_path = os.path.join(dir_path, file_name)
    os.rename(temp_java_file, dest_path)
    yield dir_path
    os.rmdir(dir_path)
    os.unlink(dest_path)

class TestWrapperPmd:
    def test_get_pmd_path_found(self):
        """Test that get_pmd_path returns a valid path if PMD is installed."""
        with patch('src.metrics_pmd.shutil.which', return_value='/usr/bin/pmd'):
            path = get_pmd_path()
            assert path == '/usr/bin/pmd'

    def test_get_pmd_path_not_found(self):
        """Test that get_pmd_path raises error if PMD is not installed."""
        with patch('src.metrics_pmd.shutil.which', return_value=None):
            with pytest.raises(FileNotFoundError):
                get_pmd_path()

    def test_validate_java_syntax_valid(self):
        """Test validation of a valid Java file."""
        with tempfile.NamedTemporaryFile(suffix='.java', delete=False) as f:
            f.write(b"public class Test {}")
            path = f.name
        try:
            assert validate_java_syntax(path) is True
        finally:
            os.unlink(path)

    def test_validate_java_syntax_invalid_extension(self):
        """Test validation of a non-Java file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"hello")
            path = f.name
        try:
            assert validate_java_syntax(path) is False
        finally:
            os.unlink(path)

    def test_calculate_cc_single_file_valid(self, temp_java_file):
        """Test CC calculation for a valid Java file."""
        # Mock subprocess.run to return a known XML output
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <pmd version="7.0.0">
            <file name="{}">
                <violation beginline="3" endline="8" begincolumn="9" endcolumn="1" rule="CyclomaticComplexity" ruleset="Complexity" package="TestClass" class="TestClass" method="simpleMethod" externalInfoUrl="https://pmd.github.io/pmd-7.0.0/pmd_rules_java_complexity.html#cyclomaticcomplexity" priority="3">
                    The method simpleMethod() has a Cyclomatic Complexity of 2.
                </violation>
                <violation beginline="11" endline="22" begincolumn="9" endcolumn="1" rule="CyclomaticComplexity" ruleset="Complexity" package="TestClass" class="TestClass" method="complexMethod" externalInfoUrl="https://pmd.github.io/pmd-7.0.0/pmd_rules_java_complexity.html#cyclomaticcomplexity" priority="3">
                    The method complexMethod(int,int) has a Cyclomatic Complexity of 6.
                </violation>
            </file>
        </pmd>
        """.format(temp_java_file)

        with patch('src.metrics_pmd.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=mock_xml.encode('utf-8'),
                stderr=b"",
                returncode=0
            )
            
            cc = calculate_cc_single_file(temp_java_file)
            
            # Expected: 2 + 6 = 8
            assert cc == 8

    def test_calculate_cc_single_file_no_violations(self, temp_java_file):
        """Test CC calculation when no violations are found (CC=0)."""
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <pmd version="7.0.0">
        </pmd>
        """

        with patch('src.metrics_pmd.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=mock_xml.encode('utf-8'),
                stderr=b"",
                returncode=0
            )
            
            cc = calculate_cc_single_file(temp_java_file)
            assert cc == 0

    def test_calculate_cc_single_file_syntax_error(self, temp_invalid_java_file):
        """Test handling of a file with syntax errors."""
        mock_stderr = "Error: Cannot parse file: ParseException"
        
        with patch('src.metrics_pmd.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=b"",
                stderr=mock_stderr.encode('utf-8'),
                returncode=1
            )
            
            with pytest.raises(RuntimeError, match="PMD parse error"):
                calculate_cc_single_file(temp_invalid_java_file)

    def test_calculate_cc_batch(self, temp_java_file):
        """Test batch processing of multiple files."""
        files = [temp_java_file]
        
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <pmd version="7.0.0">
            <file name="{}">
                <violation complexity="2">Simple violation</violation>
            </file>
        </pmd>
        """.format(temp_java_file)

        with patch('src.metrics_pmd.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=mock_xml.encode('utf-8'),
                stderr=b"",
                returncode=0
            )
            
            results = calculate_cc_batch(files)
            
            assert len(results) == 1
            assert results[temp_java_file] == 2

    def test_calculate_cc_for_directory(self, temp_dir_with_java):
        """Test directory scanning and processing."""
        dir_path = temp_dir_with_java
        
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <pmd version="7.0.0">
            <file name="{}">
                <violation complexity="3">Violation</violation>
            </file>
        </pmd>
        """.format(os.path.join(dir_path, "TestClass.java"))

        with patch('src.metrics_pmd.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout=mock_xml.encode('utf-8'),
                stderr=b"",
                returncode=0
            )
            
            results = calculate_cc_for_directory(dir_path)
            
            assert len(results) == 1
            # Verify key contains the full path
            assert any("TestClass.java" in k for k in results.keys())

    def test_save_results(self, temp_java_file):
        """Test saving results to a JSON file."""
        results = {temp_java_file: 5}
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            save_results(results, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data[temp_java_file] == 5
        finally:
            os.unlink(output_path)