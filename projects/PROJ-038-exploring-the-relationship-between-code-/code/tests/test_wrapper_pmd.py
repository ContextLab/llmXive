import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from wrapper_pmd import (
    get_pmd_path,
    load_file_list,
    save_results,
    calculate_cc_single_file,
    calculate_cc_batch,
    calculate_cc_for_directory,
    main
)


class TestWrapperPmd:
    """Tests for PMD wrapper functionality."""

    def test_get_pmd_path_from_env(self):
        """Test PMD path retrieval from environment variable."""
        with patch.dict(os.environ, {'PMD_PATH': '/custom/pmd/path'}):
            result = get_pmd_path()
            assert result == '/custom/pmd/path'

    def test_get_pmd_path_from_path(self):
        """Test PMD path retrieval from system PATH."""
        # Mock shutil.which to return a valid path
        with patch('wrapper_pmd.shutil.which', return_value='/usr/bin/pmd'):
            result = get_pmd_path()
            assert result == '/usr/bin/pmd'

    def test_get_pmd_path_not_found(self):
        """Test FileNotFoundError when PMD is not found."""
        with patch('wrapper_pmd.shutil.which', return_value=None):
            with patch('wrapper_pmd.os.path.exists', return_value=False):
                with pytest.raises(FileNotFoundError):
                    get_pmd_path()

    def test_load_file_list_json(self):
        """Test loading file list from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(['/path/to/file1.java', '/path/to/file2.java'], f)
            json_path = f.name

        try:
            result = load_file_list(json_path)
            assert len(result) == 2
            assert '/path/to/file1.java' in result
        finally:
            os.unlink(json_path)

    def test_load_file_list_json_dict(self):
        """Test loading file list from JSON dict with 'files' key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'files': ['/path/to/file1.java']}, f)
            json_path = f.name

        try:
            result = load_file_list(json_path)
            assert len(result) == 1
            assert '/path/to/file1.java' in result
        finally:
            os.unlink(json_path)

    def test_load_file_list_text(self):
        """Test loading file list from text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('/path/to/file1.java\n')
            f.write('/path/to/file2.java\n')
            txt_path = f.name

        try:
            result = load_file_list(txt_path)
            assert len(result) == 2
        finally:
            os.unlink(txt_path)

    def test_load_file_list_not_found(self):
        """Test FileNotFoundError when file list doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_file_list('/nonexistent/path.json')

    def test_save_results(self):
        """Test saving results to JSON file."""
        results = [{'file_path': '/test.java', 'cc': 5}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            save_results(results, output_path)
            
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
                
            assert len(saved_data) == 1
            assert saved_data[0]['file_path'] == '/test.java'
            assert saved_data[0]['cc'] == 5
        finally:
            os.unlink(output_path)

    @patch('wrapper_pmd.subprocess.run')
    def test_calculate_cc_single_file_success(self, mock_run):
        """Test successful CC calculation for a single file."""
        # Mock PMD XML output with CyclomaticComplexity violation
        xml_output = '''<?xml version="1.0" encoding="UTF-8"?>
        <pmd>
            <violation rule="CyclomaticComplexity" complexity="7">
                Method has CyclomaticComplexity=7
            </violation>
        </pmd>'''
        
        mock_run.return_value = MagicMock(
            stdout=xml_output,
            stderr='',
            returncode=0
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write('public class Test {}')
            java_path = f.name

        try:
            result = calculate_cc_single_file(java_path, 'pmd')
            assert result == 7
        finally:
            os.unlink(java_path)

    @patch('wrapper_pmd.subprocess.run')
    def test_calculate_cc_single_file_attribute(self, mock_run):
        """Test CC calculation when value is in attribute."""
        xml_output = '''<?xml version="1.0" encoding="UTF-8"?>
        <pmd>
            <violation rule="CyclomaticComplexity" complexity="12"/>
        </pmd>'''
        
        mock_run.return_value = MagicMock(
            stdout=xml_output,
            stderr='',
            returncode=0
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write('public class Test {}')
            java_path = f.name

        try:
            result = calculate_cc_single_file(java_path, 'pmd')
            assert result == 12
        finally:
            os.unlink(java_path)

    @patch('wrapper_pmd.subprocess.run')
    def test_calculate_cc_single_file_parse_error(self, mock_run):
        """Test handling of PMD parse errors."""
        mock_run.return_value = MagicMock(
            stdout='',
            stderr='Parse error: syntax error in file',
            returncode=1
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write('public class Test {}')
            java_path = f.name

        try:
            result = calculate_cc_single_file(java_path, 'pmd')
            assert result is None
        finally:
            os.unlink(java_path)

    @patch('wrapper_pmd.subprocess.run')
    def test_calculate_cc_single_file_timeout(self, mock_run):
        """Test handling of PMD timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=['pmd'], timeout=60)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write('public class Test {}')
            java_path = f.name

        try:
            with pytest.raises(subprocess.TimeoutExpired):
                calculate_cc_single_file(java_path, 'pmd')
        finally:
            os.unlink(java_path)

    def test_calculate_cc_single_file_not_java(self):
        """Test handling of non-Java file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('print("hello")')
            py_path = f.name

        try:
            result = calculate_cc_single_file(py_path, 'pmd')
            assert result is None
        finally:
            os.unlink(py_path)

    def test_calculate_cc_single_file_not_found(self):
        """Test handling of non-existent file."""
        result = calculate_cc_single_file('/nonexistent/file.java', 'pmd')
        assert result is None

    @patch('wrapper_pmd.calculate_cc_single_file')
    def test_calculate_cc_batch(self, mock_calc):
        """Test batch CC calculation."""
        mock_calc.side_effect = [5, 10, None, 3]
        
        file_list = [
            '/file1.java',
            '/file2.java',
            '/file3.java',
            '/file4.java'
        ]
        
        results = calculate_cc_batch(file_list, 'pmd')
        
        assert len(results) == 4
        assert results[0]['cc'] == 5
        assert results[1]['cc'] == 10
        assert results[2]['cc'] is None
        assert results[3]['cc'] == 3
        assert results[2]['status'] == 'no_violation'

    @patch('wrapper_pmd.calculate_cc_batch')
    @patch('wrapper_pmd.save_results')
    def test_calculate_cc_for_directory(self, mock_save, mock_batch):
        """Test directory CC calculation."""
        mock_batch.return_value = [{'file_path': '/test.java', 'cc': 5}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy Java file
            java_file = Path(tmpdir) / 'Test.java'
            java_file.write_text('public class Test {}')
            
            output_path = Path(tmpdir) / 'results.json'
            
            calculate_cc_for_directory(tmpdir, 'pmd', str(output_path))
            
            mock_batch.assert_called_once()
            mock_save.assert_called_once()
