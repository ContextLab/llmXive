"""
Unit tests for compute_features.py
"""
import sys
import math
from pathlib import Path
import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data.compute_features import (
    calculate_bottleneck_resolution_ratio,
    calculate_branching_entropy,
    compute_features_for_node
)


class TestBottleneckResolutionRatio:
    def test_ratio_all_improves(self):
        edges = [{'type': 'improves'}, {'type': 'improves'}, {'type': 'improves'}]
        assert calculate_bottleneck_resolution_ratio(edges) == 1.0

    def test_ratio_all_replaces(self):
        edges = [{'type': 'replaces'}, {'type': 'replaces'}]
        assert calculate_bottleneck_resolution_ratio(edges) == 1.0

    def test_ratio_mixed(self):
        # 2 improves, 1 replaces, 1 other -> 3/4
        edges = [
            {'type': 'improves'},
            {'type': 'replaces'},
            {'type': 'other'},
            {'type': 'improves'}
        ]
        assert calculate_bottleneck_resolution_ratio(edges) == 0.75

    def test_ratio_no_target(self):
        edges = [{'type': 'other'}, {'type': 'unknown'}]
        assert calculate_bottleneck_resolution_ratio(edges) == 0.0

    def test_ratio_empty_edges(self):
        assert calculate_bottleneck_resolution_ratio([]) == 0.0

    def test_ratio_case_insensitive(self):
        edges = [{'type': 'IMPROVES'}, {'type': 'Replaces'}]
        assert calculate_bottleneck_resolution_ratio(edges) == 1.0


class TestBranchingEntropy:
    def test_entropy_uniform_distribution(self):
        # 2 types, equal count -> log2(2) = 1.0
        edges = [
            {'type': 'A'}, {'type': 'A'},
            {'type': 'B'}, {'type': 'B'}
        ]
        entropy = calculate_branching_entropy(edges)
        assert math.isclose(entropy, 1.0, rel_tol=1e-5)

    def test_entropy_single_type(self):
        edges = [{'type': 'A'}, {'type': 'A'}, {'type': 'A'}]
        assert calculate_branching_entropy(edges) == 0.0

    def test_entropy_empty_edges(self):
        assert calculate_branching_entropy([]) == 0.0

    def test_entropy_uneven_distribution(self):
        # 3 A, 1 B -> p(A)=0.75, p(B)=0.25
        # H = - (0.75 * log2(0.75) + 0.25 * log2(0.25))
        edges = [
            {'type': 'A'}, {'type': 'A'}, {'type': 'A'},
            {'type': 'B'}
        ]
        expected = - (0.75 * math.log2(0.75) + 0.25 * math.log2(0.25))
        entropy = calculate_branching_entropy(edges)
        assert math.isclose(entropy, expected, rel_tol=1e-5)

    def test_entropy_three_types(self):
        # 1 A, 1 B, 1 C -> uniform 3 -> log2(3)
        edges = [{'type': 'A'}, {'type': 'B'}, {'type': 'C'}]
        expected = math.log2(3)
        entropy = calculate_branching_entropy(edges)
        assert math.isclose(entropy, expected, rel_tol=1e-5)


class TestComputeFeaturesForNode:
    def test_full_node(self):
        edges = [
            {'type': 'improves'},
            {'type': 'replaces'},
            {'type': 'other'},
            {'type': 'improves'}
        ]
        result = compute_features_for_node("node_123", edges)
        
        assert result['node_id'] == "node_123"
        assert result['bottleneck_resolution_ratio'] == 0.75
        
        # Entropy for 2 improves, 1 replaces, 1 other
        # Counts: improves=2, replaces=1, other=1. Total=4
        # p(im)=0.5, p(rep)=0.25, p(oth)=0.25
        # H = - (0.5*log2(0.5) + 0.25*log2(0.25) + 0.25*log2(0.25))
        #   = - (-0.5 - 0.5 - 0.5) = 1.5
        expected_entropy = - (0.5 * math.log2(0.5) + 0.25 * math.log2(0.25) + 0.25 * math.log2(0.25))
        assert math.isclose(result['branching_entropy'], expected_entropy, rel_tol=1e-5)

    def test_empty_edges_node(self):
        result = compute_features_for_node("node_empty", [])
        assert result['node_id'] == "node_empty"
        assert result['bottleneck_resolution_ratio'] == 0.0
        assert result['branching_entropy'] == 0.0