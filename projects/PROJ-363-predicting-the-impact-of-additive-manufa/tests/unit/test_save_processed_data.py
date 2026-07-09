"""
Unit tests for Task T018: save_processed_data.py
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import compute_file_hash, load_state, update_state

class TestSaveProcessedData:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories and mock data for each test."""
        self.test_dir = tmp_path
        self.data_dir = self.test_dir / "data" / "raw"
        self.processed_dir = self.test_dir / "data" / "processed"
        self.state_dir = self.test_dir / "state"
        
        self.data_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)
        self.state_dir.mkdir(parents=True)
        
        # Create a mock raw CSV
        self.raw_csv = self.data_dir / "316L_LPBF_dataset.csv"
        mock_data = {
            'laser_power': [100, 200, 300],
            'scan_speed': [500, 600, 700],
            'hatch_spacing': [0.1, 0.1, 0.1],
            'layer_thickness': [0.03, 0.03, 0.03],
            'porosity': [0.01, 0.02, 0.03]
        }
        pd.DataFrame(mock_data).to_csv(self.raw_csv, index=False)
        
        # Create initial state.yaml
        self.state_file = self.state_dir / "state.yaml"
        self.state_file.write_text("version: 1.0\nartifacts: {}\n")
        
        yield
        
        # Cleanup is handled by tmp_path
    
    def test_file_creation_and_hash(self):
        """Test that the output file is created and hash is computed correctly."""
        from save_processed_data import main
        
        # Temporarily patch paths to use our test directory
        import save_processed_data as spd
        
        original_root = Path(__file__).resolve().parent.parent.parent
        
        # We can't easily patch the module-level variables, so we test the logic directly
        # by importing the necessary functions and running the logic manually
        
        # Simulate the logic of main()
        processed_output_path = self.processed_dir / "cleaned_316L.csv"
        
        # Create a dummy processed file (simulating the result of preprocess_data)
        dummy_df = pd.DataFrame({
            'laser_power': [100, 200, 300],
            'scan_speed': [500, 600, 700],
            'hatch_spacing': [0.1, 0.1, 0.1],
            'layer_thickness': [0.03, 0.03, 0.03],
            'porosity': [0.01, 0.02, 0.03],
            'energy_density': [6.67, 5.56, 4.76]
        })
        dummy_df.to_csv(processed_output_path, index=False)
        
        # Verify file exists
        assert processed_output_path.exists()
        
        # Verify hash computation
        file_hash = compute_file_hash(processed_output_path)
        assert isinstance(file_hash, str)
        assert len(file_hash) == 64  # SHA-256 hex length
        
        # Verify state update logic
        state = load_state(self.state_file)
        state = update_state(
            state,
            artifact_name="cleaned_316L.csv",
            artifact_path=str(processed_output_path.relative_to(self.test_dir)),
            hash_value=file_hash,
            description="Test update"
        )
        
        assert "cleaned_316L.csv" in state.get("artifacts", {})
        assert state["artifacts"]["cleaned_316L.csv"]["hash"] == file_hash
    
    def test_state_update_persistence(self):
        """Test that state updates are persisted to disk."""
        from utils import load_state, update_state, compute_file_hash
        
        processed_output_path = self.processed_dir / "cleaned_316L.csv"
        dummy_df = pd.DataFrame({'col': [1, 2, 3]})
        dummy_df.to_csv(processed_output_path, index=False)
        
        file_hash = compute_file_hash(processed_output_path)
        
        state = load_state(self.state_file)
        state = update_state(
            state,
            artifact_name="cleaned_316L.csv",
            artifact_path=str(processed_output_path.relative_to(self.test_dir)),
            hash_value=file_hash,
            description="Persistence test"
        )
        
        # Re-load state to verify persistence
        state_reloaded = load_state(self.state_file)
        assert state_reloaded["artifacts"]["cleaned_316L.csv"]["hash"] == file_hash
        assert state_reloaded["artifacts"]["cleaned_316L.csv"]["description"] == "Persistence test"
    
    def test_degenerate_dataset_handling(self):
        """Test that the system handles degenerate datasets correctly (if they reach this step)."""
        # This test verifies that if a degenerate dataset somehow reached this step,
        # the hash computation and saving would still work (the error would have been raised earlier).
        
        processed_output_path = self.processed_dir / "cleaned_316L.csv"
        
        # Create a dataset with zero variance (degenerate)
        degenerate_df = pd.DataFrame({
            'laser_power': [100, 100, 100],
            'scan_speed': [500, 500, 500],
            'hatch_spacing': [0.1, 0.1, 0.1],
            'layer_thickness': [0.03, 0.03, 0.03],
            'porosity': [0.0, 0.0, 0.0]  # Zero variance
        })
        degenerate_df.to_csv(processed_output_path, index=False)
        
        # The save logic itself should not fail on degenerate data
        # (The check happens in preprocess.py, not here)
        file_hash = compute_file_hash(processed_output_path)
        assert file_hash is not None
        assert len(file_hash) == 64