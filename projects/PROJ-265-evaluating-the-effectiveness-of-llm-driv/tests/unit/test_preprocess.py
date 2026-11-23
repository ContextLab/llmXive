"""
Unit tests for the preprocess module (T010).

Tests:
- CodeSanitizer removes dangerous functions (eval, exec, open, etc.)
- CodeSanitizer mocks dangerous imports (os, sys, subprocess, etc.)
- sanitize_code returns correct structure
- preprocess_function handles various input cases
- run_preprocessing processes files correctly
"""

import ast
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from data.preprocess import CodeSanitizer, sanitize_code, preprocess_function, run_preprocessing


class TestCodeSanitizer:
    """Tests for the CodeSanitizer AST transformer."""
    
    def test_removes_eval_call(self):
        """Test that eval() calls are removed."""
        code = "result = eval('1 + 1')"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'eval' not in result['sanitized_code']
        assert any('Removed dangerous call: eval' in change for change in result['changes'])
    
    def test_removes_exec_call(self):
        """Test that exec() calls are removed."""
        code = "exec('print(1)')"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'exec' not in result['sanitized_code']
    
    def test_removes_open_call(self):
        """Test that open() calls are removed."""
        code = "f = open('file.txt', 'r')"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'open' not in result['sanitized_code']
    
    def test_removes_os_system_call(self):
        """Test that os.system() calls are removed."""
        code = "os.system('ls -la')"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'os.system' not in result['sanitized_code']
    
    def test_mocks_os_import(self):
        """Test that 'import os' is mocked."""
        code = "import os\nos.getcwd()"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'import os' not in result['sanitized_code']
        assert any('Mocked import: os' in change for change in result['changes'])
    
    def test_mocks_sys_import(self):
        """Test that 'import sys' is mocked."""
        code = "import sys\nsys.exit(0)"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'import sys' not in result['sanitized_code']
        assert any('Mocked import: sys' in change for change in result['changes'])
    
    def test_mocks_from_import(self):
        """Test that 'from os import path' is mocked."""
        code = "from os import path\npath.exists('file')"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'from os import' not in result['sanitized_code']
        assert any('Mocked from-import: os' in change for change in result['changes'])
    
    def test_removes_print_statement(self):
        """Test that print statements are removed."""
        code = "print('Hello, World!')"
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'print' not in result['sanitized_code']
        assert any('Removed print statement' in change for change in result['changes'])
    
    def test_preserves_safe_code(self):
        """Test that safe code is preserved."""
        code = """
        def add(a, b):
            return a + b
        
        result = add(1, 2)
        """
        result = sanitize_code(code)
        assert result['success'] is True
        assert 'def add' in result['sanitized_code']
        assert 'return a + b' in result['sanitized_code']
    
    def test_handles_syntax_error(self):
        """Test that syntax errors are handled gracefully."""
        code = "def broken("  # Invalid syntax
        result = sanitize_code(code)
        assert result['success'] is False
        assert 'SyntaxError' in str(result['changes'])

class TestSanitizeCode:
    """Tests for the sanitize_code function."""
    
    def test_returns_dict_structure(self):
        """Test that sanitize_code returns the expected dictionary structure."""
        code = "x = 1"
        result = sanitize_code(code)
        assert isinstance(result, dict)
        assert 'sanitized_code' in result
        assert 'changes' in result
        assert 'success' in result
        assert isinstance(result['changes'], list)
    
    def test_empty_code(self):
        """Test handling of empty code."""
        result = sanitize_code("")
        assert result['success'] is True
        assert result['sanitized_code'] == ""
    
    def test_complex_dangerous_calls(self):
        """Test removal of multiple dangerous calls."""
        code = """
        import os
        import subprocess
        x = eval("1+1")
        f = open("test.txt")
        subprocess.run(["ls"])
        """
        result = sanitize_code(code)
        assert result['success'] is True
        # Verify dangerous elements are removed
        assert 'eval' not in result['sanitized_code']
        assert 'open' not in result['sanitized_code']
        assert 'subprocess.run' not in result['sanitized_code']
        assert 'import os' not in result['sanitized_code']
        assert 'import subprocess' not in result['sanitized_code']

class TestPreprocessFunction:
    """Tests for the preprocess_function function."""
    
    def test_basic_preprocessing(self):
        """Test basic function preprocessing."""
        func_dict = {
            'code': 'import os\nx = eval("1")',
            'id': 'test_001',
            'name': 'test_func'
        }
        result = preprocess_function(func_dict)
        
        assert 'sanitized_code' in result
        assert 'preprocessed' in result
        assert 'preprocessing_log' in result
        assert result['preprocessed'] is True
        assert result['id'] == 'test_001'
    
    def test_preserves_original_keys(self):
        """Test that original keys are preserved."""
        func_dict = {
            'code': 'x = 1',
            'id': 'test_002',
            'name': 'my_func',
            'metadata': {'source': 'test'}
        }
        result = preprocess_function(func_dict)
        
        assert result['id'] == 'test_002'
        assert result['name'] == 'my_func'
        assert result['metadata'] == {'source': 'test'}

class TestRunPreprocessing:
    """Tests for the run_preprocessing function."""
    
    def test_process_file(self):
        """Test processing a JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_dir = Path(tmpdir) / "output"
            
            # Create input file
            test_functions = [
                {'code': 'import os\nx = 1', 'id': '1'},
                {'code': 'import sys\ny = 2', 'id': '2'},
                {'code': 'def safe(): pass', 'id': '3'}
            ]
            
            with open(input_path, 'w') as f:
                for func in test_functions:
                    f.write(json.dumps(func) + '\n')
            
            # Run preprocessing
            result = run_preprocessing(str(input_path), str(output_dir))
            
            # Verify results
            assert result['functions_processed'] == 3
            assert result['success_count'] == 3
            assert result['error_count'] == 0
            assert result['output_file'] == str(output_dir / "preprocessed_functions.jsonl")
            
            # Verify output file exists and contains valid JSON
            output_file = Path(result['output_file'])
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 3
                
                for line in lines:
                    parsed = json.loads(line)
                    assert 'sanitized_code' in parsed
                    assert 'preprocessed' in parsed

    def test_missing_input_file(self):
        """Test handling of missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.jsonl"
            output_dir = Path(tmpdir) / "output"
            
            with pytest.raises(FileNotFoundError):
                run_preprocessing(str(input_path), str(output_dir))
    
    def test_invalid_json_lines(self):
        """Test handling of invalid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_dir = Path(tmpdir) / "output"
            
            # Create input file with invalid JSON
            with open(input_path, 'w') as f:
                f.write('{"code": "x = 1"}\n')
                f.write('invalid json\n')
                f.write('{"code": "y = 2"}\n')
            
            result = run_preprocessing(str(input_path), str(output_dir))
            
            # Should process 2 valid lines, 1 error
            assert result['functions_processed'] == 3
            assert result['error_count'] == 1
            assert result['success_count'] == 2