import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_acquisition import (
    fetch_geo_dataset,
    check_response_labels,
    write_checksum_to_state,
    run_geo_acquisition,
    compute_file_checksum
)
from src.config import get_project_root

class TestGEOAcquisition:
    """
    Integration tests for GEO data acquisition.
    These tests mock the network calls and file system to verify logic.
    """

    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project structure."""
        # Create necessary directories
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        results_dir = tmp_path / "data"
        results_dir.mkdir(parents=True)
        
        return tmp_path

    def test_fetch_geo_dataset_fails_gracefully(self, temp_project_dir):
        """Test that fetch_geo_dataset returns None when download fails."""
        # This would require mocking requests.get
        # For now, we test the logic that it handles exceptions
        output_dir = temp_project_dir / "data" / "raw"
        result = fetch_geo_dataset("INVALID_ID", output_dir)
        assert result is None

    def test_check_response_labels_with_valid_data(self, temp_project_dir):
        """Test response label detection with valid data."""
        import pandas as pd
        df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'response': ['CR', 'PR'],
            'gene1': [10, 20]
        })
        assert check_response_labels(df) is True

    def test_check_response_labels_with_invalid_data(self, temp_project_dir):
        """Test response label detection with invalid data."""
        import pandas as pd
        df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'gene1': [10, 20]
        })
        assert check_response_labels(df) is False

    def test_write_checksum_to_state(self, temp_project_dir):
        """Test atomic checksum writing to state file."""
        # Create a dummy file
        dummy_file = temp_project_dir / "data" / "raw" / "test.txt"
        dummy_file.write_text("test content")
        
        state_file = temp_project_dir / "state" / "projects" / "test.yaml"
        
        checksum = compute_file_checksum(dummy_file)
        write_checksum_to_state(dummy_file, checksum, state_file)
        
        # Verify state file was created and contains checksum
        assert state_file.exists()
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)
        
        assert 'artifact_hashes' in state_data
        assert 'test.txt' in state_data['artifact_hashes']
        assert state_data['artifact_hashes']['test.txt'] == checksum

    def test_run_geo_acquisition_halts_on_insufficient_datasets(self, temp_project_dir, monkeypatch):
        """Test that acquisition halts if <2 valid GEO datasets are found."""
        # Mock fetch_geo_dataset to return None for all IDs
        def mock_fetch(geo_id, output_dir):
            return None
        
        monkeypatch.setattr("src.data_acquisition.fetch_geo_dataset", mock_fetch)
        
        # Mock CONFIGURED_GEO_IDS to have 3 IDs
        import src.data_acquisition as da
        original_ids = da.CONFIGURED_GEO_IDS
        da.CONFIGURED_GEO_IDS = ["GSE1", "GSE2", "GSE3"]
        
        # Run acquisition
        exit_code = run_geo_acquisition()
        
        # Restore original IDs
        da.CONFIGURED_GEO_IDS = original_ids
        
        # Verify exit code is 1
        assert exit_code == 1
        
        # Verify feasibility gate file was written
        gate_file = temp_project_dir / "data" / "feasibility_gate.json"
        assert gate_file.exists()
        
        with open(gate_file, 'r') as f:
            gate_result = json.load(f)
        
        assert gate_result['status'] == 'halted'
        assert gate_result['reason'] == 'insufficient_geo_datasets'

    def test_run_geo_acquisition_succeeds_with_sufficient_datasets(self, temp_project_dir, monkeypatch):
        """Test that acquisition succeeds if >=2 valid GEO datasets are found."""
        import src.data_acquisition as da
        from pathlib import Path as PPath
        
        # Mock fetch_geo_dataset to return a dummy file
        def mock_fetch(geo_id, output_dir):
            dummy_file = output_dir / f"{geo_id}.txt"
            dummy_file.write_text("dummy data")
            return dummy_file
        
        def mock_parse_metadata(file_path):
            return {}
        
        def mock_check_response_labels(df):
            return True
        
        monkeypatch.setattr("src.data_acquisition.fetch_geo_dataset", mock_fetch)
        monkeypatch.setattr("src.data_acquisition.parse_geo_metadata", mock_parse_metadata)
        monkeypatch.setattr("src.data_acquisition.check_response_labels", mock_check_response_labels)
        
        # Mock CONFIGURED_GEO_IDS to have 3 IDs
        original_ids = da.CONFIGURED_GEO_IDS
        da.CONFIGURED_GEO_IDS = ["GSE1", "GSE2", "GSE3"]
        
        # Run acquisition
        exit_code = run_geo_acquisition()
        
        # Restore original IDs
        da.CONFIGURED_GEO_IDS = original_ids
        
        # Verify exit code is 0
        assert exit_code == 0
        
        # Verify feasibility gate file was written with status 'ready' (or not written if success)
        # In this implementation, we only write on failure, so we check for the absence or a success state
        gate_file = temp_project_dir / "data" / "feasibility_gate.json"
        # Note: The current implementation only writes on failure. 
        # If we want to write on success, we need to modify run_geo_acquisition.
        # For this test, we assume success means no halt.
        # We can check that the state file has been updated with checksums.
        state_file = temp_project_dir / "state" / "projects" / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f)
        
        assert 'artifact_hashes' in state_data
        assert len(state_data['artifact_hashes']) >= 2