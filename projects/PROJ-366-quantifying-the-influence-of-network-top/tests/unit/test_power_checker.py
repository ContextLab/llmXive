"""
Unit tests for the Statistical Power Check (T035).

Tests verify:
1. Correct counting of sample files.
2. Correct status assignment based on N.
3. Correct exit codes (1 for N<2, 0 otherwise).
4. Correct JSON output format.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code root to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from analysis.power_checker import count_valid_samples, main, write_power_analysis_report
from config import get_config, get_paths

def test_count_valid_samples_empty():
    """Test counting samples in an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        count = count_valid_samples(Path(tmpdir))
        assert count == 0

def test_count_valid_samples_with_files():
    """Test counting samples with mixed file types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        # Create sample files
        (d / "sample_01.pkl").touch()
        (d / "sample_02.pkl").touch()
        (d / "sample_03.json").touch()
        # Create a file that should be ignored
        (d / "convergence_report.json").touch()
        
        count = count_valid_samples(d)
        assert count == 3

def test_power_check_logic_n_less_than_2():
    """Test that N < 2 returns exit code 1 and FATAL status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "processed" / "conductivities"
        output_dir = Path(tmpdir) / "data" / "processed" / "model_outputs"
        data_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        
        # Mock config to return our temp dirs
        mock_config = MagicMock()
        mock_paths = {
            "data_root": Path(tmpdir) / "data",
            "conductivities": data_dir,
            "model_outputs": output_dir
        }
        
        with patch('analysis.power_checker.get_config') as mock_get_config, \
             patch('analysis.power_checker.get_paths') as mock_get_paths:
            
            mock_get_config.return_value = mock_config
            mock_get_paths.return_value = mock_paths
            
            # No files -> N=0
            exit_code = main()
            
            assert exit_code == 1
            
            # Verify report
            report_file = output_dir / "power_analysis.json"
            assert report_file.exists()
            with open(report_file) as f:
                report = json.load(f)
            assert report["status"] == "FATAL_INSUFFICIENT_DATA"
            assert report["sample_count"] == 0

def test_power_check_logic_n_between_2_and_10():
    """Test that 2 <= N < 10 returns exit code 0 and INSUFFICIENT_POWER status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "processed" / "conductivities"
        output_dir = Path(tmpdir) / "data" / "processed" / "model_outputs"
        data_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        
        # Create 5 sample files
        for i in range(5):
            (data_dir / f"sample_{i}.pkl").touch()
        
        mock_config = MagicMock()
        mock_paths = {
            "data_root": Path(tmpdir) / "data",
            "conductivities": data_dir,
            "model_outputs": output_dir
        }
        
        with patch('analysis.power_checker.get_config') as mock_get_config, \
             patch('analysis.power_checker.get_paths') as mock_get_paths:
            
            mock_get_config.return_value = mock_config
            mock_get_paths.return_value = mock_paths
            
            exit_code = main()
            
            assert exit_code == 0
            
            report_file = output_dir / "power_analysis.json"
            assert report_file.exists()
            with open(report_file) as f:
                report = json.load(f)
            assert report["status"] == "INSUFFICIENT_POWER"
            assert report["sample_count"] == 5

def test_power_check_logic_n_ge_10():
    """Test that N >= 10 returns exit code 0 and SUFFICIENT_POWER status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "processed" / "conductivities"
        output_dir = Path(tmpdir) / "data" / "processed" / "model_outputs"
        data_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        
        # Create 12 sample files
        for i in range(12):
            (data_dir / f"sample_{i}.pkl").touch()
        
        mock_config = MagicMock()
        mock_paths = {
            "data_root": Path(tmpdir) / "data",
            "conductivities": data_dir,
            "model_outputs": output_dir
        }
        
        with patch('analysis.power_checker.get_config') as mock_get_config, \
             patch('analysis.power_checker.get_paths') as mock_get_paths:
            
            mock_get_config.return_value = mock_config
            mock_get_paths.return_value = mock_paths
            
            exit_code = main()
            
            assert exit_code == 0
            
            report_file = output_dir / "power_analysis.json"
            assert report_file.exists()
            with open(report_file) as f:
                report = json.load(f)
            assert report["status"] == "SUFFICIENT_POWER"
            assert report["sample_count"] == 12
