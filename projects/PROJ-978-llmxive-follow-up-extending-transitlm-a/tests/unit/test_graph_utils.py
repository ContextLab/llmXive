import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.graph_utils import (
    build_route_graph,
    load_ground_truth,
    compute_edge_overlap,
    validate_graph_against_ground_truth,
    compute_path_betweenness_centrality,
    compute_route_complexity_metrics
)


class TestBuildRouteGraph:
    def test_basic_graph_building(self):
        routes = [
            ["A", "B", "C"],
            ["B", "D", "E"]
        ]
        graph = build_route_graph(routes)
        
        assert "A" in graph
        assert "B" in graph["A"]
        assert "C" in graph["B"]
        assert "D" in graph["B"]
        assert "E" in graph["D"]
    
    def test_empty_routes(self):
        routes = []
        graph = build_route_graph(routes)
        assert graph == {}
    
    def test_single_station_route(self):
        routes = [["A"]]
        graph = build_route_graph(routes)
        assert graph == {}
    
    def test_two_station_route(self):
        routes = [["A", "B"]]
        graph = build_route_graph(routes)
        assert "A" in graph
        assert "B" in graph["A"]
        assert "A" in graph["B"]


class TestLoadGroundTruth:
    def test_load_ground_truth(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"from": "A", "to": "B", "count": 10},
                {"from": "B", "to": "C", "count": 20}
            ], f)
            temp_path = f.name
        
        try:
            edges = load_ground_truth(temp_path)
            assert ("A", "B") in edges
            assert ("B", "C") in edges
            assert len(edges) == 2
        finally:
            Path(temp_path).unlink()
    
    def test_normalized_edges(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"from": "B", "to": "A", "count": 10}
            ], f)
            temp_path = f.name
        
        try:
            edges = load_ground_truth(temp_path)
            assert ("A", "B") in edges
        finally:
            Path(temp_path).unlink()


class TestComputeEdgeOverlap:
    def test_complete_overlap(self):
        built_graph = {
            "A": {"B"},
            "B": {"A", "C"},
            "C": {"B"}
        }
        ground_truth = {("A", "B"), ("B", "C")}
        
        overlap = compute_edge_overlap(built_graph, ground_truth)
        assert overlap == 1.0
    
    def test_no_overlap(self):
        built_graph = {
            "A": {"B"},
            "B": {"A"}
        }
        ground_truth = {("C", "D"), ("D", "E")}
        
        overlap = compute_edge_overlap(built_graph, ground_truth)
        assert overlap == 0.0
    
    def test_partial_overlap(self):
        built_graph = {
            "A": {"B", "C"},
            "B": {"A"},
            "C": {"A"}
        }
        ground_truth = {("A", "B")}
        
        overlap = compute_edge_overlap(built_graph, ground_truth)
        assert overlap == 0.5  # 1 out of 2 edges overlap
    
    def test_empty_built_graph(self):
        built_graph = {}
        ground_truth = {("A", "B")}
        
        overlap = compute_edge_overlap(built_graph, ground_truth)
        assert overlap == 0.0


class TestValidateGraphAgainstGroundTruth:
    def test_validation_pass(self):
        routes = [
            ["A", "B", "C"],
            ["C", "D"]
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"from": "A", "to": "B", "count": 10},
                {"from": "B", "to": "C", "count": 10},
                {"from": "C", "to": "D", "count": 10}
            ], f)
            temp_path = f.name
        
        try:
            is_valid, details = validate_graph_against_ground_truth(routes, temp_path, threshold=0.95)
            assert is_valid
            assert details["overlap_ratio"] == 1.0
        finally:
            Path(temp_path).unlink()
    
    def test_validation_fail(self):
        routes = [
            ["A", "B"],
            ["C", "D"]
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"from": "X", "to": "Y", "count": 10}
            ], f)
            temp_path = f.name
        
        try:
            is_valid, details = validate_graph_against_ground_truth(routes, temp_path, threshold=0.95)
            assert not is_valid
            assert details["overlap_ratio"] == 0.0
        finally:
            Path(temp_path).unlink()


class TestComputePathBetweennessCentrality:
    def test_basic_centrality(self):
        routes = [
            ["A", "B", "C", "D"],
            ["E", "B", "F"]
        ]
        centrality = compute_path_betweenness_centrality(routes)
        
        # B appears as intermediate in both routes
        assert centrality.get("B", 0) > 0
        # A, C, D, E, F are not intermediates
        assert centrality.get("A", 0) == 0
        assert centrality.get("C", 0) == 0
    
    def test_empty_routes(self):
        centrality = compute_path_betweenness_centrality([])
        assert centrality == {}
    
    def test_short_routes(self):
        routes = [
            ["A", "B"],
            ["C"]
        ]
        centrality = compute_path_betweenness_centrality(routes)
        assert centrality == {}


class TestComputeRouteComplexityMetrics:
    def test_basic_metrics(self):
        routes = [
            ["A", "B", "C", "D"],
            ["E", "F"]
        ]
        metrics = compute_route_complexity_metrics(routes)
        
        assert len(metrics) == 2
        assert metrics[0]["length"] == 4
        assert metrics[1]["length"] == 2
        assert metrics[0]["complexity_score"] >= 0
        assert metrics[1]["complexity_score"] == 0  # No intermediate nodes
    
    def test_empty_routes(self):
        metrics = compute_route_complexity_metrics([])
        assert metrics == []