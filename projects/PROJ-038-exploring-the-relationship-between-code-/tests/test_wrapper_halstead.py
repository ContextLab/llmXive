import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from wrapper_halstead import (
    load_file_list,
    calculate_halstead_single_file,
    calculate_halstead_batch,
    save_results,
    build_halstead_jar
)

@pytest.fixture
def temp_java_file():
    """Create a temporary valid Java file for testing."""
    content = """
    public class TestClass {
        public static void main(String[] args) {
            int x = 5 + 10;
            if (x > 10) {
                System.out.println("Greater");
            } else {
                System.out.println("Less");
            }
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        return Path(f.name)

@pytest.fixture
def temp_file_list(temp_java_file):
    """Create a temporary file list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([str(temp_java_file)], f)
        return Path(f.name)

@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        return Path(f.name)

class TestLoadFileList:
    def test_load_json_list(self, temp_file_list):
        files = load_file_list(temp_file_list)
        assert len(files) == 1
        assert files[0].endswith('.java')

    def test_load_text_list(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("/path/to/file1.java\n/path/to/file2.java\n")
            txt_path = Path(f.name)
        
        try:
            files = load_file_list(txt_path)
            assert len(files) == 2
            assert files[0] == "/path/to/file1.java"
        finally:
            os.unlink(txt_path)

class TestCalculateHalsteadSingleFile:
    @patch('wrapper_halstead.subprocess.run')
    def test_returns_metrics_on_success(self, mock_run, temp_java_file, temp_output_file):
        # Mock the subprocess to return a successful JSON output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "operators": 10.0,
            "operands": 5.0,
            "volume": 50.0,
            "length": 15.0,
            "difficulty": 2.0,
            "effort": 100.0,
            "bugs": 1.0
        })
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Mock jar path existence
        with patch('wrapper_halstead.Path.exists', return_value=True):
            metrics = calculate_halstead_single_file(temp_java_file, Path("dummy.jar"))
            
            assert metrics is not None
            assert 'halstead_volume' in metrics or 'volume' in metrics
            assert metrics['file_path'] == str(temp_java_file)

    @patch('wrapper_halstead.subprocess.run')
    def test_returns_none_on_parse_error(self, mock_run, temp_java_file, temp_output_file):
        # Mock a parse error
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Parse error at line 5"
        mock_run.return_value = mock_result

        with patch('wrapper_halstead.Path.exists', return_value=True):
            metrics = calculate_halstead_single_file(temp_java_file, Path("dummy.jar"))
            assert metrics is None

    def test_file_not_found(self, temp_output_file):
        fake_path = Path("/nonexistent/file.java")
        metrics = calculate_halstead_single_file(fake_path, Path("dummy.jar"))
        assert metrics is None

class TestCalculateHalsteadBatch:
    @patch('wrapper_halstead.build_halstead_jar')
    @patch('wrapper_halstead.load_file_list')
    @patch('wrapper_halstead.calculate_halstead_single_file')
    @patch('wrapper_halstead.save_results')
    def test_batch_processing(
        self, 
        mock_save, 
        mock_calc, 
        mock_load, 
        mock_build, 
        temp_file_list, 
        temp_output_file
    ):
        mock_build.return_value = Path("dummy.jar")
        mock_load.return_value = ["/file1.java", "/file2.java"]
        mock_calc.side_effect = [
            {"volume": 10.0, "file_path": "/file1.java"},
            {"volume": 20.0, "file_path": "/file2.java"}
        ]

        results = calculate_halstead_batch(temp_file_list, temp_output_file)
        
        assert len(results) == 2
        assert mock_save.called
        assert mock_save.call_args[0][0] == results

class TestSaveResults:
    def test_save_json(self, temp_output_file):
        data = [{"volume": 10.0}, {"volume": 20.0}]
        save_results(data, temp_output_file)
        
        assert temp_output_file.exists()
        with open(temp_output_file, 'r') as f:
            loaded = json.load(f)
        
        assert len(loaded) == 2
        assert loaded[0]["volume"] == 10.0