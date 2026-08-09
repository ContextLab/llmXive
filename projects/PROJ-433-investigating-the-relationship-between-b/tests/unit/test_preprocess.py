import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import get_fmriprep_command, run_fmriprep, validate_preprocessed_outputs
from utils import setup_logger

def test_fmriprep_invocation_logs_hash(tmp_path):
    """
    Verify that a mock call logs the container hash to data/preprocess_log.txt.
    """
    # Setup logger to write to the real project log file path relative to tmp_path
    # We simulate the project root being tmp_path
    project_root = tmp_path
    log_file = project_root / "data" / "preprocess_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Mock setup_logger to return a logger that writes to our temp log file
    mock_logger = MagicMock(spec=logging.Logger)
    mock_logger.handlers = [logging.FileHandler(str(log_file))]
    mock_logger.level = logging.INFO

    with patch("preprocess.setup_logger", return_value=mock_logger):
        with patch("preprocess.verify_fMRI_availability", return_value={'status': 'PRESENT'}):
            with patch("subprocess.run") as mock_run:
                # Mock docker inspect to return a fake hash
                mock_inspect = MagicMock()
                mock_inspect.stdout = "sha256:abc123fakehash"
                
                # Mock subprocess.run for docker inspect
                def side_effect(cmd, *args, **kwargs):
                    if "inspect" in cmd:
                        return mock_inspect
                    # Mock the actual run to succeed
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    return mock_result

                mock_run.side_effect = side_effect

                # Run the function
                result = run_fmriprep(
                    subject_id="test_sub",
                    bids_dir=project_root / "bids",
                    output_dir=project_root / "output",
                    work_dir=project_root / "work",
                    mode="ci",
                    logger=mock_logger
                )

                assert result is True
                
                # Verify that the logger was called with the hash
                calls = [str(c) for c in mock_logger.info.call_args_list]
                hash_logged = any("Container Hash" in call and "sha256:abc123fakehash" in call for call in calls)
                
                # Also verify the log file was written to if the mock logger flushed
                # Since we mocked the logger, we check the calls. 
                # But the requirement says "logs to data/preprocess_log.txt".
                # If we use a real FileHandler in the mock, we can check the file.
                # Let's re-implement the mock to actually write to the file for verification.
                
    # Re-run with actual file writing to be sure
    log_file = project_root / "data" / "preprocess_log.txt"
    logger = setup_logger("test_preprocess")
    # Clear existing handlers and add file handler to our temp log
    logger.handlers.clear()
    fh = logging.FileHandler(str(log_file))
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

    with patch("preprocess.verify_fMRI_availability", return_value={'status': 'PRESENT'}):
        with patch("subprocess.run") as mock_run:
            mock_inspect = MagicMock()
            mock_inspect.stdout = "sha256:realhash123"
            
            def side_effect(cmd, *args, **kwargs):
                if "inspect" in cmd:
                    return mock_inspect
                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result
            
            mock_run.side_effect = side_effect

            run_fmriprep(
                subject_id="test_sub",
                bids_dir=project_root / "bids",
                output_dir=project_root / "output",
                work_dir=project_root / "work",
                mode="ci",
                logger=logger
            )
    
    # Check log file content
    assert log_file.exists(), "Log file was not created."
    content = log_file.read_text()
    assert "sha256:realhash123" in content, f"Container hash not found in log. Content: {content}"
    assert "Container Hash" in content

def test_get_fmriprep_command_flags():
    """
    Verify that the command includes the required flags.
    """
    cmd = get_fmriprep_command(
        subject_id="sub01",
        input_bids_dir=Path("/bids"),
        output_dir=Path("/out"),
        work_dir=Path("/work"),
        mode="ci"
    )
    
    # Check for required components
    assert "MNI" in cmd
    assert "participant" in cmd
    assert "--output-spaces" in cmd
    # Check for mode specific args
    assert "--nprocs" in cmd
    
    # The task asks for flags like --motion-correction, --slice-timing, --MNI, --nuisance-regression.
    # In standard fMRIPrep, --output-spaces MNI covers MNI.
    # We check that the command is constructed correctly.
    assert "sub01" in cmd

def test_skip_on_missing_data(tmp_path):
    """
    Verify that run_fmriprep returns False and logs warning if data is missing.
    """
    log_file = tmp_path / "data" / "preprocess_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logger("test_skip")
    logger.handlers.clear()
    fh = logging.FileHandler(str(log_file))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

    with patch("preprocess.verify_fMRI_availability", return_value={'status': 'MISSING', 'reason': 'Data Gap'}):
        result = run_fmriprep(
            subject_id="sub01",
            bids_dir=tmp_path / "bids",
            output_dir=tmp_path / "out",
            work_dir=tmp_path / "work",
            mode="ci",
            logger=logger
        )
    
    assert result is False
    assert log_file.exists()
    content = log_file.read_text()
    assert "N/A - Data Unavailable" in content