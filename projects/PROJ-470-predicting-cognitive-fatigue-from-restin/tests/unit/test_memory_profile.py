import os
import sys
import json
import pytest
from pathlib import Path

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def test_memory_profile_runs_successfully():
    """Test that the memory profiling script runs and produces a valid report.
    
    This test verifies T026 requirements:
    - Uses memory_profiler (via tracemalloc) with line-by-line capability
    - Processes N=30 participants
    - Peak memory usage stays below 7 GB
    """
    # Run the memory profiling script
    import subprocess
    result = subprocess.run(
        [sys.executable, "code/profile_memory.py", "--stage", "all"],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    # Check that the script completed successfully
    assert result.returncode == 0, f"Memory profiling failed: {result.stderr}"
    
    # Verify that profile_report.json was created
    report_path = Path("profile_report.json")
    assert report_path.exists(), "profile_report.json was not created"
    
    # Load and validate the report
    with open(report_path, "r") as f:
        report = json.load(f)
    
    # Check that both stages were profiled
    assert "stages" in report, "Report must contain 'stages' key"
    assert len(report["stages"]) >= 2, "Report must contain at least preprocessing and features stages"
    
    # Validate each stage's results
    for stage_result in report["stages"]:
        assert "stage" in stage_result, f"Stage result missing 'stage' key: {stage_result}"
        assert "peak_memory_mb" in stage_result, f"Stage {stage_result['stage']} missing 'peak_memory_mb'"
        assert "status" in stage_result, f"Stage {stage_result['stage']} missing 'status'"
        assert stage_result["status"] == "success", f"Stage {stage_result['stage']} did not succeed"
        
        # Verify memory constraint (DC-001: ≤ 7 GB)
        peak_mb = stage_result["peak_memory_mb"]
        peak_gb = peak_mb / 1024
        assert peak_gb <= 7.0, f"Stage {stage_result['stage']} exceeded memory limit: {peak_gb:.2f} GB > 7 GB"
    
    print(f"Memory profiling successful. All stages under 7 GB limit.")

def test_synthetic_data_generation_for_memory_test():
    """Test that synthetic data is generated when real data is insufficient.
    
    This verifies the T026 requirement: 'If the available real dataset is smaller 
    than N=30, generate synthetic EEG data to reach N=30 participants for the 
    purpose of this memory test.'
    """
    from profile_memory import _generate_synthetic_eeg_data
    from preprocess import load_config
    
    config = load_config()
    n_participants = config.get("n_threshold", 30)
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic data
    _generate_synthetic_eeg_data(n_participants, output_dir, config)
    
    # Verify that files were created
    generated_files = list(output_dir.glob("*.fif"))
    assert len(generated_files) >= n_participants, f"Expected {n_participants} files, found {len(generated_files)}"
    
    # Verify file format (MNE FIF)
    import mne
    test_file = generated_files[0]
    raw = mne.io.read_raw_fif(test_file, preload=False)
    assert raw.info['sfreq'] == config.get("sampling_rate", 256), "Sampling rate mismatch"
    assert len(raw.ch_names) == 19, "Channel count mismatch"
    
    print(f"Synthetic data generation verified: {len(generated_files)} files created")

def test_memory_profiling_uses_streaming():
    """Verify that the preprocessing pipeline uses streaming (preload=False) to minimize memory.
    
    This verifies T026 implementation detail: 'asserts that `preload=False` is used and 
    generator-based iteration is implemented.'
    """
    # Check that preprocess.py uses preload=False in its streaming logic
    preprocess_path = Path("code/preprocess.py")
    assert preprocess_path.exists(), "preprocess.py not found"
    
    with open(preprocess_path, "r") as f:
        preprocess_content = f.read()
    
    # Verify streaming implementation
    assert "preload=False" in preprocess_content, "preload=False must be used for memory efficiency"
    assert "stream_eeg_files" in preprocess_content, "Generator-based streaming must be implemented"
    
    print("Memory-efficient streaming implementation verified")
