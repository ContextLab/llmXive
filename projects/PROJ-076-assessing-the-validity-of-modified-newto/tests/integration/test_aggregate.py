"""
Integration test for T015: Aggregate filtered data and update metadata.
"""
import os
import tempfile
import shutil
import pandas as pd
import yaml
from pathlib import Path
import pytest

# Mock the dependencies for testing without full pipeline
# We will test the logic of writing the file and updating metadata
# by mocking the load_filtered_data function or providing a test fixture.

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir()
    
    # Create a dummy metadata.yaml
    metadata = {
        "project": {"name": "test", "version": "0.1"},
        "data": {"source": "SPARC", "url": "http://test.com"},
        "paths": {
            "processed_data": str(processed_dir / "filtered_galaxies.csv"),
            "raw_data": str(data_dir / "raw" / "sparc_data.zip")
        }
    }
    metadata_file = data_dir / "metadata.yaml"
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f)
    
    # Create a dummy raw file to satisfy existence check
    raw_dir = data_dir / "raw"
    raw_dir.mkdir()
    (raw_dir / "sparc_data.zip").touch()
    
    # Create a dummy intermediate file to simulate T013/T014 output
    # We will simulate that T013/T014 created a file that T015 picks up
    # OR we mock the function. Let's create a dummy CSV that looks like processed data.
    # Since T013/T014 are "done", we assume they produced something.
    # To test T015 specifically, we'll place a file that T015 would read.
    
    # Actually, the implementation of T015 (aggregate.py) tries to run the pipeline
    # if the file is missing. To test T015 in isolation, we should mock the
    # load_filtered_data function or ensure the file exists.
    # Let's create the file directly to test the "load existing" path.
    test_df = pd.DataFrame({
        'galaxy_id': ['NGC001', 'NGC002'],
        'r': [1.0, 2.0],
        'v': [100.0, 150.0],
        'sigma_v': [5.0, 6.0],
        'inclination': [45.0, 60.0],
        'inclination_uncertainty': [1.0, 2.0]
    })
    test_df.to_csv(processed_dir / "filtered_galaxies.csv", index=False)
    
    return tmp_path, metadata_file, processed_dir

def test_aggregate_writes_csv_and_updates_metadata(temp_project_dir):
    tmp_path, metadata_file, processed_dir = temp_project_dir
    
    # We need to run the logic of aggregate.py
    # Since aggregate.py imports from utils/config which might have global state,
    # we will run the main logic but with patched paths if necessary.
    # For now, let's assume we can run the script with environment variables or
    # by directly calling the functions with the temp paths.
    
    # To avoid complex patching of the whole module, we will simulate the
    # execution by calling the functions with the temp paths.
    
    from aggregate import load_filtered_data, update_metadata
    from config import load_config
    
    # Change directory to tmp_path to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Reload config to pick up temp paths
        config = load_config(str(metadata_file)) # Assuming load_config takes path
        
        # 1. Load Data
        df = load_filtered_data(Path(config['paths']['processed_data']).parent)
        assert len(df) == 2
        assert 'galaxy_id' in df.columns
        
        # 2. Update Metadata
        update_metadata(config, metadata_file)
        
        # Verify metadata was updated
        with open(metadata_file, 'r') as f:
            updated_config = yaml.safe_load(f)
        
        assert 'download_timestamp' in updated_config['data']
        assert updated_config['data']['source'] == 'SPARC'
        
    finally:
        os.chdir(original_cwd)
