import pytest
import networkx as nx
from code.network_analysis import (
    load_graph_from_adjacency_list,
    compute_degree_centrality,
    compute_eigenvector_centrality,
    compute_betweenness_centrality,
    compute_all_centrality_metrics,
    process_organism_networks
)

def test_load_graph_from_adjacency_list():
    """Test graph loading from adjacency list."""
    adj_list = {
        'A': ['B', 'C'],
        'B': ['A'],
        'C': ['A']
    }
    G = load_graph_from_adjacency_list(adj_list)
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 2
    assert 'A' in G.nodes()
    assert 'B' in G.nodes()
    assert 'C' in G.nodes()

def test_compute_degree_centrality():
    """Test degree centrality computation."""
    G = nx.Graph()
    G.add_edges_from([('A', 'B'), ('A', 'C'), ('B', 'C')])
    centrality = compute_degree_centrality(G)
    assert centrality['A'] == pytest.approx(1.0)
    assert centrality['B'] == pytest.approx(0.5)
    assert centrality['C'] == pytest.approx(0.5)

def test_compute_degree_centrality_empty_graph():
    """Test degree centrality on empty graph returns empty dict."""
    G = nx.Graph()
    centrality = compute_degree_centrality(G)
    assert centrality == {}

def test_compute_eigenvector_centrality():
    """Test eigenvector centrality computation."""
    G = nx.Graph()
    G.add_edges_from([('A', 'B'), ('A', 'C'), ('B', 'C')])
    centrality = compute_eigenvector_centrality(G)
    assert 'A' in centrality
    assert 'B' in centrality
    assert 'C' in centrality

def test_compute_eigenvector_centrality_disconnected():
    """Test eigenvector centrality on disconnected graph."""
    G = nx.Graph()
    G.add_edges_from([('A', 'B'), ('C', 'D')])  # Two disconnected components
    centrality = compute_eigenvector_centrality(G)
    # Should not raise, and should return values for all nodes
    assert len(centrality) == 4

def test_compute_betweenness_centrality():
    """Test betweenness centrality computation."""
    G = nx.Graph()
    G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
    centrality = compute_betweenness_centrality(G)
    # B and C should have higher betweenness than A and D
    assert centrality['B'] > centrality['A']
    assert centrality['C'] > centrality['D']

def test_compute_betweenness_centrality_k_sampling():
    """Test betweenness centrality with k-sampling."""
    G = nx.Graph()
    G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
    centrality = compute_betweenness_centrality(G, k=2)
    assert len(centrality) == 4

def test_compute_all_centrality_metrics():
    """Test all centrality metrics computation."""
    G = nx.Graph()
    G.add_edges_from([('A', 'B'), ('A', 'C'), ('B', 'C')])
    results = compute_all_centrality_metrics(G)
    assert 'degree' in results
    assert 'betweenness' in results
    assert 'eigenvector' in results
    assert len(results['degree']) == 3
    assert len(results['betweenness']) == 3
    assert len(results['eigenvector']) == 3

def test_process_organism_networks_no_overlap():
    """Test processing when no gene overlap exists."""
    networks_data = {
        'adjacency_list': {'A': ['B'], 'B': ['A']},
        'mapped_genes': set()  # Empty mapped genes
    }
    essentiality_labels = {'C': 1, 'D': 0}  # No overlap with network
    config = {'use_k_sampling': True, 'k_samples': 100}
    
    result = process_organism_networks('test_org', networks_data, essentiality_labels, config)
    assert result['status'] == 'skipped'
    assert result['reason'] == 'No gene overlap'

def test_process_organism_networks_empty_labels():
    """Test processing when no valid essentiality labels exist."""
    networks_data = {
        'adjacency_list': {'A': ['B'], 'B': ['A']},
        'mapped_genes': {'A', 'B'}
    }
    essentiality_labels = {}  # Empty labels
    config = {'use_k_sampling': True, 'k_samples': 100}
    
    result = process_organism_networks('test_org', networks_data, essentiality_labels, config)
    assert result['status'] == 'skipped'
    assert result['reason'] == 'No valid essentiality labels'

def test_process_organism_networks_disconnected_nodes():
    """Test that disconnected nodes get 0 centrality."""
    networks_data = {
        'adjacency_list': {
            'A': ['B'],
            'B': ['A'],
            'C': []  # Isolated node
        },
        'mapped_genes': {'A', 'B', 'C'}
    }
    essentiality_labels = {'A': 1, 'B': 0, 'C': 1}
    config = {'use_k_sampling': True, 'k_samples': 100}
    
    result = process_organism_networks('test_org', networks_data, essentiality_labels, config)
    assert result['status'] == 'success'
    # Check that isolated node C has 0 centrality
    assert result['centrality_metrics']['degree'].get('C', 0) == 0.0
    assert result['centrality_metrics']['betweenness'].get('C', 0) == 0.0
    assert result['centrality_metrics']['eigenvector'].get('C', 0) == 0.0

def test_process_organism_networks_successful():
    """Test successful processing with valid data."""
    networks_data = {
        'adjacency_list': {
            'A': ['B', 'C'],
            'B': ['A', 'C'],
            'C': ['A', 'B']
        },
        'mapped_genes': {'A', 'B', 'C'}
    }
    essentiality_labels = {'A': 1, 'B': 0, 'C': 1}
    config = {'use_k_sampling': True, 'k_samples': 100}
    
    result = process_organism_networks('test_org', networks_data, essentiality_labels, config)
    assert result['status'] == 'success'
    assert 'correlations' in result
    assert 'degree' in result['correlations']
    assert 'betweenness' in result['correlations']
    assert 'eigenvector' in result['correlations']
    assert result['correlations']['degree']['n'] == 3
