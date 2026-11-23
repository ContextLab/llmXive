"""
Unit tests for the AXPO Simulator.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.lib.axpo_simulator import (
    AXPOSimulator,
    AXPOSimulatorError,
    SimulationResult,
    BatchSimulationResult,
    load_axpo_simulations,
    run_axpo_simulation_diagnostic
)

class TestAXPOSimulator:
    """Tests for the AXPOSimulator class."""

    def test_init_creates_cache_dir(self, tmp_path):
        """Test that the simulator creates the cache directory if it doesn't exist."""
        simulator = AXPOSimulator(cache_dir=tmp_path / "new_cache")
        assert simulator.cache_dir.exists()
        assert simulator.cache_dir.is_dir()

    def test_load_cache_missing_file(self, tmp_path):
        """Test that loading from a missing file raises an error."""
        simulator = AXPOSimulator(cache_dir=tmp_path)
        with pytest.raises(AXPOSimulatorError, match="Simulation cache not found"):
            simulator.load_cache()

    def test_load_cache_empty_file(self, tmp_path):
        """Test that loading an empty JSON list raises an error."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        cache_file.write_text("[]")
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        with pytest.raises(AXPOSimulatorError, match="Simulation cache is empty"):
            simulator.load_cache()

    def test_load_cache_invalid_json(self, tmp_path):
        """Test that loading invalid JSON raises an error."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        cache_file.write_text("{ invalid json }")
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        with pytest.raises(AXPOSimulatorError, match="Failed to parse simulation cache JSON"):
            simulator.load_cache()

    def test_load_cache_missing_keys(self, tmp_path):
        """Test that loading data with missing required keys raises an error."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        # Missing 'success' key
        data = [{"problem_id": "123"}]
        cache_file.write_text(json.dumps(data))
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        with pytest.raises(AXPOSimulatorError, match="missing required keys"):
            simulator.load_cache()

    def test_load_cache_success(self, tmp_path):
        """Test successful loading of valid cache data."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [
            {"problem_id": "p1", "success": True, "reasoning": "trace1"},
            {"problem_id": "p2", "success": False, "reasoning": "trace2"}
        ]
        cache_file.write_text(json.dumps(data))
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        loaded = simulator.load_cache()
        
        assert len(loaded) == 2
        assert loaded[0]["problem_id"] == "p1"
        assert loaded[1]["success"] is False

    def test_simulate_single_found(self, tmp_path):
        """Test retrieving a single existing problem."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [
            {"problem_id": "p1", "success": True, "meta": "value"}
        ]
        cache_file.write_text(json.dumps(data))
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        result = simulator.simulate_single("p1")
        
        assert result.problem_id == "p1"
        assert result.success is True
        assert result.failure_rate == 0.0
        assert result.metadata == {"meta": "value"}

    def test_simulate_single_not_found(self, tmp_path):
        """Test retrieving a non-existing problem raises error."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [{"problem_id": "p1", "success": True}]
        cache_file.write_text(json.dumps(data))
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        with pytest.raises(AXPOSimulatorError, match="not found in simulation cache"):
            simulator.simulate_single("p999")

    def test_run_batch_success(self, tmp_path):
        """Test running a batch of simulations."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [
            {"problem_id": "p1", "success": True},
            {"problem_id": "p2", "success": False},
            {"problem_id": "p3", "success": False}
        ]
        cache_file.write_text(json.dumps(data))
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        batch = simulator.run_batch(["p1", "p2", "p3"])
        
        assert batch.total_samples == 3
        assert batch.total_failures == 2
        assert batch.aggregate_failure_rate == pytest.approx(2/3)
        assert len(batch.results) == 3

    def test_run_batch_missing_ids(self, tmp_path):
        """Test running a batch with missing IDs raises error."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [{"problem_id": "p1", "success": True}]
        cache_file.write_text(json.dumps(data))
        
        simulator = AXPOSimulator(cache_dir=tmp_path)
        with pytest.raises(AXPOSimulatorError, match="Missing simulation results"):
            simulator.run_batch(["p1", "p999"])

class TestRunAXPOSimulationDiagnostic:
    """Tests for the run_axpo_simulation_diagnostic function."""

    def test_run_diagnostic(self, tmp_path):
        """Test the main diagnostic entry point."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [
            {"problem_id": "p1", "success": True},
            {"problem_id": "p2", "success": False}
        ]
        cache_file.write_text(json.dumps(data))
        
        result = run_axpo_simulation_diagnostic(["p1", "p2"], cache_dir=tmp_path)
        
        assert result["total_samples"] == 2
        assert result["total_failures"] == 1
        assert result["aggregate_failure_rate"] == pytest.approx(0.5)
        assert result["failure_rates"]["p1"] == 0.0
        assert result["failure_rates"]["p2"] == 1.0

class TestLoadAXPOSimulations:
    """Tests for the load_axpo_simulations function."""

    def test_load_axpo_simulations(self, tmp_path):
        """Test the convenience loader function."""
        cache_file = tmp_path / "axpo_simulations_cache.json"
        data = [{"problem_id": "p1", "success": True}]
        cache_file.write_text(json.dumps(data))
        
        loaded = load_axpo_simulations(cache_dir=tmp_path)
        
        assert len(loaded) == 1
        assert loaded[0]["problem_id"] == "p1"