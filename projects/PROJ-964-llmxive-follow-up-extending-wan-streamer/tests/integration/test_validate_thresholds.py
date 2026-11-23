"""
Integration test for T012b: Validate Thresholds & Event Count.

Verifies that:
1. The script runs successfully when event count >= 500.
2. The script exits with code 1 when event count < 500.
3. The log file is created with the correct format.
"""
import os
import sys
import tempfile
import subprocess
import shutil
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from tasks.validate_thresholds import load_thresholds, load_extracted_data, count_events, write_log, main

def test_count_events_interruptions():
    """Test interruption counting logic."""
    # Create a small dataframe with known interruptions
    data = {
        'audio_energy': [10.0, 20.0, 30.0, 5.0, 25.0], # 3 active speech frames
        'latent_delta_magnitude': [0.1, 0.6, 0.7, 0.8, 0.2] # 2 exceed 0.5
    }
    df = pd.DataFrame(data)
    
    thresholds = {
        'audio_energy_db': -30.0, # All are > -30, so all active
        'latent_delta_magnitude': 0.5,
        'pause_duration_frames': 10
    }
    
    count = count_events(df, thresholds)
    # Interruptions: rows 1, 2, 3 (indices) -> 3 interruptions? 
    # Wait: row 3 (index 3) has energy 5.0 which is >= -30.0, and delta 0.8 > 0.5.
    # So interruptions at indices 1, 2, 3. Total 3.
    # Pauses: none (no run of 10).
    assert count == 3, f"Expected 3 interruptions, got {count}"

def test_count_events_pauses():
    """Test pause counting logic."""
    # Create data with a run of silence longer than threshold
    # 15 frames of silence (< -30), 5 frames of speech
    n_silence = 15
    n_speech = 5
    silence_energy = -40.0
    speech_energy = 10.0
    
    energies = [silence_energy] * n_silence + [speech_energy] * n_speech
    deltas = [0.1] * len(energies) # Low deltas, no interruptions
    
    df = pd.DataFrame({
        'audio_energy': energies,
        'latent_delta_magnitude': deltas
    })
    
    thresholds = {
        'audio_energy_db': -30.0,
        'latent_delta_magnitude': 0.5,
        'pause_duration_frames': 10
    }
    
    count = count_events(df, thresholds)
    # 1 pause detected (run of 15 >= 10)
    assert count == 1, f"Expected 1 pause, got {count}"

def test_count_events_combined():
    """Test combined counting."""
    # 2 interruptions, 1 pause
    data = {
        'audio_energy': [10.0, 10.0] + [-40.0] * 12 + [10.0],
        'latent_delta_magnitude': [0.6, 0.6] + [0.1] * 12 + [0.1]
    }
    df = pd.DataFrame(data)
    
    thresholds = {
        'audio_energy_db': -30.0,
        'latent_delta_magnitude': 0.5,
        'pause_duration_frames': 10
    }
    
    count = count_events(df, thresholds)
    assert count == 3, f"Expected 3 events (2 interruptions + 1 pause), got {count}"

def test_script_success_path():
    """Test the script exits 0 when count >= 500."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create config
        config_path = tmpdir / "thresholds.yaml"
        config = {
            'audio_energy_db': -30.0,
            'latent_delta_magnitude': 0.5,
            'pause_duration_frames': 10
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Create data with >= 500 events
        # We need 500 interruptions or pauses.
        # Let's make 500 interruptions.
        n_events = 500
        energies = [10.0] * n_events
        deltas = [0.6] * n_events
        
        data_path = tmpdir / "raw_extract.parquet"
        df = pd.DataFrame({
            'audio_energy': energies,
            'latent_delta_magnitude': deltas
        })
        df.to_parquet(data_path)
        
        log_path = tmpdir / "threshold_validation.log"
        
        # Run script
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "code" / "tasks" / "validate_thresholds.py"),
                "--config", str(config_path),
                "--input", str(data_path),
                "--output", str(log_path),
                "--min-events", "500"
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert log_path.exists(), "Log file not created"
        
        with open(log_path, 'r') as f:
            content = f.read()
            assert "Event count: 500" in content
            assert "Validation status: PASS" in content

def test_script_failure_path():
    """Test the script exits 1 when count < 500."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create config
        config_path = tmpdir / "thresholds.yaml"
        config = {
            'audio_energy_db': -30.0,
            'latent_delta_magnitude': 0.5,
            'pause_duration_frames': 10
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Create data with < 500 events (e.g., 499)
        n_events = 499
        energies = [10.0] * n_events
        deltas = [0.6] * n_events
        
        data_path = tmpdir / "raw_extract.parquet"
        df = pd.DataFrame({
            'audio_energy': energies,
            'latent_delta_magnitude': deltas
        })
        df.to_parquet(data_path)
        
        log_path = tmpdir / "threshold_validation.log"
        
        # Run script
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "code" / "tasks" / "validate_thresholds.py"),
                "--config", str(config_path),
                "--input", str(data_path),
                "--output", str(log_path),
                "--min-events", "500"
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, f"Script should have exited with 1: {result.stdout}"
        assert log_path.exists(), "Log file not created"
        
        with open(log_path, 'r') as f:
            content = f.read()
            assert "Event count: 499" in content
            assert "ERROR: insufficient events" in content
            assert "Validation status: FAIL" in content

def test_missing_input_file():
    """Test handling of missing input file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        config_path = tmpdir / "thresholds.yaml"
        with open(config_path, 'w') as f:
            yaml.dump({'audio_energy_db': -30.0}, f)
        
        log_path = tmpdir / "threshold_validation.log"
        
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "code" / "tasks" / "validate_thresholds.py"),
                "--config", str(config_path),
                "--input", str(tmpdir / "nonexistent.parquet"),
                "--output", str(log_path)
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1
        assert log_path.exists()
        with open(log_path, 'r') as f:
            assert "File not found" in f.read()

if __name__ == "__main__":
    test_count_events_interruptions()
    test_count_events_pauses()
    test_count_events_combined()
    test_script_success_path()
    test_script_failure_path()
    test_missing_input_file()
    print("All tests passed.")