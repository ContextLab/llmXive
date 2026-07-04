import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import hashlib
from pathlib import Path
import sys

# Add code root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.config import compute_file_hash, get_state_root, get_project_root
from src.data.harmonize import update_state_with_hashes

def test_compute_file_hash():
    """Test that compute_file_hash generates a valid SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n1,2\n3,4")
        temp_path = f.name
    
    try:
        hash_value = compute_file_hash(temp_path)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in hash_value)
    finally:
        os.unlink(temp_path)

def test_update_state_with_hashes():
    """Test that update_state_with_hashes creates/updates state file correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        csv1_path = os.path.join(tmpdir, "test1.csv")
        csv2_path = os.path.join(tmpdir, "test2.csv")
        
        with open(csv1_path, 'w') as f:
            f.write("a,b\n1,2")
        
        with open(csv2_path, 'w') as f:
            f.write("c,d\n3,4")
        
        # Mock state file path
        import src.utils.config as config
        original_state_root = config.get_state_root
        
        def mock_get_state_root():
            return Path(tmpdir)
        
        config.get_state_root = mock_get_state_root
        
        try:
            # Call the function
            update_state_with_hashes(csv1_path, csv2_path)
            
            # Check state file exists
            state_file = Path(tmpdir) / "PROJ-206-statistical-analysis.yaml"
            assert state_file.exists()
            
            # Read and verify content
            import yaml
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            assert 'artifacts' in state_data
            assert 'poll_data_cleaned.csv' in state_data['artifacts']
            assert 'historical_weights.csv' in state_data['artifacts']
            
            # Verify hashes are present and valid
            assert 'sha256' in state_data['artifacts']['poll_data_cleaned.csv']
            assert 'sha256' in state_data['artifacts']['historical_weights.csv']
            assert len(state_data['artifacts']['poll_data_cleaned.csv']['sha256']) == 64
            assert len(state_data['artifacts']['historical_weights.csv']['sha256']) == 64
        finally:
            config.get_state_root = original_state_root

def test_missing_file_handling():
    """Test that missing files are handled gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import src.utils.config as config
        original_state_root = config.get_state_root
        
        def mock_get_state_root():
            return Path(tmpdir)
        
        config.get_state_root = mock_get_state_root
        
        try:
            # Call with non-existent file
            update_state_with_hashes("/nonexistent/file.csv", "/another/nonexistent.csv")
            
            # Should still create state file
            state_file = Path(tmpdir) / "PROJ-206-statistical-analysis.yaml"
            assert state_file.exists()
            
            import yaml
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            # Missing files should not be in artifacts or have null hashes
            # (depending on implementation, they might be skipped entirely)
            assert 'artifacts' in state_data
        finally:
            config.get_state_root = original_state_root
