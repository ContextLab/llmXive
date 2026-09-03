import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import subprocess

# Import the module under test
# Note: Ensure the path is correct relative to where tests run
from code.src.metrics_pmd import (
    calculate_cc_single_file,
    calculate_cc_batch,
    calculate_cc_for_directory,
    ToolchainError,
    get_pmd_path,
    validate_java_syntax,
    PMD_RULESET
)

# Fixtures
@pytest.fixture
def temp_java_file():
    """Creates a temporary valid Java file."""
    content = """
    public class Test {
        public void method1() {
            if (true) {
                System.out.println("hi");
            }
        }
        public void method2() {
            int x = 0;
            if (x > 0) {
                x++;
            } else if (x < 0) {
                x--;
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        return f.name

@pytest.fixture
def temp_invalid_java_file():
    """Creates a temporary invalid Java file (syntax error)."""
    content = """
    public class Test {
        public void method1() {
            if (true { // Missing closing parenthesis
                System.out.println("hi");
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        return f.name

@pytest.fixture
def temp_dir_with_java(temp_java_file):
    """Creates a temporary directory containing the java file."""
    dir_path = Path(temp_java_file).parent
    return str(dir_path)

@pytest.fixture
def cleanup_jar():
    """Yields, then cleans up any generated jars if needed (not used here but good practice)."""
    yield
    # Cleanup logic if jars were created

class TestWrapperPmd:
    
    def test_get_pmd_path_found(self):
        """Test that get_pmd_path returns a valid path or 'pmd'."""
        # Mock environment variables
        with patch.dict(os.environ, {"PMD_PATH": "/fake/pmd/bin/pmd"}):
            # If the file doesn't exist, it might return the string, 
            # but the function logic checks for existence if it's a dir.
            # Let's test the fallback
            pass
        
        # Test default
        path = get_pmd_path()
        assert path is not None
        assert isinstance(path, str)

    def test_validate_java_syntax_valid(self, temp_java_file):
        """Test validation of a valid Java file."""
        assert validate_java_syntax(temp_java_file) is True

    def test_validate_java_syntax_invalid_extension(self, temp_java_file):
        """Test validation of a non-java file."""
        invalid_path = temp_java_file.replace(".java", ".txt")
        # Create the file first
        with open(invalid_path, 'w') as f:
            f.write("test")
        try:
            assert validate_java_syntax(invalid_path) is False
        finally:
            os.remove(invalid_path)

    def test_validate_java_syntax_empty(self):
        """Test validation of an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write("")
            path = f.name
        try:
            assert validate_java_syntax(path) is False
        finally:
            os.remove(path)

    @patch('subprocess.run')
    def test_calculate_cc_single_file_valid(self, mock_run, temp_java_file):
        """Test successful calculation of CC with mocked subprocess."""
        # Mock successful PMD run
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <pmd>
            <file name="{}">
                <violation beginline="3" endline="6" begincolumn="13" endcolumn="1" rule="CyclomaticComplexity" ruleset="Complexity Rules" class="Test" method="method1" externalInfoUrl="" priority="3" complexity="2">
                    Avoid really long methods.
                </violation>
                <violation beginline="8" endline="14" begincolumn="13" endcolumn="1" rule="CyclomaticComplexity" ruleset="Complexity Rules" class="Test" method="method2" externalInfoUrl="" priority="3" complexity="3">
                    Avoid really long methods.
                </violation>
            </file>
        </pmd>""".format(temp_java_file)

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xml,
            stderr=""
        )

        # Mock get_pmd_path to return a fake path
        with patch('code.src.metrics_pmd.get_pmd_path', return_value="/fake/pmd"):
            result = calculate_cc_single_file(temp_java_file, "/fake/pmd")
            
        # Expected sum: 2 + 3 = 5
        assert result == 5
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_calculate_cc_single_file_no_violations(self, mock_run, temp_java_file):
        """Test calculation when PMD finds no violations (low complexity)."""
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <pmd>
        </pmd>"""
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_xml,
            stderr=""
        )

        with patch('code.src.metrics_pmd.get_pmd_path', return_value="/fake/pmd"):
            result = calculate_cc_single_file(temp_java_file, "/fake/pmd")
            
        assert result == 0

    @patch('subprocess.run')
    def test_calculate_cc_single_file_pmd_error(self, mock_run, temp_invalid_java_file):
        """Test that ToolchainError is raised when PMD fails to parse."""
        mock_run.return_value = MagicMock(
            returncode=4, # PMD error code
            stdout="",
            stderr="Syntax error in file"
        )

        with patch('code.src.metrics_pmd.get_pmd_path', return_value="/fake/pmd"):
            with pytest.raises(ToolchainError) as excinfo:
                calculate_cc_single_file(temp_invalid_java_file, "/fake/pmd")
            
            assert "PMD failed to parse" in str(excinfo.value)

    @patch('subprocess.run')
    def test_calculate_cc_single_file_missing_ruleset(self, mock_run, temp_java_file):
        """Test that ToolchainError is raised for missing ruleset."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Ruleset not found"
        )

        with patch('code.src.metrics_pmd.get_pmd_path', return_value="/fake/pmd"):
            with pytest.raises(ToolchainError) as excinfo:
                calculate_cc_single_file(temp_java_file, "/fake/pmd")
            
            assert "ruleset" in str(excinfo.value).lower()

    def test_calculate_cc_batch(self, temp_java_file, temp_invalid_java_file, tmp_path):
        """Test batch processing with mixed valid/invalid files."""
        # Create a list of files
        files = [temp_java_file, temp_invalid_java_file]
        exclusion_log = str(tmp_path / "exclusion.log")
        
        # We need to mock the subprocess call for the valid file to succeed
        # and for the invalid file to fail (or we rely on the real PMD if installed)
        # Since we can't guarantee PMD is installed in the test env, we mock.
        
        with patch('code.src.metrics_pmd.calculate_cc_single_file') as mock_single:
            # First call (valid) returns 5
            # Second call (invalid) raises ToolchainError
            mock_single.side_effect = [5, ToolchainError("Parse error")]
            
            with patch('code.src.metrics_pmd.get_pmd_path', return_value="/fake/pmd"):
                with pytest.raises(ToolchainError):
                    calculate_cc_batch(files, exclusion_log, "/fake/pmd")
            
            # Check that exclusion log was written
            assert os.path.exists(exclusion_log)
            with open(exclusion_log, 'r') as f:
                content = f.read()
                assert "Parse error" in content

    def test_calculate_cc_for_directory(self, temp_dir_with_java, tmp_path):
        """Test directory scanning."""
        exclusion_log = str(tmp_path / "dir_exclusion.log")
        output_json = str(tmp_path / "results.json")
        
        # Mock the batch function to return dummy data
        with patch('code.src.metrics_pmd.calculate_cc_batch', return_value=({temp_dir_with_java + "/test.java": 10}, 0)):
            with patch('code.src.metrics_pmd.save_results'):
                with patch('code.src.metrics_pmd.get_pmd_path', return_value="/fake/pmd"):
                    results, count = calculate_cc_for_directory(temp_dir_with_java, exclusion_log, "/fake/pmd")
                    
                    # Should find the file we created
                    assert len(results) >= 1
                    assert count == 0

    def test_calculate_cc_for_directory_not_found(self, tmp_path):
        """Test error when directory does not exist."""
        fake_dir = str(tmp_path / "non_existent")
        exclusion_log = str(tmp_path / "exclusion.log")
        
        with pytest.raises(ToolchainError) as excinfo:
            calculate_cc_for_directory(fake_dir, exclusion_log, "/fake/pmd")
        
        assert "Directory does not exist" in str(excinfo.value)
