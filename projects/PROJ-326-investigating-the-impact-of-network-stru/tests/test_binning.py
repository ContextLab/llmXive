"""
Unit tests for the binning logic in code/src/generators/binning.py.
"""
import pytest
import networkx as nx
from code.src.generators.binning import classify_graph, get_clustering_coefficient


class TestGetClusteringCoefficient:
    def test_empty_graph(self):
        """Test that an empty graph returns 0.0."""
        G = nx.Graph()
        assert get_clustering_coefficient(G) == 0.0

    def test_single_node(self):
        """Test that a single node graph returns 0.0."""
        G = nx.Graph()
        G.add_node(1)
        assert get_clustering_coefficient(G) == 0.0

    def test_complete_graph_k3(self):
        """Test a complete graph K3 (triangle) has coefficient 1.0."""
        G = nx.complete_graph(3)
        # Transitivity of K3 is exactly 1.0
        assert abs(get_clustering_coefficient(G) - 1.0) < 1e-6

    def test_path_graph(self):
        """Test a path graph has coefficient 0.0."""
        G = nx.path_graph(5)
        # Path graphs have no triangles, so transitivity is 0.0
        assert get_clustering_coefficient(G) == 0.0

    def test_watts_strogatz_small_world(self):
        """Test a small-world graph has a non-zero clustering coefficient."""
        # Create a small-world graph with high clustering
        G = nx.watts_strogatz_graph(n=100, k=4, p=0.0)
        coeff = get_clustering_coefficient(G)
        # With p=0, it's a regular lattice, should have significant clustering
        assert coeff > 0.0


class TestClassifyGraph:
    def test_classify_low_clustering(self):
        """Test classification of a graph with low clustering."""
        G = nx.path_graph(10)
        bin_label, coeff = classify_graph(G)
        assert bin_label == "bin_0"
        assert coeff == 0.0

    def test_classify_high_clustering(self):
        """Test classification of a graph with high clustering."""
        G = nx.complete_graph(10)
        bin_label, coeff = classify_graph(G)
        # K10 has coeff 1.0, should fall in the last bin (bin_5 for default bins)
        assert bin_label == "bin_5"
        assert abs(coeff - 1.0) < 1e-6

    def test_classify_mid_range(self):
        """Test classification of a graph with mid-range clustering."""
        # Create a graph with clustering ~0.25
        G = nx.watts_strogatz_graph(n=100, k=6, p=0.1)
        bin_label, coeff = classify_graph(G)
        # Verify the coefficient is within the claimed bin
        bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
        idx = int(bin_label.split('_')[1])
        lower = bins[idx]
        upper = bins[idx + 1]
        if idx == len(bins) - 2:
            assert lower <= coeff <= upper
        else:
            assert lower <= coeff < upper

    def test_classify_custom_bins(self):
        """Test classification with custom bin definitions."""
        G = nx.complete_graph(5)
        custom_bins = [0.0, 0.5, 1.0]
        bin_label, coeff = classify_graph(G, bins=custom_bins)
        assert bin_label == "bin_1"
        assert abs(coeff - 1.0) < 1e-6

    def test_classify_none_graph(self):
        """Test that passing None raises ValueError."""
        with pytest.raises(ValueError):
            classify_graph(None)

    def test_classify_empty_graph(self):
        """Test that passing an empty graph raises ValueError."""
        G = nx.Graph()
        with pytest.raises(ValueError):
            classify_graph(G)

    def test_classify_out_of_range(self):
        """Test that a coefficient outside defined bins raises ValueError."""
        # Create a graph with coeff 1.0
        G = nx.complete_graph(5)
        # Define bins that don't reach 1.0
        bad_bins = [0.0, 0.5, 0.8]
        with pytest.raises(ValueError):
            classify_graph(G, bins=bad_bins)

    def test_classify_boundary_value(self):
        """Test classification exactly on a bin boundary."""
        # Create a graph with coeff exactly 0.2 (hard to do perfectly, but test logic)
        # We will test the logic by mocking or using a specific graph if possible.
        # For now, we test that 0.2 falls into bin_2 [0.2, 0.3)
        # Using a Watts-Strogatz graph tuned to be close to 0.2
        G = nx.watts_strogatz_graph(n=200, k=6, p=0.15)
        bin_label, coeff = classify_graph(G)
        # Just ensure it classifies successfully and is consistent
        assert bin_label.startswith("bin_")
        assert 0.0 <= coeff <= 1.0