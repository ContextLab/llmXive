"""
Integration test for preprocessing pipeline (T011).

This test verifies that the preprocessing pipeline (T013) produces valid epochs
labeled "standard" and "deviant" and logs rejected epochs.

EXPECTED STATE: This test is expected to FAIL until T013 (code/preprocess.py) is implemented.
It checks for the existence of the output file and validates its contents.
"""
import os
import pytest
from pathlib import Path
import mne

# Project root relative to tests/integration
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
PREPROCESS_LOG = RESULTS_DIR / "preprocess_log.txt"

# Expected output paths as defined in T013
EXPECTED_EPOCHS_FILE = DATA_PROCESSED / "epo.fif"
EXPECTED_LOG_FILE = PREPROCESS_LOG

@pytest.mark.integration
def test_preprocess_pipeline_output_exists():
    """
    Test that the preprocessing pipeline produces the expected output file.
    
    This will fail with FileNotFoundError if T013 has not been run or failed.
    """
    assert EXPECTED_EPOCHS_FILE.exists(), (
        f"Preprocessing output {EXPECTED_EPOCHS_FILE} not found. "
        "Has code/preprocess.py (T013) been executed successfully?"
    )

@pytest.mark.integration
def test_preprocess_epochs_valid_structure():
    """
    Test that the output epochs file contains valid MNE epochs with required conditions.
    """
    # Skip if file doesn't exist yet (graceful failure for pre-implementation state)
    if not EXPECTED_EPOCHS_FILE.exists():
        pytest.skip("Preprocessing output not yet generated. Run T013 first.")

    try:
        epochs = mne.read_epochs(str(EXPECTED_EPOCHS_FILE), preload=False)
    except Exception as e:
        pytest.fail(f"Failed to read epochs file: {e}")

    # Verify conditions exist
    assert "standard" in epochs.event_id, "Missing 'standard' condition in epochs."
    assert "deviant" in epochs.event_id, "Missing 'deviant' condition in epochs."

    # Verify basic properties
    assert epochs.get_data().shape[0] > 0, "Epochs array is empty."
    assert epochs.get_data().shape[2] > 0, "Epochs have no time points."

@pytest.mark.integration
def test_preprocess_log_exists():
    """
    Test that the preprocessing log file exists and contains expected format.
    """
    if not EXPECTED_LOG_FILE.exists():
        pytest.skip("Preprocessing log not yet generated. Run T013 first.")

    with open(EXPECTED_LOG_FILE, "r") as f:
        content = f.read()

    # Basic check that log has content
    assert len(content) > 0, "Preprocessing log is empty."
    
    # Check for expected log format pattern (from T017)
    # Pattern: "Subject {subject_id}: Rejected {count} epochs, Removed {ica_count} ICA components"
    import re
    pattern = r"Subject \w+: Rejected \d+ epochs, Removed \d+ ICA components"
    matches = re.findall(pattern, content)
    assert len(matches) > 0, (
        f"Log file does not contain expected format. "
        f"Expected pattern: 'Subject <id>: Rejected <n> epochs, Removed <m> ICA components'. "
        f"Content: {content[:200]}"
    )