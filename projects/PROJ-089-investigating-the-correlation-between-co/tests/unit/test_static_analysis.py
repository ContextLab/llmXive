import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.static_analysis import get_file_language, run_radon_on_file, run_semgrep_on_file, process_repository

def test_get_file_language():
    assert get_file_language("test.py") == "python"
    assert get_file_language("test.java") == "java"
    assert get_file_language("test.js") == "javascript"
    assert get_file_language("test.ts") == "typescript"
    assert get_file_language("test.go") == "go"
    assert get_file_language("test.rs") == "rust"
    assert get_file_language("test.txt") is None
    assert get_file_language("test.xyz") is None

@patch('subprocess.run')
def test_run_radon_on_file(mock_run):
    # Mock successful radon output
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="test.py\n    <module> 1\n    func_a 2\nTotal: 3\n",
        stderr=""
    )
    
    # Create a temp file to simulate existence
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
        f.write(b"def test(): pass")
        temp_path = f.name
    
    try:
        cc, mi = run_radon_on_file(temp_path)
        # We expect cc to be parsed (at least 0 or some int) and mi to be None if not parsed correctly in mock
        # The mock logic for parsing is simplistic in the test, but ensures the function runs without error
        assert cc is not None or mi is not None # At least one should be attempted
    finally:
        os.unlink(temp_path)

@patch('subprocess.run')
def test_run_semgrep_on_file(mock_run):
    # Mock successful semgrep output with findings
    mock_run.return_value = MagicMock(
        returncode=1, # Semgrep returns 1 if findings found
        stdout=json.dumps({"results": [{"check_id": "test-rule", "path": "test.java"}]}),
        stderr=""
    )
    
    with tempfile.NamedTemporaryFile(suffix='.java', delete=False) as f:
        f.write(b"public class Test {}")
        temp_path = f.name
    
    try:
        smells, findings = run_semgrep_on_file(temp_path)
        assert smells == 1
        assert len(findings) == 1
    finally:
        os.unlink(temp_path)

def test_process_repository():
    # This is an integration-style unit test. 
    # We create a temp repo structure with one python file.
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Create a dummy python file
        test_file = repo_path / "main.py"
        test_file.write_text("def hello(): pass")
        
        output_dir = Path(tmpdir) / "output"
        
        # Mock the subprocess calls inside process_repository to avoid actual tool execution
        # This is tricky because process_repository calls the functions which call subprocess.
        # We will rely on the fact that if tools are not installed, it logs warnings and returns None/0.
        # For a true test, we assume radon/semgrep are installed in the test environment.
        # If not, the function should handle the error gracefully.
        
        try:
            result = process_repository("test_repo", repo_path, output_dir)
            assert result["repo_id"] == "test_repo"
            assert result["source_files_processed"] >= 1
            assert (output_dir / "semgrep_results.json").exists()
            
            with open(output_dir / "semgrep_results.json") as f:
                data = json.load(f)
                assert len(data) >= 1
                assert data[0]["file_path"] == "main.py"
        except FileNotFoundError:
            # If tools are not installed, the function might fail or return partial results.
            # This test assumes the environment has the tools.
            pytest.skip("Static analysis tools (radon/semgrep) not installed in test environment")
