import json
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# We need to mock the project structure and dependencies
# Since we are running tests, we assume the code is importable
# or we mock the imports if necessary.
# For this test, we will create a temporary directory structure.

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory structure."""
    base = tempfile.mkdtemp()
    # Create required dirs
    dirs = ['code', 'data', 'data/processed', 'data/raw', 'state', 'models', 'reports']
    for d in dirs:
        os.makedirs(os.path.join(base, d), exist_ok=True)
    
    # Create a mock aggregated_clean.csv
    data_path = os.path.join(base, 'data', 'processed', 'aggregated_clean.csv')
    df = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'normalization_method': ['normalized', 'normalized', 'raw', 'normalized', 'raw']
    })
    df.to_csv(data_path, index=False)
    
    # Create a mock hygiene.py to satisfy imports if needed
    # (In a real scenario, we would mock the import or have the file present)
    # For now, we assume the test runner has the files or we mock them.
    
    return base

def test_count_records(temp_project_dir):
    """Test that count_records correctly counts normalized and raw records."""
    # Change to temp directory to simulate project root
    original_dir = os.getcwd()
    os.chdir(temp_project_dir)
    
    try:
        # Import the function from the code directory
        # We need to add the code directory to sys.path
        code_dir = os.path.join(temp_project_dir, 'code')
        if code_dir not in sys.path:
            sys.path.insert(0, code_dir)
        
        # We need to mock the hygiene module if it's not present
        # For this test, we'll create a minimal mock
        hygiene_path = os.path.join(code_dir, 'hygiene.py')
        if not os.path.exists(hygiene_path):
            with open(hygiene_path, 'w') as f:
                f.write("def update_artifact_hash(path): pass\n")
        
        # Similarly for logging_config
        logging_config_path = os.path.join(code_dir, 'logging_config.py')
        if not os.path.exists(logging_config_path):
            with open(logging_config_path, 'w') as f:
                f.write("""
                import logging
                def get_logger(name): return logging.getLogger(name)
                def raise_on_missing_data(msg): raise ValueError(msg)
                """)

        from ingest import count_records

        result = count_records()
        
        assert result['total_count'] == 5
        assert result['normalized_count'] == 3
        assert result['raw_count'] == 2
        assert 'timestamp' in result
        assert result['task_id'] == 'T016a'
        
        # Check that the output file was created
        output_path = os.path.join(temp_project_dir, 'data', 'processed', 'record_counts.json')
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result['total_count'] == 5
        assert saved_result['normalized_count'] == 3
        assert saved_result['raw_count'] == 2
        
    finally:
        os.chdir(original_dir)
        # Clean up temp directory
        shutil.rmtree(temp_project_dir)
