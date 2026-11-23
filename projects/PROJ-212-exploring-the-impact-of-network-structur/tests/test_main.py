"""
Unit tests for main.py orchestration logic.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from data_models import SimulationResult, SynchronizationStatus

class TestMainOrchestration:
    """Tests for the main orchestration script."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dirs = {
                "raw": tmp_path / "data" / "raw",
                "results": tmp_path / "results",
                "state": tmp_path / "state"
            }
            for d in dirs.values():
                d.mkdir(parents=True, exist_ok=True)
            yield dirs

    @pytest.fixture
    def mock_config(self, temp_dirs):
        """Create a mock configuration."""
        config = {
            "paths": {
                "raw_data_dir": str(temp_dirs["raw"]),
                "results_dir": str(temp_dirs["results"]),
                "state_dir": str(temp_dirs["state"])
            },
            "simulation": {
                "n_oscillators": 100,
                "threshold_r": 0.8,
                "threshold_t": 50,
                "k_min": 0.0,
                "k_max": 5.0,
                "tolerance": 0.01
            },
            "seeds": {
                "random_seed": 42
            }
        }
        return config

    def test_main_creates_output_file(self, temp_dirs, mock_config):
        """Test that main creates the sim_results.json file."""
        from main import main
        
        # Create a mock network file
        network_file = temp_dirs["raw"] / "test_network.mtx"
        network_file.write_text("# Test network\n3 3\n1 2\n2 3\n3 1\n")
        
        # Mock the loader to return our test file
        with patch('main.get_snap_dataset_list') as mock_list, \
             patch('main.load_snap_graph_from_edgelist') as mock_load, \
             patch('main.compute_metrics') as mock_metrics, \
             patch('main.process_single_network') as mock_sim, \
             patch('main.validate_network_list', return_value=True):
            
            # Setup mocks
            mock_list.return_value = [network_file]
            mock_graph = MagicMock()
            mock_load.return_value = mock_graph
            mock_metrics.return_value = {"degree": 2.0, "clustering": 0.5, "path_length": 1.5}
            mock_sim.return_value = SimulationResult(
                threshold=1.2,
                status=SynchronizationStatus.SYNCHRONIZED,
                computation_time=0.5
            )
            
            # Run main
            result = main(mock_config)
            
            # Verify output file exists
            output_path = Path(mock_config["paths"]["results_dir"]) / "sim_results.json"
            assert output_path.exists()
            
            # Verify content
            with open(output_path) as f:
                data = json.load(f)
            
            assert "networks" in data
            assert data["total_processed"] == 1
            assert data["status"] == "completed"
            assert data["networks"][0]["network_id"] == "test_network"
            assert "threshold" in data["networks"][0]
            assert "metrics" in data["networks"][0]

    def test_main_handles_empty_directory(self, temp_dirs, mock_config):
        """Test that main handles empty raw data directory gracefully."""
        from main import main
        
        with patch('main.get_snap_dataset_list', return_value=[]):
            result = main(mock_config)
            
            output_path = Path(mock_config["paths"]["results_dir"]) / "sim_results.json"
            assert output_path.exists()
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data["status"] == "completed_no_data"
            assert data["total_processed"] == 0

    def test_main_handles_processing_errors(self, temp_dirs, mock_config):
        """Test that main continues processing if one network fails."""
        from main import main
        
        # Create two network files
        network1 = temp_dirs["raw"] / "network1.mtx"
        network1.write_text("# Network 1\n3 3\n1 2\n2 3\n3 1\n")
        network2 = temp_dirs["raw"] / "network2.mtx"
        network2.write_text("# Network 2\n3 3\n1 2\n2 3\n3 1\n")
        
        call_count = 0
        
        def mock_load_side_effect(path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Simulated load error")
            return MagicMock()
        
        with patch('main.get_snap_dataset_list', return_value=[network1, network2]), \
             patch('main.load_snap_graph_from_edgelist', side_effect=mock_load_side_effect), \
             patch('main.compute_metrics', return_value={"degree": 2.0}), \
             patch('main.process_single_network', return_value=SimulationResult(
                 threshold=1.0,
                 status=SynchronizationStatus.SYNCHRONIZED,
                 computation_time=0.1
             )), \
             patch('main.validate_network_list', return_value=True):
            
            result = main(mock_config)
            
            output_path = Path(mock_config["paths"]["results_dir"]) / "sim_results.json"
            assert output_path.exists()
            
            with open(output_path) as f:
                data = json.load(f)
            
            # Should have processed 1 network (the second one)
            assert data["total_processed"] == 1
            assert len(data["networks"]) == 1
            assert data["networks"][0]["network_id"] == "network2"
            assert "error" not in data["networks"][0]

    def test_main_output_schema(self, temp_dirs, mock_config):
        """Test that the output JSON matches the required schema."""
        from main import main
        
        network_file = temp_dirs["raw"] / "schema_test.mtx"
        network_file.write_text("# Schema test\n4 4\n1 2\n2 3\n3 4\n4 1\n")
        
        with patch('main.get_snap_dataset_list', return_value=[network_file]), \
             patch('main.load_snap_graph_from_edgelist', return_value=MagicMock()), \
             patch('main.compute_metrics', return_value={
                 "mean_degree": 2.0,
                 "clustering_coefficient": 0.5,
                 "average_path_length": 1.5
             }), \
             patch('main.process_single_network', return_value=SimulationResult(
                 threshold=0.85,
                 status=SynchronizationStatus.SYNCHRONIZED,
                 computation_time=0.2
             )), \
             patch('main.validate_network_list', return_value=True):
            
            main(mock_config)
            
            output_path = Path(mock_config["paths"]["results_dir"]) / "sim_results.json"
            with open(output_path) as f:
                data = json.load(f)
            
            # Check required keys in top level
            assert "networks" in data
            assert "total_processed" in data
            assert "status" in data
            
            # Check required keys in each network entry
            network_entry = data["networks"][0]
            assert "network_id" in network_entry
            assert "metrics" in network_entry
            assert "threshold" in network_entry