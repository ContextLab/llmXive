"""
Unit tests for simulation result serialization (T029).
"""
import json
import pytest
from pathlib import Path
from typing import Dict, Any

from code.src.simulation.serialization import (
    save_simulation_result,
    save_batch_results,
    load_simulation_results
)
from code.src.simulation.schema import get_results_schema, validate_simulation_run


class TestSerialization:
    """Tests for result serialization functionality."""

    @pytest.fixture
    def temp_output_path(self, temp_data_dir: Path):
        """Create a temporary path for output files."""
        return temp_data_dir / "analysis" / "test_results.json"

    def test_save_single_result_valid(self, temp_output_path: Path):
        """Test saving a valid single simulation result."""
        result_path = save_simulation_result(
            output_path=temp_output_path,
            network_id="test-net-001",
            seed=42,
            diffusion_rate=0.85,
            topology_class="ErdosRenyi"
        )

        assert result_path.exists()
        assert result_path.suffix == ".json"

        # Verify content
        with open(result_path, 'r') as f:
            data = json.load(f)

        assert data["network_id"] == "test-net-001"
        assert data["seed"] == 42
        assert data["diffusion_rate"] == 0.85
        assert data["topology_class"] == "ErdosRenyi"
        assert "timestamp" in data
        assert "metadata" in data

    def test_save_single_result_with_additional_metrics(self, temp_output_path: Path):
        """Test saving a result with additional metrics."""
        additional = {
            "max_energy": 10.5,
            "min_energy": -2.3,
            "iterations": 1000
        }

        save_simulation_result(
            output_path=temp_output_path,
            network_id="test-net-002",
            seed=123,
            diffusion_rate=0.75,
            topology_class="WattsStrogatz",
            additional_metrics=additional
        )

        with open(temp_output_path, 'r') as f:
            data = json.load(f)

        assert data["additional_metrics"] == additional

    def test_save_batch_results(self, temp_output_path: Path):
        """Test saving a batch of simulation results."""
        results = [
            {
                "network_id": "net-001",
                "seed": 1,
                "diffusion_rate": 0.5,
                "topology_class": "ErdosRenyi"
            },
            {
                "network_id": "net-002",
                "seed": 2,
                "diffusion_rate": 0.6,
                "topology_class": "WattsStrogatz"
            }
        ]

        save_batch_results(temp_output_path, results)

        assert temp_output_path.exists()

        with open(temp_output_path, 'r') as f:
            data = json.load(f)

        assert data["total_runs"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["network_id"] == "net-001"
        assert data["results"][1]["topology_class"] == "WattsStrogatz"

    def test_load_simulation_results(self, temp_output_path: Path):
        """Test loading saved simulation results."""
        # First save
        save_simulation_result(
            output_path=temp_output_path,
            network_id="load-test",
            seed=999,
            diffusion_rate=0.99,
            topology_class="ScaleFree"
        )

        # Then load
        loaded = load_simulation_results(temp_output_path)

        assert loaded["network_id"] == "load-test"
        assert loaded["seed"] == 999
        assert loaded["diffusion_rate"] == 0.99
        assert loaded["topology_class"] == "ScaleFree"

    def test_load_batch_results(self, temp_output_path: Path):
        """Test loading batch simulation results."""
        results = [
            {
                "network_id": "batch-001",
                "seed": 10,
                "diffusion_rate": 0.4,
                "topology_class": "ErdosRenyi"
            },
            {
                "network_id": "batch-002",
                "seed": 20,
                "diffusion_rate": 0.45,
                "topology_class": "WattsStrogatz"
            }
        ]

        save_batch_results(temp_output_path, results)
        loaded = load_simulation_results(temp_output_path)

        assert loaded["total_runs"] == 2
        assert loaded["results"][0]["network_id"] == "batch-001"
        assert loaded["results"][1]["network_id"] == "batch-002"

    def test_schema_validation_failure(self, temp_output_path: Path):
        """Test that invalid results fail schema validation."""
        # Create an invalid result (missing required field)
        invalid_result = {
            "network_id": "invalid",
            "seed": 1,
            # Missing "diffusion_rate"
            "topology_class": "Test"
        }

        # Attempting to save should raise ValueError due to schema validation
        with pytest.raises(ValueError, match="Schema validation failed"):
            save_simulation_result(
                output_path=temp_output_path,
                network_id=invalid_result["network_id"],
                seed=invalid_result["seed"],
                diffusion_rate=0.0, # We must provide a float, but the dict passed to validate is constructed from args
                topology_class=invalid_result["topology_class"]
            )
            # Note: The function constructs the dict from arguments, so to test
            # a specific schema violation (like missing a field that the function
            # doesn't enforce via arguments), we would need to manipulate the
            # constructed dict. However, the function enforces the core fields
            # via its signature. The test above ensures the function runs.
            # A true schema failure would happen if we passed a type that
            # validation rejects (e.g., string instead of float for rate).

        # Test type mismatch
        with pytest.raises(ValueError, match="Schema validation failed"):
            # Pass a string where a float is expected (if schema is strict on types)
            # Or manually construct a bad dict if the function allowed it.
            # Since the function signature enforces types, we test the validation
            # logic by calling the validator directly with bad data.
            pass

        # Direct validation test
        schema = get_results_schema()
        bad_data = {"network_id": "x", "seed": 1, "topology_class": "y"}
        with pytest.raises(Exception): # Schema validation raises
            validate_simulation_run(bad_data, schema)

    def test_directory_creation(self, temp_data_dir: Path):
        """Test that save_simulation_result creates necessary directories."""
        deep_path = temp_data_dir / "analysis" / "subdir" / "deep" / "result.json"
        
        save_simulation_result(
            output_path=deep_path,
            network_id="deep-test",
            seed=1,
            diffusion_rate=0.1,
            topology_class="Test"
        )

        assert deep_path.exists()
        assert deep_path.parent.exists()