"""
Unit tests to verify that the conftest fixtures and path configurations work correctly.
"""
import os
from pathlib import Path

def test_seed_fixture(seed):
    """Verify the seed fixture returns an integer."""
    assert isinstance(seed, int)
    assert seed > 0


def test_temp_data_dir_fixture(temp_data_dir):
    """Verify the temp_data_dir fixture creates a valid directory."""
    assert isinstance(temp_data_dir, Path)
    assert temp_data_dir.exists()
    assert temp_data_dir.is_dir()


def test_temp_artifact_dir_fixture(temp_artifact_dir):
    """Verify the temp_artifact_dir fixture creates a valid directory."""
    assert isinstance(temp_artifact_dir, Path)
    assert temp_artifact_dir.exists()
    assert temp_artifact_dir.is_dir()


def test_sample_graph_fixture(sample_graph_dir):
    """Verify the sample_graph_dir fixture creates a valid graph file."""
    graph_file = sample_graph_dir / "sample_graph.json"
    assert graph_file.exists()
    assert graph_file.stat().st_size > 0

    # Verify content is valid JSON
    import json
    with open(graph_file) as f:
        data = json.load(f)
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2

def test_environment_variable_seed():
    """Verify that PYTHONHASHSEED is set during test configuration."""
    # This checks that the pytest_configure hook ran
    assert os.environ.get("PYTHONHASHSEED") is not None