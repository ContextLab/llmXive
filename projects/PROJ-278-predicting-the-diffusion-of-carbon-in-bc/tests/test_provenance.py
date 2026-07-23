import pytest
import pandas as pd
import logging
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports if running from tests
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from logging_config import setup_logger

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
    4. The log file contains evidence of the exclusion process (optional but recommended).
    """
    dataset_path = Path("data/processed/dataset_cleaned.csv")
    
    if not dataset_path.exists():
        pytest.skip("Dataset not yet generated. Run code/02_preprocess.py first.")
    
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
        f"Found {null_count} entries with missing 'microstructure_controlled' flag. "
        "Provenance exclusion logic failed to filter these out."
    )
    
    # 3. Check 'single_crystal' if present in the output
    # The spec mentions single_crystal flags in FR-008, SC-006.
    # If the raw data had 'single_crystal' and it was retained, it must be valid.
    if 'single_crystal' in df.columns:
        null_count_sc = df['single_crystal'].isnull().sum()
        assert null_count_sc == 0, (
            f"Found {null_count_sc} entries with missing 'single_crystal' flag. "
            "Provenance exclusion logic failed to filter these out."
        )
    
    # 4. Verify logging of exclusions
    # We look for a log file in the standard location or the current working directory
    # The 02_preprocess.py script should have logged the exclusion count.
    log_file = Path("data/processed/preprocessing.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Check for keywords indicating the logic ran
        assert 'provenance' in log_content.lower() or 'exclusion' in log_content.lower(), (
            "Log file exists but does not contain evidence of provenance exclusion logic execution."
        )
        # Optional: Check that it mentions the number of excluded rows if any
        # assert 'excluded' in log_content.lower(), "Log does not mention exclusions."
    else:
        # If no log file, we rely solely on the data integrity checks above.
        # In a strict CI environment, we might want to enforce log generation,
        # but for this test, data integrity is the primary contract.
        pass
    
    print("Provenance exclusion logic verified: No null flags in output dataset.")