import pytest
import os
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if needed, though standard import assumes relative to code/
# We assume tests are run from root or code is in PYTHONPATH
try:
    from preprocess import main as preprocess_main
    from utils import ResourceMonitor
except ImportError:
    from code.preprocess import main as preprocess_main
    from code.utils import ResourceMonitor

@pytest.fixture
def mock_motion_log_zero_valid(tmp_path):
    """Create a motion_exclusion_log.csv where all subjects are excluded."""
    motion_log_path = tmp_path / "data" / "processed" / "motion_exclusion_log.csv"
    motion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = "subject_id,translation_mm,rotation_mm,excluded\n"
    content += "sub-01,4.5,2.1,True\n"
    content += "sub-02,3.2,1.8,True\n"
    content += "sub-03,5.0,3.0,True\n"
    
    motion_log_path.write_text(content)
    return str(motion_log_path)

@pytest.fixture
def mock_valid_subjects_json(tmp_path):
    """Create a valid_subjects.json file."""
    valid_path = tmp_path / "data" / "processed" / "valid_subjects.json"
    valid_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "subjects": [
            {"id": "sub-01", "score": 1.5},
            {"id": "sub-02", "score": 2.0},
            {"id": "sub-03", "score": 1.8}
        ],
        "count": 3
    }
    valid_path.write_text(json.dumps(data))
    return str(valid_path)

@pytest.fixture
def mock_processed_dir_empty(tmp_path):
    """Ensure the processed directory exists but is empty of preprocessed files."""
    proc_dir = tmp_path / "data" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    # Do not create any NIfTI files
    return str(proc_dir)

@pytest.mark.parametrize("env_vars", [
    {"FSLDIR": "/usr/share/fsl"},
    {"FSLDIR": "/usr/share/fsl", "AFNI_HOME": "/usr/lib/afni"}
])
def test_halt_on_zero_effective_subjects(
    env_vars, 
    mock_motion_log_zero_valid, 
    mock_valid_subjects_json, 
    mock_processed_dir_empty, 
    tmp_path,
    caplog
):
    """
    Test that preprocess.py halts with ValueError if motion exclusion results in 0 subjects.
    """
    # Set environment variables for FSL/AFNI check to pass (mocked later)
    for k, v in env_vars.items():
        os.environ[k] = v

    # Mock the run_command to avoid actual FSL calls
    with patch('preprocess.run_command') as mock_run:
        mock_run.return_value = (0, "", "")
        
        # Mock check_fsl_afni to return True
        with patch('preprocess.check_fsl_afni', return_value=True):
            # Mock ResourceMonitor to avoid actual RAM logging issues in test
            with patch('preprocess.ResourceMonitor') as MockMonitor:
                mock_monitor_instance = MagicMock()
                MockMonitor.return_value = mock_monitor_instance
                
                # Configure the script to use our temp paths
                # We need to patch the internal Path references or pass args if the script supports CLI
                # Based on typical implementation, we'll patch the internal logic that reads the CSV
                # However, the task requires the script to FAIL with a specific message.
                
                # Since main() usually runs end-to-end, we need to simulate the state
                # where valid_subjects.json exists, but motion_exclusion_log.csv excludes everyone.
                
                # We will patch the specific function that counts valid subjects after motion exclusion
                # to ensure we trigger the exact condition described in T016b.
                
                # Actually, let's just run the main logic but ensure the file paths are correct.
                # The task description implies the script reads `data/processed/motion_exclusion_log.csv`.
                # We need to make sure the script runs in the context of our temp_dir.
                
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmp_path)
                    # Ensure data/processed exists relative to cwd
                    (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
                    
                    # The mock fixtures created files in tmp_path, but we need them in tmp_path/data/processed
                    # The fixtures already created them in tmp_path / "data" / "processed"
                    
                    # Now run main. We expect it to raise ValueError.
                    with pytest.raises(ValueError) as excinfo:
                        preprocess_main()
                    
                    assert "No valid subjects remaining after motion exclusion" in str(excinfo.value)
                    
                    # Verify log file creation (optional but good practice)
                    # The task says "Log event to data/processed/pipeline_errors.log"
                    # We check if the error was logged or the exception was raised as primary verification.
                    # The exception is the primary verification per task description.
                    
                finally:
                    os.chdir(original_cwd)

def test_halt_message_exact_match(mock_motion_log_zero_valid, mock_valid_subjects_json, mock_processed_dir_empty, tmp_path):
    """
    Verify the exact error message string matches the requirement.
    """
    os.environ['FSLDIR'] = '/usr/share/fsl'
    
    with patch('preprocess.run_command', return_value=(0, "", "")):
        with patch('preprocess.check_fsl_afni', return_value=True):
            with patch('preprocess.ResourceMonitor'):
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmp_path)
                    (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
                    
                    with pytest.raises(ValueError) as excinfo:
                        preprocess_main()
                    
                    error_msg = str(excinfo.value)
                    expected_msg = "No valid subjects remaining after motion exclusion"
                    
                    assert error_msg == expected_msg, f"Expected '{expected_msg}', got '{error_msg}'"
                finally:
                    os.chdir(original_cwd)
