"""
Unit tests for simulation result schema validation (T029a).
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from code.src.simulation.schema import (
    validate_simulation_run,
    validate_results_file,
    save_results,
    load_results,
    get_schema,
    SIMULATION_RUN_SCHEMA
)


class TestSimulationRunValidation:
    """Tests for individual simulation run validation."""

    def test_valid_run_entry(self):
        """Test a fully valid simulation run entry."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi"
        }
        assert validate_simulation_run(entry) is True

    def test_missing_required_field_network_id(self):
        """Test validation fails when network_id is missing."""
        entry = {
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="Missing required field: network_id"):
            validate_simulation_run(entry)

    def test_missing_required_field_seed(self):
        """Test validation fails when seed is missing."""
        entry = {
            "network_id": "graph_123",
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="Missing required field: seed"):
            validate_simulation_run(entry)

    def test_missing_required_field_diffusion_rate(self):
        """Test validation fails when diffusion_rate is missing."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="Missing required field: diffusion_rate"):
            validate_simulation_run(entry)

    def test_missing_required_field_topology_class(self):
        """Test validation fails when topology_class is missing."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5
        }
        with pytest.raises(ValueError, match="Missing required field: topology_class"):
            validate_simulation_run(entry)

    def test_invalid_network_id_empty(self):
        """Test validation fails when network_id is empty."""
        entry = {
            "network_id": "",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="network_id must be a non-empty string"):
            validate_simulation_run(entry)

    def test_invalid_seed_negative(self):
        """Test validation fails when seed is negative."""
        entry = {
            "network_id": "graph_123",
            "seed": -1,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="seed must be a non-negative integer"):
            validate_simulation_run(entry)

    def test_invalid_diffusion_rate_zero(self):
        """Test validation fails when diffusion_rate is zero."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.0,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="diffusion_rate must be a positive number"):
            validate_simulation_run(entry)

    def test_invalid_diffusion_rate_negative(self):
        """Test validation fails when diffusion_rate is negative."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": -0.5,
            "topology_class": "ErdosRenyi"
        }
        with pytest.raises(ValueError, match="diffusion_rate must be a positive number"):
            validate_simulation_run(entry)

    def test_invalid_topology_class(self):
        """Test validation fails when topology_class is not in enum."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "InvalidClass"
        }
        with pytest.raises(ValueError, match="topology_class must be one of"):
            validate_simulation_run(entry)

    def test_valid_topology_classes(self):
        """Test all valid topology classes pass validation."""
        valid_classes = ["ErdosRenyi", "WattsStrogatz", "BarabasiAlbert", "Random", "SmallWorld", "ScaleFree"]
        for cls in valid_classes:
            entry = {
                "network_id": "graph_123",
                "seed": 42,
                "diffusion_rate": 0.5,
                "topology_class": cls
            }
            assert validate_simulation_run(entry) is True

    def test_optional_fields_valid(self):
        """Test entry with all optional fields passes validation."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi",
            "num_nodes": 100,
            "num_edges": 200,
            "clustering_coefficient": 0.45,
            "average_path_length": 3.2,
            "simulation_steps": 100,
            "energy_density_final": 0.8,
            "spatial_variance_final": 0.12,
            "stability_check_passed": True,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        assert validate_simulation_run(entry) is True

    def test_invalid_clustering_coefficient_range(self):
        """Test validation fails when clustering_coefficient is out of range."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi",
            "clustering_coefficient": 1.5
        }
        with pytest.raises(ValueError, match="clustering_coefficient must be between 0.0 and 1.0"):
            validate_simulation_run(entry)

    def test_invalid_spatial_variance_negative(self):
        """Test validation fails when spatial_variance_final is negative."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi",
            "spatial_variance_final": -0.1
        }
        with pytest.raises(ValueError, match="spatial_variance_final must be non-negative"):
            validate_simulation_run(entry)

    def test_unexpected_field(self):
        """Test validation fails when unexpected field is present."""
        entry = {
            "network_id": "graph_123",
            "seed": 42,
            "diffusion_rate": 0.5,
            "topology_class": "ErdosRenyi",
            "unexpected_field": "value"
        }
        with pytest.raises(ValueError, match="Unexpected fields"):
            validate_simulation_run(entry)


class TestResultsFileValidation:
    """Tests for full results file validation."""

    def test_valid_results_list(self):
        """Test a valid list of simulation runs."""
        results = [
            {
                "network_id": "graph_123",
                "seed": 42,
                "diffusion_rate": 0.5,
                "topology_class": "ErdosRenyi"
            },
            {
                "network_id": "graph_456",
                "seed": 123,
                "diffusion_rate": 0.7,
                "topology_class": "WattsStrogatz"
            }
        ]
        assert validate_results_file(results) is True

    def test_empty_results_list(self):
        """Test validation fails for empty list."""
        with pytest.raises(ValueError, match="Results list cannot be empty"):
            validate_results_file([])

    def test_non_list_input(self):
        """Test validation fails when input is not a list."""
        with pytest.raises(ValueError, match="Results must be a list"):
            validate_results_file({"network_id": "graph_123"})

    def test_invalid_entry_in_list(self):
        """Test validation fails when one entry in list is invalid."""
        results = [
            {
                "network_id": "graph_123",
                "seed": 42,
                "diffusion_rate": 0.5,
                "topology_class": "ErdosRenyi"
            },
            {
                "network_id": "graph_456",
                "seed": -1,  # Invalid
                "diffusion_rate": 0.7,
                "topology_class": "WattsStrogatz"
            }
        ]
        with pytest.raises(ValueError, match="Validation failed for entry 1"):
            validate_results_file(results)


class TestSaveAndLoadResults:
    """Tests for saving and loading results to/from JSON."""

    def test_save_and_load_valid(self):
        """Test saving and loading valid results."""
        results = [
            {
                "network_id": "graph_123",
                "seed": 42,
                "diffusion_rate": 0.5,
                "topology_class": "ErdosRenyi"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_results(results, temp_path)
            loaded = load_results(temp_path)
            assert len(loaded) == 1
            assert loaded[0]["network_id"] == "graph_123"
            assert loaded[0]["seed"] == 42
            assert loaded[0]["diffusion_rate"] == 0.5
            assert loaded[0]["topology_class"] == "ErdosRenyi"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_save_invalid_fails(self):
        """Test that saving invalid results raises ValueError."""
        results = [
            {
                "network_id": "graph_123",
                "seed": -1,  # Invalid
                "diffusion_rate": 0.5,
                "topology_class": "ErdosRenyi"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                save_results(results, temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_results("/nonexistent/path/results.json")

    def test_load_invalid_json(self):
        """Test loading invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_results(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_valid_then_invalid(self):
        """Test loading valid file then modifying to be invalid."""
        results = [
            {
                "network_id": "graph_123",
                "seed": 42,
                "diffusion_rate": 0.5,
                "topology_class": "ErdosRenyi"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_results(results, temp_path)
            # Corrupt the file
            with open(temp_path, 'w') as f:
                f.write('{"network_id": "graph_123"}')  # Missing required fields
            
            with pytest.raises(ValueError):
                load_results(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestSchemaRetrieval:
    """Tests for schema retrieval functions."""

    def test_get_schema_returns_dict(self):
        """Test that get_schema returns a dictionary."""
        schema = get_schema()
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert "title" in schema
        assert schema["title"] == "SimulationRun"

    def test_get_results_schema_returns_array_schema(self):
        """Test that get_results_schema returns array schema."""
        schema = get_results_schema()
        assert isinstance(schema, dict)
        assert schema["type"] == "array"
        assert "items" in schema