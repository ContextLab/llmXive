import pytest
import pandas as pd
import logging
import os
from pathlib import Path
import sys
import re

# Ensure the code directory is in the path for imports if running from tests
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from logging_config import setup_logger
from exceptions import DataInsufficientError

def test_provenance_exclusion_logic():
    """
    T013b: Validate provenance exclusion logic.
    Verify that entries missing microstructure_controlled or single_crystal flags
    are correctly excluded and logged in code/02_preprocess.py.
    
    This test assumes the preprocessing step has been run and checks the output.
    It verifies:
    1. The cleaned dataset exists.
    2. No rows in the cleaned dataset have null values for 'microstructure_controlled'.
    3. If 'single_crystal' exists in the output, it has no null values.
    4. The log file contains evidence of the exclusion process.
    """
    dataset_path = Path("data/processed/dataset_cleaned.csv")
    log_path = Path("data/processed/preprocessing.log")
    
    if not dataset_path.exists():
        pytest.fail(
            "Dataset 'data/processed/dataset_cleaned.csv' not found. "
            "Run 'python code/02_preprocess.py' to generate it before testing provenance."
        )
    
    df = pd.read_csv(dataset_path)
    
    # 1. Verify required column exists
    assert 'microstructure_controlled' in df.columns, (
        "Column 'microstructure_controlled' missing from cleaned dataset. "
        "The preprocessing step must enforce this column."
    )
    
    # 2. Verify no null values in 'microstructure_controlled'
    # This is the core of the provenance check: if an entry didn't have this flag,
    # it should have been excluded by enforce_provenance() in 02_preprocess.py.
    null_count = df['microstructure_controlled'].isnull().sum()
    assert null_count == 0, (
        f"Found {null_count} entries with missing 'microstructure_controlled' flag in the output. "
        "Provenance exclusion logic failed to filter these out. "
        "All rows in the final dataset must have valid provenance flags."
    )
    
    # 3. Check 'single_crystal' if present in the output
    # The spec mentions single_crystal flags in FR-008, SC-006.
    # If the raw data had 'single_crystal' and it was retained, it must be valid.
    if 'single_crystal' in df.columns:
        null_count_sc = df['single_crystal'].isnull().sum()
        assert null_count_sc == 0, (
            f"Found {null_count_sc} entries with missing 'single_crystal' flag in the output. "
            "Provenance exclusion logic failed to filter these out."
        )
    
    # 4. Verify logging of exclusions
    # We look for a log file in the standard location
    if log_path.exists():
        with open(log_path, 'r') as f:
            log_content = f.read()
        
        # Check for keywords indicating the logic ran
        # The 02_preprocess.py script should log the exclusion count and reason.
        has_provenance_log = 'provenance' in log_content.lower()
        has_exclusion_log = 'exclusion' in log_content.lower() or 'excluded' in log_content.lower()
        
        assert has_provenance_log or has_exclusion_log, (
            "Log file exists but does not contain evidence of provenance exclusion logic execution. "
            "Expected to find keywords like 'provenance', 'exclusion', or 'excluded'."
        )
    else:
        # If no log file, we rely solely on the data integrity checks above.
        # However, for a strict test of the *logging* aspect, we might want to fail if the log is missing
        # but the dataset exists (implying the script ran but didn't log).
        # Given the task is to validate the logic, and the logic is validated by the data state,
        # we pass if the data is clean, but note the missing log.
        # For this specific test T013b, we require the log to prove the *logging* part of the task.
        # If the log is missing, we cannot verify the logging requirement.
        # We will raise a warning or fail if the log is strictly required by the spec for this task.
        # Re-reading T013b: "verify that entries ... are correctly excluded AND logged".
        # So the log is required.
        pytest.fail(
            "Log file 'data/processed/preprocessing.log' not found. "
            "The preprocessing script must log provenance exclusions as per T013b requirements."
        )
    
    print("Provenance exclusion logic verified: No null flags in output dataset and logging confirmed.")

def test_provenance_exclusion_content():
    """
    Additional test to verify the specific content of the exclusion logic in the log.
    Ensures that the log explicitly mentions the fields being checked.
    """
    log_path = Path("data/processed/preprocessing.log")
    
    if not log_path.exists():
        # If the main test passes, this log should exist. If not, we skip to avoid duplicate failure.
        pytest.skip("Log file missing; main test should have caught this.")
    
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    # Check that the log mentions the specific fields required for provenance
    # FR-008 and SC-006 require checking 'microstructure_controlled' and 'single_crystal'
    mentions_microstructure = 'microstructure_controlled' in log_content
    mentions_single_crystal = 'single_crystal' in log_content
    
    # We expect at least one of them to be mentioned if the logic ran correctly
    assert mentions_microstructure or mentions_single_crystal, (
        "Log file does not explicitly mention the provenance fields ('microstructure_controlled' or 'single_crystal'). "
        "The logging implementation must reference the specific fields being validated."
    )
    
    print("Log content verified: Provenance fields explicitly mentioned in logs.")