import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.data.ingest import (
    fetch_dataset_from_hf,
    load_and_count_reactions,
    filter_transition_metals,
    handle_scarcity,
    run_ingestion
)
from src.data.checksum_manager import load_checksum_manifest

class TestIngest:
    """Test suite for data ingestion module (T015, T016, T016b)."""
    
    def test_fetch_dataset_from_hf_creates_file(self):
        """Test that fetch_dataset_from_hf downloads and creates the file."""
        with patch('src.data.ingest.requests.get') as mock_get, \
             patch('src.data.ingest.compute_file_checksum') as mock_checksum, \
             patch('src.data.ingest.save_checksum_manifest'), \
             patch('src.data.ingest.Path.mkdir'), \
             patch('src.data.ingest.shutil.move'):
            
            # Mock response
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"fake_data"]
            mock_get.return_value = mock_response
            mock_checksum.return_value = "abc123"
            
            # Call function
            result_path = fetch_dataset_from_hf()
            
            # Verify
            assert result_path.exists() or str(result_path).endswith("qm9_ts_subset.parquet")
            mock_get.assert_called_once()
    
    def test_load_and_count_reactions_parquet(self):
        """Test loading and counting from parquet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame([{"a": 1}, {"a": 2}, {"a": 3}])
            df.to_parquet(data_path)
            
            count, records = load_and_count_reactions(data_path)
            
            assert count == 3
            assert len(records) == 3
    
    def test_filter_transition_metals(self):
        """Test filtering for specific metals."""
        records = [
            {"metal_center": "Pd", "energy": 1.0},
            {"metal_center": "Ni", "energy": 2.0},
            {"metal_center": "Cu", "energy": 3.0},
            {"metal_center": "Fe", "energy": 4.0},
            {"metal_center": "Pd", "energy": 5.0}
        ]
        
        count, filtered = filter_transition_metals(records, ["Pd", "Ni", "Cu"])
        
        assert count == 4
        assert all(r["metal_center"] in ["Pd", "Ni", "Cu"] for r in filtered)
    
    def test_handle_scarcity_below_threshold(self):
        """Test scarcity flag creation when count < threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scarcity.json"
            
            result = handle_scarcity(50, 120, output_path)
            
            assert result["status"] == "scarcity"
            assert result["count"] == 50
            assert result["threshold"] == 120
            assert output_path.exists()
            
            with open(output_path) as f:
                saved = json.load(f)
                assert saved["status"] == "scarcity"
    
    def test_handle_scarcity_above_threshold(self):
        """Test no flag creation when count >= threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "scarcity.json"
            
            result = handle_scarcity(200, 120, output_path)
            
            assert result["status"] == "sufficient"
            assert not output_path.exists()
    
    def test_run_ingestion_integration(self):
        """Integration test for the full ingestion pipeline."""
        # This test mocks the external dependencies to verify flow
        with patch('src.data.ingest.fetch_dataset_from_hf') as mock_fetch, \
             patch('src.data.ingest.load_and_count_reactions') as mock_load, \
             patch('src.data.ingest.filter_transition_metals') as mock_filter, \
             patch('src.data.ingest.handle_scarcity') as mock_scarcity, \
             patch('src.data.ingest.load_config') as mock_config, \
             patch('src.data.ingest.get_config_value') as mock_get_val:
            
            # Setup mocks
            mock_fetch.return_value = Path("/fake/path/data.parquet")
            mock_load.return_value = (1000, [{"metal_center": "Pd"}] * 1000)
            mock_filter.return_value = (150, [{"metal_center": "Pd"}] * 150)
            mock_scarcity.return_value = {"status": "sufficient", "count": 150}
            mock_config.return_value = {}
            mock_get_val.return_value = 120
            
            result = run_ingestion()
            
            assert result["status"] == "sufficient"
            assert mock_fetch.called
            assert mock_load.called
            assert mock_filter.called
            assert mock_scarcity.called