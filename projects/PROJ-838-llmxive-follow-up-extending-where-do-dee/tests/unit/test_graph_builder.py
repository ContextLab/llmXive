import pytest
import networkx as nx
from pathlib import Path
import json
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph_builder import parse_trajectory, detect_citations, build_dag, save_graph, load_trajectories_from_directory
from config import ensure_directories

class TestParseTrajectory:
    def test_parse_trajectory_basic(self):
        """Test basic span filtering"""
        trajectory = {
            "id": "test_1",
            "spans": [{"id": i, "text": f"span {i}"} for i in range(10)]
        }
        result = parse_trajectory(trajectory, cutoff_depth=0.5)
        assert len(result) == 5
        assert result[0]["id"] == 0
        assert result[4]["id"] == 4

    def test_parse_trajectory_short_trajectory(self):
        """Test handling of short trajectories (cutoff results in 0)"""
        trajectory = {
            "id": "test_2",
            "spans": [{"id": 0, "text": "only one"}]
        }
        result = parse_trajectory(trajectory, cutoff_depth=0.5)
        # Should return all spans when cutoff would result in 0
        assert len(result) == 1

    def test_parse_trajectory_empty(self):
        """Test empty trajectory"""
        trajectory = {"id": "test_3", "spans": []}
        result = parse_trajectory(trajectory, cutoff_depth=0.5)
        assert result == []

    def test_parse_trajectory_missing_spans(self):
        """Test trajectory without spans key"""
        trajectory = {"id": "test_4"}
        result = parse_trajectory(trajectory, cutoff_depth=0.5)
        assert result == []

class TestDetectCitations:
    def test_detect_citations_empty(self):
        """Test with empty spans list"""
        from graph_builder import _nlp, _matcher
        edges = detect_citations([], _nlp, _matcher)
        assert edges == []

    def test_detect_citations_no_pattern(self):
        """Test spans without citation patterns"""
        spans = [{"id": 0, "text": "Hello world"}, {"id": 1, "text": "Goodbye world"}]
        from graph_builder import _nlp, _matcher
        edges = detect_citations(spans, _nlp, _matcher)
        # No citation patterns detected, so no edges
        assert edges == []

    def test_detect_citations_with_pattern(self):
        """Test spans with citation pattern"""
        spans = [
            {"id": 0, "text": "Previous step"},
            {"id": 1, "text": "I cite to the previous step"}
        ]
        from graph_builder import _nlp, _matcher
        edges = detect_citations(spans, _nlp, _matcher)
        # Should detect edge from 1 to 0
        assert (1, 0) in edges

class TestBuildDag:
    def test_build_dag_empty(self):
        """Test building graph from empty spans"""
        graph = build_dag([])
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_build_dag_single_node(self):
        """Test building graph with single span"""
        spans = [{"id": 0, "text": "Only span"}]
        graph = build_dag(spans)
        assert graph.number_of_nodes() == 1
        assert graph.number_of_edges() == 0

    def test_build_dag_multiple_nodes(self):
        """Test building graph with multiple spans"""
        spans = [
            {"id": 0, "text": "Step 1"},
            {"id": 1, "text": "Step 2"},
            {"id": 2, "text": "I cite to the previous step"}
        ]
        graph = build_dag(spans)
        assert graph.number_of_nodes() == 3
        # Should have at least one edge from 2 to 0 or 2 to 1
        assert graph.number_of_edges() >= 1

class TestSaveGraph:
    def test_save_graph_creates_file(self):
        """Test that save_graph creates a JSON file"""
        graph = nx.DiGraph()
        graph.add_node(0, text="test")
        graph.add_edge(0, 1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = save_graph(graph, "test_traj", Path(tmpdir))
            assert output_path.exists()
            assert output_path.suffix == ".json"

    def test_save_graph_content(self):
        """Test that saved JSON contains expected structure"""
        graph = nx.DiGraph()
        graph.add_node(0, text="test")
        graph.add_edge(0, 1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = save_graph(graph, "test_traj", Path(tmpdir))
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert "trajectory_id" in data
            assert data["trajectory_id"] == "test_traj"
            assert "num_nodes" in data
            assert data["num_nodes"] == 2
            assert "num_edges" in data
            assert data["num_edges"] == 1
            assert "graph" in data

class TestLoadTrajectoriesFromDirectory:
    def test_load_from_empty_dir(self):
        """Test loading from directory with no JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            trajectories = load_trajectories_from_directory(Path(tmpdir))
            assert trajectories == []

    def test_load_from_single_file(self):
        """Test loading from directory with single trajectory file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            traj_file = Path(tmpdir) / "test.json"
            with open(traj_file, "w") as f:
                json.dump({"id": "test", "spans": [{"id": 0, "text": "test"}]}, f)
            
            trajectories = load_trajectories_from_directory(Path(tmpdir))
            assert len(trajectories) == 1
            assert trajectories[0]["id"] == "test"

    def test_load_from_list_file(self):
        """Test loading from directory with list of trajectories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            traj_file = Path(tmpdir) / "test.json"
            with open(traj_file, "w") as f:
                json.dump([{"id": "test1", "spans": []}, {"id": "test2", "spans": []}], f)
            
            trajectories = load_trajectories_from_directory(Path(tmpdir))
            assert len(trajectories) == 2
            assert trajectories[0]["id"] == "test1"
            assert trajectories[1]["id"] == "test2"
