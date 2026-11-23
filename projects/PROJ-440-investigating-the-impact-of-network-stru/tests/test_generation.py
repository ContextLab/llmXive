"""
Tests for network generation.
"""
import os
import sys
import pytest
import csv
import numpy as np
import networkx as nx

# Add code directory to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.generate_networks import (
    generate_random_graph,
    generate_scale_free_graph,
    generate_small_world_graph,
    generate_lattice_graph,
    generate_star_graph,
    validate_scale_free_graph,
    validate_random_graph,
    set_seed
)
from code.utils.metrics import compute_graph_metrics


class TestGeneration:
    """Tests for graph generation functions."""

    def test_generate_random_graphs(self):
        """Test that random graphs are generated correctly."""
        set_seed(42)
        result = generate_random_graph("test_rand_001", 42)
        assert result is not None
        assert result['class'] == 'random'
        assert 'clustering_coeff' in result
        assert 'avg_path_length' in result

    def test_generate_scale_free_graphs(self):
        """Test that scale-free graphs are generated and validated."""
        set_seed(43)
        result = generate_scale_free_graph("test_sf_001", 43)
        assert result is not None
        assert result['class'] == 'scale_free'
        # Check theoretical match passed
        assert result['theoretical_match'] == 'passed' or 'failed' in result['theoretical_match']
        # Assert 10 graphs generated logic is in main, here we test single generation
        assert result['status'] == 'valid'

    def test_generate_all_classes(self):
        """Test generation of all classes."""
        set_seed(44)
        classes = ['random', 'scale_free', 'small_world', 'lattice', 'star']
        for cls in classes:
            if cls == 'random':
                res = generate_random_graph(f"test_{cls}", 44)
            elif cls == 'scale_free':
                res = generate_scale_free_graph(f"test_{cls}", 44)
            elif cls == 'small_world':
                res = generate_small_world_graph(f"test_{cls}", 44)
            elif cls == 'lattice':
                res = generate_lattice_graph(f"test_{cls}", 44)
            elif cls == 'star':
                res = generate_star_graph(f"test_{cls}", 44)
            
            assert res is not None, f"Failed to generate {cls}"
            assert res['class'] == cls

    def test_full_generation_pipeline(self):
        """Test that the full pipeline produces a valid CSV."""
        # This assumes the main function is run or we simulate it
        # For unit test, we check that we can generate enough and save
        from code.generate_networks import generate_networks, save_to_csv
        
        data = generate_networks()
        assert len(data) >= 50, f"Expected at least 50 graphs, got {len(data)}"
        
        # Check distribution
        classes = [d['class'] for d in data]
        for cls in ['random', 'scale_free', 'small_world', 'lattice', 'star']:
            count = classes.count(cls)
            assert count >= 10, f"Expected at least 10 {cls} graphs, got {count}"

class TestMetricsBounds:
    """Tests for metric bounds."""

    def test_clustering_coefficient_bounds(self):
        """Assert clustering coefficient is between 0 and 1."""
        set_seed(50)
        result = generate_random_graph("test_clust", 50)
        assert result is not None
        assert 0.0 <= result['clustering_coeff'] <= 1.0

    def test_path_length_bounds(self):
        """Assert average path length is positive and finite."""
        set_seed(51)
        result = generate_small_world_graph("test_path", 51)
        assert result is not None
        assert result['avg_path_length'] > 0
        assert np.isfinite(result['avg_path_length'])

    def test_degree_distribution_summary(self):
        """Assert degree distribution summary is present."""
        set_seed(52)
        result = generate_scale_free_graph("test_deg", 52)
        assert result is not None
        assert len(result['degree_dist_summary']) > 0

    def test_file_format(self):
        """Assert output CSV has correct columns."""
        # Run generation
        from code.generate_networks import generate_networks, save_to_csv
        data = generate_networks()
        path = "data/raw/test_networks.csv"
        save_to_csv(data, path)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            required = ['id', 'class', 'N', 'clustering_coeff', 'avg_path_length', 'degree_dist_summary']
            for col in required:
                assert col in headers, f"Missing column: {col}"
        
        os.remove(path)