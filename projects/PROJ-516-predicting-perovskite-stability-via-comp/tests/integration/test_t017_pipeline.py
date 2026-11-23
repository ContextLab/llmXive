"""
Integration test for T017: End-to-end execution of finalize_descriptors.
Verifies that the script runs, produces the output file, and updates the state.
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Adjust import path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from finalize_descriptors import main, DESCRIPTORS_INPUT_PATH, UNCERTAINTY_FLAGS_PATH, FINAL_OUTPUT_PATH, STATE_FILE_PATH

@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure to simulate the project environment."""
    temp_dir = tempfile.mkdtemp()
    temp_code = Path(temp_dir) / "code"
    temp_data = Path(temp_dir) / "data"
    temp_state = Path(temp_dir) / "state"
    
    temp_data_raw = temp_data / "raw"
    temp_data_processed = temp_data / "processed"
    
    temp_code.mkdir(parents=True)
    temp_data_raw.mkdir(parents=True)
    temp_data_processed.mkdir(parents=True)
    temp_state.mkdir(parents=True)
    
    # Create dummy input files
    descriptors_df = pd.DataFrame({
        'id': [1, 2, 3],
        'formula': ['ABX3', 'CDY4', 'EFZ5'],
        'T_d': [500, 600, 700],
        'atomic_fraction_A': [0.2, 0.3, 0.4],
        'weighted_ionic_radius': [1.2, 1.3, 1.4]
    })
    descriptors_csv = temp_data_processed / "descriptors.csv"
    descriptors_df.to_csv(descriptors_csv, index=False)
    
    uncertainty_flags = [
        {'id': 1, 'T_d_uncertainty': 5.0},
        {'id': 2, 'T_d_uncertainty': 10.0},
        {'id': 3, 'T_d_uncertainty': 10.0}
    ]
    flags_json = temp_data_raw / "uncertainty_flags.json"
    with open(flags_json, 'w') as f:
        json.dump(uncertainty_flags, f)
    
    # Create empty state file
    state_yaml = temp_state / "artifacts.yaml"
    state_yaml.write_text("artifacts: {}\n")
    
    # Patch the module-level paths
    with patch('finalize_descriptors.PROJECT_ROOT', Path(temp_dir)), \
         patch('finalize_descriptors.DATA_DIR', temp_data), \
         patch('finalize_descriptors.PROCESSED_DIR', temp_data_processed), \
         patch('finalize_descriptors.RAW_DIR', temp_data_raw), \
         patch('finalize_descriptors.STATE_DIR', temp_state), \
         patch('finalize_descriptors.DESCRIPTORS_INPUT_PATH', descriptors_csv), \
         patch('finalize_descriptors.UNCERTAINTY_FLAGS_PATH', flags_json), \
         patch('finalize_descriptors.FINAL_OUTPUT_PATH', temp_data_processed / "descriptors.csv"), \
         patch('finalize_descriptors.STATE_FILE_PATH', state_yaml):
        
        yield {
            'temp_dir': temp_dir,
            'descriptors_csv': descriptors_csv,
            'flags_json': flags_json,
            'output_csv': temp_data_processed / "descriptors.csv",
            'state_file': state_yaml
        }
    
    shutil.rmtree(temp_dir)

def test_t017_integration(temp_project_structure):
    """Run T017 and verify the output."""
    # Run the main function
    main()
    
    # Verify output file exists
    assert temp_project_structure['output_csv'].exists(), "Final descriptors.csv was not created."
    
    # Verify content
    df = pd.read_csv(temp_project_structure['output_csv'])
    assert 'T_d_uncertainty' in df.columns, "T_d_uncertainty column is missing."
    assert len(df) == 3, "Row count mismatch."
    assert df.loc[df['id'] == 1, 'T_d_uncertainty'].values[0] == 5.0
    
    # Verify state file updated
    assert temp_project_structure['state_file'].exists(), "State file was not updated."
    import yaml
    with open(temp_project_structure['state_file'], 'r') as f:
        state = yaml.safe_load(f)
    
    assert 'artifacts' in state
    assert 'descriptors.csv' in state['artifacts']
    assert 'hash' in state['artifacts']['descriptors.csv']