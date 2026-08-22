import os
import json
import tempfile
import subprocess
from pathlib import Path
import pytest

# Import the functions we want to test
# Note: We mock the subprocess calls to avoid needing real tools installed in test env
from code.run_metrics_collection import calculate_loc_via_cloc, calculate_cc_via_radon, collect_metrics

class TestMetricsCollection:
    def test_calculate_loc_via_cloc_mock(self, monkeypatch):
        """Test LOC calculation with mocked cloc output."""
        mock_output = {
            "SUM": {
                "code": 150,
                "blank": 20,
                "comment": 10
            }
        }
        
        def mock_run(*args, **kwargs):
            class Result:
                stdout = json.dumps(mock_output)
                stderr = ""
                returncode = 0
            return Result()
        
        monkeypatch.setattr(subprocess, 'run', mock_run)
        
        # Create a dummy path
        dummy_path = Path("/fake/path")
        
        result = calculate_loc_via_cloc(dummy_path)
        
        assert result['status'] == 'success'
        assert result['total_loc'] == 150
        assert result['raw_data']['code'] == 150

    def test_calculate_cc_via_radon_mock(self, monkeypatch):
        """Test CC calculation with mocked radon output."""
        # Mock radon output: file:line:name - CC
        mock_stdout = """src/main.py:10:main - 5
src/main.py:25:helper - 3
src/utils.py:5:util_func - 2"""
        
        def mock_run(*args, **kwargs):
            class Result:
                stdout = mock_stdout
                stderr = ""
                returncode = 0
            return Result()
        
        monkeypatch.setattr(subprocess, 'run', mock_run)
        
        dummy_path = Path("/fake/path")
        
        result = calculate_cc_via_radon(dummy_path)
        
        assert result['status'] == 'success'
        assert result['function_count'] == 3
        # Average of 5, 3, 2 is 3.33
        assert abs(result['avg_cyclomatic_complexity'] - 3.33) < 0.01

    def test_collect_metrics_creates_file(self, monkeypatch, tmp_path):
        """Test that collect_metrics writes the output file."""
        mock_loc = {'total_loc': 100, 'status': 'success'}
        mock_cc = {'avg_cyclomatic_complexity': 2.0, 'function_count': 1, 'status': 'success'}
        
        def mock_loc_calc(*args): return mock_loc
        def mock_cc_calc(*args): return mock_cc
        
        monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: type('R', (), {'stdout': '{}', 'stderr': '', 'returncode': 0})())
        # Override the specific functions to avoid subprocess dependency in this simple test
        import code.run_metrics_collection as mod
        orig_loc = mod.calculate_loc_via_cloc
        orig_cc = mod.calculate_cc_via_radon
        mod.calculate_loc_via_cloc = mock_loc_calc
        mod.calculate_cc_via_radon = mock_cc_calc

        try:
            repos = [{'repo_name': 'test_repo', 'path': str(tmp_path)}]
            output_file = tmp_path / "metrics.json"
            
            collect_metrics(repos, output_file)
            
            assert output_file.exists()
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]['repo_name'] == 'test_repo'
            assert data[0]['status'] == 'success'
        finally:
            mod.calculate_loc_via_cloc = orig_loc
            mod.calculate_cc_via_radon = orig_cc