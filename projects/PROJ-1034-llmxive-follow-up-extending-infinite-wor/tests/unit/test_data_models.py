"""
Unit tests for the base data models in src/data_models.py.
"""

import pytest
from datetime import datetime
from src.data_models import SimulationRun, MetricRecord, ParameterGrid


class TestSimulationRun:
    def test_creation(self):
        """Test basic creation of a SimulationRun."""
        run = SimulationRun(
            run_id="test-001",
            config_hash="abc123",
            start_time=datetime(2023, 1, 1, 12, 0, 0)
        )
        assert run.run_id == "test-001"
        assert run.config_hash == "abc123"
        assert run.status == "running"
        assert run.end_time is None

    def test_to_dict(self):
        """Test conversion to dictionary."""
        run = SimulationRun(
            run_id="test-002",
            config_hash="def456",
            start_time=datetime(2023, 1, 2, 10, 0, 0),
            end_time=datetime(2023, 1, 2, 10, 5, 0),
            status="completed",
            parameters={"lr": 0.01},
            metrics_path="data/metrics.json"
        )
        d = run.to_dict()
        assert d["run_id"] == "test-002"
        assert d["status"] == "completed"
        assert d["parameters"]["lr"] == 0.01
        assert d["metrics_path"] == "data/metrics.json"

    def test_round_trip(self):
        """Test serialization and deserialization."""
        original = SimulationRun(
            run_id="test-003",
            config_hash="ghi789",
            start_time=datetime(2023, 1, 3, 8, 0, 0),
            parameters={"temp": 0.5}
        )
        json_str = original.to_json()
        restored = SimulationRun.from_dict(eval(json_str.replace("datetime", "datetime.datetime").replace("isoformat()", "'")[:-1])) # Simplified for test
        # Proper JSON round trip would require custom encoder/decoder, testing dict round trip here
        d = original.to_dict()
        restored = SimulationRun.from_dict(d)
        assert restored.run_id == original.run_id
        assert restored.config_hash == original.config_hash
        assert restored.parameters == original.parameters


class TestMetricRecord:
    def test_creation(self):
        """Test basic creation of a MetricRecord."""
        metric = MetricRecord(
            run_id="test-001",
            step=10,
            metric_name="coherence_score",
            value=0.85
        )
        assert metric.run_id == "test-001"
        assert metric.step == 10
        assert metric.metric_name == "coherence_score"
        assert metric.value == 0.85

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metric = MetricRecord(
            run_id="test-001",
            step=100,
            metric_name="latency",
            value=0.05,
            tags=["baseline", "neural"],
            metadata={"unit": "seconds"}
        )
        d = metric.to_dict()
        assert d["metric_name"] == "latency"
        assert d["value"] == 0.05
        assert "baseline" in d["tags"]
        assert d["metadata"]["unit"] == "seconds"

    def test_default_timestamp(self):
        """Test that timestamp defaults to now."""
        before = datetime.now()
        metric = MetricRecord(run_id="test-001", metric_name="test", value=1.0)
        after = datetime.now()
        assert before <= metric.timestamp <= after


class TestParameterGrid:
    def test_creation(self):
        """Test basic creation of a ParameterGrid."""
        grid = ParameterGrid(
            name="test_grid",
            parameters={"lr": [0.01, 0.1], "batch_size": [32, 64]}
        )
        assert grid.name == "test_grid"
        assert len(grid.parameters["lr"]) == 2

    def test_generate_combinations(self):
        """Test generation of all parameter combinations."""
        grid = ParameterGrid(
            name="small_grid",
            parameters={"a": [1, 2], "b": ["x", "y"]}
        )
        combos = grid.generate_combinations()
        assert len(combos) == 4
        expected = [
            {"a": 1, "b": "x"},
            {"a": 1, "b": "y"},
            {"a": 2, "b": "x"},
            {"a": 2, "b": "y"}
        ]
        assert combos == expected

    def test_empty_parameters(self):
        """Test grid with empty parameter lists."""
        grid = ParameterGrid(name="empty", parameters={})
        combos = grid.generate_combinations()
        assert combos == [{}]

    def test_to_dict_round_trip(self):
        """Test serialization and deserialization."""
        original = ParameterGrid(
            name="round_trip",
            parameters={"x": [1, 2]},
            description="Test desc",
            tags=["test"]
        )
        d = original.to_dict()
        restored = ParameterGrid.from_dict(d)
        assert restored.name == original.name
        assert restored.parameters == original.parameters
        assert restored.description == original.description