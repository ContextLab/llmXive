"""
Unit tests for static_analysis.py
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

from static_analysis import get_file_language, run_radon_on_file, run_semgrep_on_file

def test_get_file_language():
    assert get_file_language(Path("test.py")) == "python"
    assert get_file_language(Path("test.java")) == "java"
    assert get_file_language(Path("test.js")) == "javascript"
    assert get_file_language(Path("test.ts")) == "typescript"
    assert get_file_language(Path("test.go")) == "go"
    assert get_file_language(Path("test.rs")) == "rust"
    assert get_file_language(Path("test.txt")) is None

@patch('static_analysis.open', new_callable=MagicMock)
@patch('static_analysis.cc_visit')
@patch('static_analysis.mi_visit')
def test_run_radon_on_file(mock_mi, mock_cc, mock_open):
    # Mock file content
    mock_open.return_value.__enter__.return_value.read.return_value = "def foo(): pass"
    
    # Mock Radon results
    mock_func = MagicMock()
    mock_func.cc = 2
    mock_cc.return_value = [mock_func]
    mock_mi.return_value = [50.0]
    
    avg_cc, avg_mi, total_cc = run_radon_on_file(Path("test.py"))
    
    assert avg_cc == 2.0
    assert total_cc == 2
    assert avg_mi == 50.0

@patch('static_analysis.subprocess.run')
def test_run_semgrep_on_file(mock_run):
    # Mock subprocess output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = '{"results": [{"rule": "test-rule"}]}'
    mock_run.return_value = mock_result
    
    code_smells, cc = run_semgrep_on_file(Path("test.java"))
    
    assert code_smells == 1
    assert cc == 1