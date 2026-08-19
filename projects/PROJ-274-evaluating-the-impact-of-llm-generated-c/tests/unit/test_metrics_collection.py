"""
Unit tests for T021c metric collection logic.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

# We test the logic functions directly by importing them or mocking subprocess
# Since the script is standalone, we test the helper functions if we extract them,
# or we test the integration by mocking the subprocess calls.

# For this task, we will test the logic by mocking subprocess.run
from unittest.mock import patch, MagicMock
import code.run_metrics_collection as metrics_module

def test_check_dependencies_exists():
    """Test that check_dependencies passes when tools exist."""
    with patch('shutil.which', return_value=True):
        # Should not raise
        metrics_module.check_dependencies()

def test_check_dependencies_missing():
    """Test that check_dependencies raises when tools are missing."""
    with patch('shutil.which', return_value=None):
        with pytest.raises(RuntimeError) as exc_info:
            metrics_module.check_dependencies()
        assert "radon" in str(exc_info.value) or "cloc" in str(exc_info.value)

def test_calculate_loc_via_cloc():
    """Test LOC calculation parsing."""
    mock_json_output = json.dumps({
        "sum": {"code": 150, "comment": 20, "blank": 10},
        "lang": {"Python": {"code": 150}}
    })
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_json_output)
        loc = metrics_module.calculate_loc_via_cloc("/fake/path")
        assert loc == 150
        mock_run.assert_called_once()

def test_calculate_cc_via_radon():
    """Test CC calculation parsing."""
    mock_radon_output = "Average CC: 2.5\n"
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_radon_output)
        cc = metrics_module.calculate_cc_via_radon("/fake/path")
        assert cc == 2.5

def test_collect_metrics_integration():
    """Test the full collection flow on a temp dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy python file to make radon/cloc happy
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("def hello():\n    pass\n")
        
        # We cannot easily mock subprocess inside collect_metrics without patching the module's subprocess
        # So we rely on the fact that if the dir exists, it tries to run.
        # For a robust unit test, we'd refactor collect_metrics to accept a 'runner' function.
        # Here we assume the environment has radon/cloc or we skip if not.
        try:
            metrics = metrics_module.collect_metrics(tmpdir)
            assert "path" in metrics
            assert "loc" in metrics
            assert "cc" in metrics
        except RuntimeError as e:
            if "Missing required dependencies" in str(e):
                pytest.skip("radon or cloc not installed in environment")
            raise