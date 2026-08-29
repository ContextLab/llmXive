"""
Contract test for T086: Validate Participant entity.

Ensures that `data/processed/anonymised_ratings.csv` contains a non-null
`participant_id` column matching the Participant schema.
"""
import csv
import os
import pytest
from pathlib import Path
from config import get_processed_data_dir
from code.logging_config import setup_logging, get_logger

# Re-import the validation logic for direct testing if needed, 
# though the main check is via the script's exit code or file inspection.
# Here we verify the file content directly to ensure the test is robust.
from code import config
from code import logging_config

@pytest.fixture(autouse=True)
def setup_logs(tmp_path):
    # Ensure logging is setup but directed somewhere safe for tests if needed
    # The main validation logic writes to the project log, which is fine.
    pass

def test_t086_participant_id_column_exists_and_valid():
    """
    Verify that anonymised_ratings.csv exists, has the participant_id column,
    and all values are non-null and match the hash pattern.
    """
    processed_dir = get_processed_data_dir()
    input_path = processed_dir / "anonymised_ratings.csv"
    
    # Check file existence
    assert input_path.exists(), f"File {input_path} does not exist. T051 (anonymisation) may not have run."
    
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check headers
        assert reader.fieldnames is not None, "CSV file is empty."
        assert 'participant_id' in reader.fieldnames, \
            f"Missing 'participant_id' column. Found: {reader.fieldnames}"
        
        rows = list(reader)
        assert len(rows) > 0, "No data rows found in anonymised_ratings.csv."
        
        import re
        pattern = re.compile(r'^[a-f0-9]{32,64}$')
        
        null_count = 0
        invalid_count = 0
        
        for i, row in enumerate(rows):
            pid = row.get('participant_id')
            
            if pid is None or pid.strip() == '':
                null_count += 1
            elif not pattern.match(pid.strip()):
                invalid_count += 1
        
        assert null_count == 0, \
            f"Found {null_count} rows with null/empty 'participant_id'."
        assert invalid_count == 0, \
            f"Found {invalid_count} rows with malformed 'participant_id'."