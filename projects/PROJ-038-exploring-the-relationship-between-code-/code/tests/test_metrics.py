"""
Tests for the metrics extraction module.
"""
import pytest
from pathlib import Path
import tempfile
import os
import sys
import json
from unittest.mock import patch, MagicMock

from src.metrics import calculate_loc_ast, calculate_loc_batch, calculate_cc_single_file, calculate_halstead_single_file, calculate_metrics_batch

@pytest.fixture
def temp_java_file():
    """Create a temporary valid Java file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        content = """
        public class TestClass {
            public static void main(String[] args) {
                int x = 1;
                if (x > 0) {
                    System.out.println("Positive");
                }
            }
        }
        """
        f.write(content)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_java_file_with_comments():
    """Create a temporary Java file with various comments."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        content = """
        // This is a single line comment
        public class TestComments {
            /* 
             * Multi-line comment
             */
            public void method() {
                int a = 1; // inline comment
                // another single line
            }
        }
        """
        f.write(content)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_invalid_file():
    """Create a temporary invalid file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Not a java file")
        yield f.name
    os.unlink(f.name)

class TestLOC:
    def test_loc_returns_int(self, temp_java_file):
        """Test that calculate_loc_ast returns an integer."""
        result = calculate_loc_ast(temp_java_file)
        assert isinstance(result, int)
        assert result > 0

    def test_loc_counts_code_lines(self, temp_java_file):
        """Test that LOC counts actual code lines, excluding comments."""
        result = calculate_loc_ast(temp_java_file)
        # The file has: class def, main def, var decl, if, print, if close, main close, class close
        # Approx 7-8 lines of code.
        assert result >= 5

    def test_loc_excludes_comments(self, temp_java_file_with_comments):
        """Test that comments are not counted as code lines."""
        result = calculate_loc_ast(temp_java_file_with_comments)
        # Should be less than total lines
        assert result < 10

    def test_loc_non_existent_file(self):
        """Test handling of non-existent file."""
        with pytest.raises(FileNotFoundError):
            calculate_loc_ast("/non/existent/file.java")

    def test_loc_invalid_extension(self, temp_invalid_file):
        """Test handling of non-Java file."""
        with pytest.raises(ValueError):
            calculate_loc_ast(temp_invalid_file)

class TestLOCBatch:
    def test_loc_batch(self, temp_java_file, temp_java_file_with_comments):
        """Test batch LOC calculation."""
        files = [temp_java_file, temp_java_file_with_comments]
        results = calculate_loc_batch(files)
        
        assert len(results) == 2
        assert temp_java_file in results
        assert temp_java_file_with_comments in results
        assert isinstance(results[temp_java_file], int)

class TestCyclomaticComplexity:
    @patch('src.metrics.get_pmd_path')
    @patch('subprocess.run')
    def test_calculate_cc_single_file_mocked(self, mock_run, mock_get_pmd, temp_java_file):
        """Test CC calculation with mocked PMD."""
        mock_get_pmd.return_value = "/fake/pmd/path"
        
        # Mock the subprocess to return a fake XML
        mock_xml = """
        <pmd version="7.0.0">
            <file name="Test.java">
                <violation rule="CyclomaticComplexity" beginline="3" endline="3" msg="Cyclomatic Complexity is 2">
                    Cyclomatic Complexity is 2
                </violation>
            </file>
        </pmd>
        """
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_xml, stderr="")
        
        # Mock os.path.exists to return True for the output file
        with patch('os.path.exists', return_value=True):
            # Mock ET.parse to return a fake tree
            with patch('src.metrics.ET.parse') as mock_parse:
                mock_root = MagicMock()
                mock_file_elem = MagicMock()
                mock_violation = MagicMock()
                mock_violation.get.return_value = 'CyclomaticComplexity'
                mock_violation.text = "Cyclomatic Complexity is 2"
                mock_file_elem.findall.return_value = [mock_violation]
                mock_root.findall.return_value = [mock_file_elem]
                mock_tree = MagicMock()
                mock_tree.getroot.return_value = mock_root
                mock_parse.return_value = mock_tree

                result = calculate_cc_single_file(temp_java_file)
                assert result == 2

class TestHalstead:
    def test_halstead_returns_float(self, temp_java_file):
        """Test that calculate_halstead_single_file returns a float."""
        result = calculate_halstead_single_file(temp_java_file)
        assert isinstance(result, float)
        assert result >= 0.0

class TestMetricsBatch:
    def test_calculate_metrics_batch(self, temp_java_file):
        """Test full metrics batch calculation."""
        results = calculate_metrics_batch([temp_java_file])
        
        assert len(results) == 1
        item = results[0]
        assert 'file_path' in item
        assert 'loc' in item
        assert 'cc' in item
        assert 'halstead' in item
        assert isinstance(item['loc'], int)
        assert isinstance(item['cc'], int)
        assert isinstance(item['halstead'], float)