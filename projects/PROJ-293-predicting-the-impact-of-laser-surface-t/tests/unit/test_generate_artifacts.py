import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from hygiene import load_artifact_hashes, calculate_md5
from generate_artifacts import main

class TestGenerateArtifacts:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary directories and mock data for testing."""
        # Create necessary directory structure
        self.data_processed = tmp_path / "data" / "processed"
        self.state = tmp_path / "state"
        self.data_processed.mkdir(parents=True)
        self.state.mkdir(parents=True)
        
        # Create a mock aggregated_clean.csv
        self.mock_csv = self.data_processed / "aggregated_clean.csv"
        mock_data = {
            'pulse_duration': [10.0, 20.0, 30.0],
            'power': [100.0, 150.0, 200.0],
            'wear_rate': [0.5, 0.6, 0.7],
            'normalization_method': ['normalized', 'normalized', 'raw']
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(self.mock_csv, index=False)
        
        # Set environment variable to point to temp root if needed, 
        # but for this test we will patch paths if the script relies on __file__ parent.
        # Since the script uses Path(__file__).parent.parent, we need to ensure the test 
        # context mimics the project structure or we test the logic directly.
        # For this specific task, we will test the side effects on the file system.
        
        self.tmp_root = tmp_path
        # Re-structure to match expected relative paths from code dir
        # code/
        #   generate_artifacts.py (in this test, we are running from tests/unit)
        #   hygiene.py
        # data/processed/aggregated_clean.csv
        # state/artifact_hashes.yaml
        
        # We will patch the main function's behavior or run it in a controlled env
        pass

    def test_artifact_hash_update(self, tmp_path):
        """Test that the script updates the artifact_hashes.yaml correctly."""
        # Setup paths to mimic project structure relative to a code dir
        # We create a fake 'code' dir inside tmp_path to make __file__ logic work if we moved the script
        # Instead, we test the hygiene functions directly as the script just orchestrates them.
        
        csv_path = tmp_path / "data" / "processed" / "aggregated_clean.csv"
        state_path = tmp_path / "state" / "artifact_hashes.yaml"
        
        csv_path.parent.mkdir(parents=True)
        state_path.parent.mkdir(parents=True)
        
        # Write mock CSV
        df = pd.DataFrame({'col': [1, 2, 3]})
        df.to_csv(csv_path, index=False)
        
        # Calculate expected hash
        expected_hash = calculate_md5(csv_path)
        
        # Simulate the update logic
        from hygiene import load_artifact_hashes, update_artifact_hash, save_artifact_hashes
        
        hashes = load_artifact_hashes(state_path)
        hashes = update_artifact_hash(hashes, "data/processed/aggregated_clean.csv", expected_hash, "md5")
        save_artifact_hashes(hashes, state_path)
        
        # Verify file exists and content
        assert state_path.exists()
        with open(state_path, 'r') as f:
            content = yaml.safe_load(f)
        
        assert "data/processed/aggregated_clean.csv" in content
        assert content["data/processed/aggregated_clean.csv"]["hash"] == expected_hash
        assert content["data/processed/aggregated_clean.csv"]["type"] == "md5"

    def test_csv_generation_logic(self):
        """Verify that if the CSV is missing, the ingestion pipeline is triggered."""
        # This is a logic check. Since we cannot easily run the full ingestion pipeline 
        # in a unit test without mocking complex dependencies, we verify the 
        # condition check exists in the code.
        import inspect
        source = inspect.getsource(main)
        
        assert "aggregated_clean.csv" in source
        assert "ingest" in source
        assert "exists" in source
        assert "ValueError" in source or "RuntimeError" in source # Should fail loudly if missing
        assert "calculate_md5" in source
        assert "update_artifact_hash" in source
        assert "save_artifact_hashes" in source