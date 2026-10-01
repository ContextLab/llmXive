import json
import os
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Mock the environment for testing
def test_metadata_structure(tmp_path):
    """Test that the metadata file has the correct structure."""
    # Create a temporary merged CSV
    merged_csv = tmp_path / "data" / "raw" / "perovskites_merged.csv"
    merged_csv.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'formula': ['CsPbI3', 'MAPbBr3', 'FAPbI3'],
        'source': ['NREL', 'MaterialsProject', 'NREL'],
        'instrument_model': ['TA Instruments', None, 'Mettler Toledo'],
        'manufacturer': ['TA', None, 'Mettler']
    }
    df = pd.DataFrame(data)
    df.to_csv(merged_csv, index=False)
    
    # Create a fallback log
    fallback_log = tmp_path / "data" / "raw" / "instrumentation_fallbacks.log"
    fallback_log.parent.mkdir(parents=True, exist_ok=True)
    with open(fallback_log, 'w') as f:
        f.write("WARNING: Missing precision for MAPbBr3, defaulting to 10°C\n")
    
    # Change working directory to tmp_path to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Import and run the function
        # We need to adjust the import path or mock it
        # For this test, we will simulate the logic
        
        from code.write_metadata import load_merged_perovskites, process_metadata_entries, validate_metadata_structure
        
        records = load_merged_perovskites()
        metadata_list = process_metadata_entries(records)
        
        assert validate_metadata_structure(metadata_list)
        
        # Check specific entries
        # CsPbI3: Has model -> source -> precision_from_registry=True (or source)
        # MAPbBr3: No model, in fallback log -> default -> precision_from_registry=False
        # FAPbI3: Has model -> source -> precision_from_registry=True
        
        cs_entry = next(m for m in metadata_list if m['formula'] == 'CsPbI3')
        map_entry = next(m for m in metadata_list if m['formula'] == 'MAPbBr3')
        fa_entry = next(m for m in metadata_list if m['formula'] == 'FAPbI3')
        
        assert cs_entry['precision_from_registry'] == True # Or source
        assert cs_entry['precision_source'] == 'source'
        
        assert map_entry['precision_from_registry'] == False
        assert map_entry['precision_source'] == 'default'
        
        assert fa_entry['precision_from_registry'] == True
        assert fa_entry['precision_source'] == 'source'
        
    finally:
        os.chdir(original_cwd)
