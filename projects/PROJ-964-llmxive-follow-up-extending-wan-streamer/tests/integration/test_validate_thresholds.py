"""
Integration test for T012b: Validate Thresholds & Event Count
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import yaml
from pathlib import Path
import subprocess

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_validate_thresholds_success():
    """Test successful validation when event count >= 500."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock data with >= 500 events
        data_dir = tmpdir / 'data' / 'processed'
        data_dir.mkdir(parents=True)
        
        # Create a dataframe with 600 interruption events and 100 pause events
        n_rows = 1000
        df = pd.DataFrame({
            'is_interruption': [True] * 600 + [False] * 400,
            'is_pause': [True] * 100 + [False] * 900,
            'timestamp': range(n_rows),
            'latent_delta_magnitude': [0.6] * 600 + [0.1] * 400
        })
        
        parquet_path = data_dir / 'raw_extract.parquet'
        df.to_parquet(parquet_path)
        
        # Create thresholds config
        config_dir = tmpdir / 'code' / 'config'
        config_dir.mkdir(parents=True)
        config_path = config_dir / 'detection_thresholds.yaml'
        thresholds = {
            'audio_energy_db': -30.0,
            'latent_delta_magnitude': 0.5,
            'pause_duration_frames': 10,
            'calibration_status': 'pending'
        }
        with open(config_path, 'w') as f:
            yaml.dump(thresholds, f)
        
        # Run validation
        log_path = tmpdir / 'data' / 'logs' / 'threshold_validation.log'
        log_path.parent.mkdir(parents=True)
        
        result = subprocess.run([
            sys.executable,
            str(Path(__file__).parent.parent.parent / 'code' / 'tasks' / 'validate_thresholds.py'),
            '--data-path', str(parquet_path),
            '--thresholds-path', str(config_path),
            '--log-path', str(log_path)
        ], capture_output=True, text=True)
        
        # Verify exit code is 0
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. Stderr: {result.stderr}"
        
        # Verify log file exists and contains correct count
        assert log_path.exists(), "Log file not created"
        log_content = log_path.read_text()
        assert "Event count: 700" in log_content, f"Expected 'Event count: 700' in log, got: {log_content}"
        assert "Validation PASSED" in log_content, f"Expected 'Validation PASSED' in log, got: {log_content}"

def test_validate_thresholds_failure():
    """Test validation fails when event count < 500."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock data with < 500 events
        data_dir = tmpdir / 'data' / 'processed'
        data_dir.mkdir(parents=True)
        
        # Create a dataframe with only 200 events total
        n_rows = 1000
        df = pd.DataFrame({
            'is_interruption': [True] * 150 + [False] * 850,
            'is_pause': [True] * 50 + [False] * 950,
            'timestamp': range(n_rows),
            'latent_delta_magnitude': [0.6] * 150 + [0.1] * 850
        })
        
        parquet_path = data_dir / 'raw_extract.parquet'
        df.to_parquet(parquet_path)
        
        # Create thresholds config
        config_dir = tmpdir / 'code' / 'config'
        config_dir.mkdir(parents=True)
        config_path = config_dir / 'detection_thresholds.yaml'
        thresholds = {
            'audio_energy_db': -30.0,
            'latent_delta_magnitude': 0.5,
            'pause_duration_frames': 10
        }
        with open(config_path, 'w') as f:
            yaml.dump(thresholds, f)
        
        # Run validation
        log_path = tmpdir / 'data' / 'logs' / 'threshold_validation.log'
        log_path.parent.mkdir(parents=True)
        
        result = subprocess.run([
            sys.executable,
            str(Path(__file__).parent.parent.parent / 'code' / 'tasks' / 'validate_thresholds.py'),
            '--data-path', str(parquet_path),
            '--thresholds-path', str(config_path),
            '--log-path', str(log_path)
        ], capture_output=True, text=True)
        
        # Verify exit code is non-zero
        assert result.returncode != 0, f"Expected non-zero exit code, got {result.returncode}"
        
        # Verify log file contains error
        assert log_path.exists(), "Log file not created"
        log_content = log_path.read_text()
        assert "Event count: 200" in log_content, f"Expected 'Event count: 200' in log, got: {log_content}"
        assert "ERROR: insufficient events" in log_content, f"Expected error message in log, got: {log_content}"
        assert "Validation FAILED" in log_content, f"Expected 'Validation FAILED' in log, got: {log_content}"

def test_validate_thresholds_missing_file():
    """Test validation fails when input file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create thresholds config
        config_dir = tmpdir / 'code' / 'config'
        config_dir.mkdir(parents=True)
        config_path = config_dir / 'detection_thresholds.yaml'
        thresholds = {'audio_energy_db': -30.0}
        with open(config_path, 'w') as f:
            yaml.dump(thresholds, f)
        
        # Run validation with non-existent data path
        log_path = tmpdir / 'data' / 'logs' / 'threshold_validation.log'
        log_path.parent.mkdir(parents=True)
        
        result = subprocess.run([
            sys.executable,
            str(Path(__file__).parent.parent.parent / 'code' / 'tasks' / 'validate_thresholds.py'),
            '--data-path', str(tmpdir / 'nonexistent.parquet'),
            '--thresholds-path', str(config_path),
            '--log-path', str(log_path)
        ], capture_output=True, text=True)
        
        # Verify exit code is non-zero
        assert result.returncode != 0, f"Expected non-zero exit code, got {result.returncode}"
        assert "File not found" in result.stderr or "File not found" in result.stdout

if __name__ == '__main__':
    test_validate_thresholds_success()
    print("✓ test_validate_thresholds_success passed")
    
    test_validate_thresholds_failure()
    print("✓ test_validate_thresholds_failure passed")
    
    test_validate_thresholds_missing_file()
    print("✓ test_validate_thresholds_missing_file passed")
    
    print("\nAll integration tests passed!")