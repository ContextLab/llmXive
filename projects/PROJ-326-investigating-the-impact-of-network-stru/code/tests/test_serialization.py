"""
Unit tests for simulation result serialization (T029).

Tests that results are correctly serialized to JSON with proper schema compliance.
"""
import json
import tempfile
from pathlib import Path
import pytest

from code.src.simulation.serialization import (
    save_simulation_result,
    save_batch_simulation_results,
    load_simulation_results,
    append_single_result
)
from code.src.simulation.schema import get_results_schema, validate_results_file


class TestSerialization:
    """Test suite for simulation result serialization."""

    def test_save_single_result(self, temp_data_dir):
        """Test saving a single simulation result."""
        output_path = temp_data_dir / "single_result.json"
        
        result_path = save_simulation_result(
            output_path=output_path,
            network_id="test_net_001",
            seed=42,
            diffusion_rate=0.75,
            topology_class="er"
        )
        
        assert result_path.exists()
        
        with open(result_path, 'r') as f:
            data = json.load(f)
            
        assert isinstance(data, list)
        assert len(data) == 1
        
        result = data[0]
        assert result["network_id"] == "test_net_001"
        assert result["seed"] == 42
        assert result["diffusion_rate"] == 0.75
        assert result["topology_class"] == "er"
        assert "timestamp" in result
        assert "schema_version" in result

    def test_save_batch_results(self, temp_data_dir):
        """Test saving a batch of simulation results."""
        output_path = temp_data_dir / "batch_results.json"
        
        results = [
            {
                "network_id": "net_001",
                "seed": 1,
                "diffusion_rate": 0.5,
                "topology_class": "er"
            },
            {
                "network_id": "net_002",
                "seed": 2,
                "diffusion_rate": 0.6,
                "topology_class": "sw"
            },
            {
                "network_id": "net_003",
                "seed": 3,
                "diffusion_rate": 0.7,
                "topology_class": "sf"
            }
        ]
        
        result_path = save_batch_simulation_results(output_path, results)
        
        assert result_path.exists()
        
        loaded = load_simulation_results(output_path)
        assert len(loaded) == 3
        
        for i, loaded_result in enumerate(loaded):
            assert loaded_result["network_id"] == results[i]["network_id"]
            assert loaded_result["diffusion_rate"] == results[i]["diffusion_rate"]

    def test_load_nonexistent_file(self, temp_data_dir):
        """Test loading from a non-existent file raises FileNotFoundError."""
        output_path = temp_data_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_simulation_results(output_path)

    def test_schema_compliance(self, temp_data_dir):
        """Test that saved results conform to schema."""
        output_path = temp_data_dir / "schema_test.json"
        
        save_simulation_result(
            output_path=output_path,
            network_id="test_001",
            seed=123,
            diffusion_rate=0.8,
            topology_class="sw"
        )
        
        loaded = load_simulation_results(output_path)
        schema = get_results_schema()
        
        for result in loaded:
            # This should not raise
            validate_results_file(result, schema)

    def test_append_result(self, temp_data_dir):
        """Test appending a result to an existing file."""
        output_path = temp_data_dir / "append_test.json"
        
        # First save
        save_simulation_result(
            output_path=output_path,
            network_id="net_001",
            seed=1,
            diffusion_rate=0.5,
            topology_class="er"
        )
        
        # Append second result
        append_single_result(
            output_path=output_path,
            result={
                "network_id": "net_002",
                "seed": 2,
                "diffusion_rate": 0.6,
                "topology_class": "sw"
            }
        )
        
        loaded = load_simulation_results(output_path)
        assert len(loaded) == 2
        assert loaded[0]["network_id"] == "net_001"
        assert loaded[1]["network_id"] == "net_002"

    def test_additional_metrics(self, temp_data_dir):
        """Test saving results with additional metrics."""
        output_path = temp_data_dir / "metrics_test.json"
        
        save_simulation_result(
            output_path=output_path,
            network_id="net_001",
            seed=1,
            diffusion_rate=0.5,
            topology_class="er",
            additional_metrics={
                "spatial_variance": 0.25,
                "energy_density": 0.1,
                "steps": 100
            }
        )
        
        loaded = load_simulation_results(output_path)
        assert "additional_metrics" in loaded[0]
        assert loaded[0]["additional_metrics"]["spatial_variance"] == 0.25

    def test_invalid_diffusion_rate_type(self, temp_data_dir):
        """Test that invalid diffusion rate type is handled."""
        output_path = temp_data_dir / "invalid_type.json"
        
        # This should still serialize, but schema validation might catch it
        # depending on schema strictness
        save_simulation_result(
            output_path=output_path,
            network_id="net_001",
            seed=1,
            diffusion_rate="not_a_number",  # Invalid type
            topology_class="er"
        )
        
        # The file should exist
        assert output_path.exists()

    def test_empty_batch(self, temp_data_dir):
        """Test saving an empty batch."""
        output_path = temp_data_dir / "empty_batch.json"
        
        result_path = save_batch_simulation_results(output_path, [])
        
        assert result_path.exists()
        
        loaded = load_simulation_results(output_path)
        assert len(loaded) == 0

    def test_overwrite_behavior(self, temp_data_dir):
        """Test that save_batch_simulation_results overwrites existing file."""
        output_path = temp_data_dir / "overwrite_test.json"
        
        # Save initial batch
        save_batch_simulation_results(
            output_path,
            [{"network_id": "old", "seed": 1, "diffusion_rate": 0.1, "topology_class": "er"}]
        )
        
        # Overwrite with new batch
        save_batch_simulation_results(
            output_path,
            [{"network_id": "new", "seed": 2, "diffusion_rate": 0.2, "topology_class": "sw"}]
        )
        
        loaded = load_simulation_results(output_path)
        assert len(loaded) == 1
        assert loaded[0]["network_id"] == "new"

    def test_malformed_json_handling(self, temp_data_dir):
        """Test handling of malformed JSON in existing file."""
        output_path = temp_data_dir / "malformed.json"
        
        # Create malformed JSON
        with open(output_path, 'w') as f:
            f.write("{ invalid json }")
        
        # Should handle gracefully and create new file
        result_path = save_simulation_result(
            output_path=output_path,
            network_id="net_001",
            seed=1,
            diffusion_rate=0.5,
            topology_class="er"
        )
        
        # Should have created valid JSON
        loaded = load_simulation_results(output_path)
        assert len(loaded) == 1
        assert loaded[0]["network_id"] == "net_001"
