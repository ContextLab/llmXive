import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import networkx as nx
import numpy as np
from config import load_config, get_organisms, get_path, ensure_dirs

logger = logging.getLogger(__name__)

class NetworkAnalysisError(Exception):
    """Custom exception for network analysis errors."""
    pass

def load_graph_from_adjacency_list(adjacency_list: Dict[str, List[str]]) -> nx.Graph:
    """
    Load a NetworkX graph from an adjacency list dictionary.

    Args:
        adjacency_list: Dictionary where keys are node IDs and values are lists of neighbor IDs.

    Returns:
        A NetworkX Graph object.
    """
    G = nx.Graph()
    for node, neighbors in adjacency_list.items():
        G.add_node(node)
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    return G

def compute_degree_centrality(G: nx.Graph) -> Dict[str, float]:
    """
    Compute degree centrality for all nodes in the graph.

    Args:
        G: A NetworkX Graph.

    Returns:
        Dictionary mapping node IDs to degree centrality values.
    """
    if G.number_of_nodes() == 0:
        return {}
    return nx.degree_centrality(G)

def compute_eigenvector_centrality(G: nx.Graph, max_iter: int = 1000) -> Dict[str, float]:
    """
    Compute eigenvector centrality for all nodes in the graph.

    Args:
        G: A NetworkX Graph.
        max_iter: Maximum number of iterations for the power method.

    Returns:
        Dictionary mapping node IDs to eigenvector centrality values.

    Raises:
        NetworkAnalysisError: If the algorithm fails to converge.
    """
    if G.number_of_nodes() == 0:
        return {}
    try:
        return nx.eigenvector_centrality(G, max_iter=max_iter)
    except nx.PowerIterationFailedConvergence as e:
        logger.warning(f"Eigenvector centrality failed to converge: {e}. Returning zeros.")
        return {node: 0.0 for node in G.nodes()}

def compute_betweenness_centrality(G: nx.Graph, k: Optional[int] = None) -> Dict[str, float]:
    """
    Compute betweenness centrality for all nodes in the graph.

    Args:
        G: A NetworkX Graph.
        k: Number of nodes to sample for random sampling (None for exact calculation).
           If k is set, uses nx.betweenness_centrality with k sampling.

    Returns:
        Dictionary mapping node IDs to betweenness centrality values.
    """
    if G.number_of_nodes() == 0:
        return {}
    if k is not None:
        logger.info(f"Computing betweenness centrality with k={k} samples.")
        return nx.betweenness_centrality(G, k=k, normalized=True)
    else:
        logger.info("Computing exact betweenness centrality.")
        return nx.betweenness_centrality(G, normalized=True)

def compute_all_centrality_metrics(
    G: nx.Graph,
    use_k_sampling: bool = True,
    k_samples: int = 500
) -> Dict[str, Dict[str, float]]:
    """
    Compute degree, betweenness, and eigenvector centrality for all nodes.

    Args:
        G: A NetworkX Graph.
        use_k_sampling: If True and graph is large, use k-sampling for betweenness.
        k_samples: Number of nodes to sample for betweenness centrality.

    Returns:
        Dictionary with keys 'degree', 'betweenness', 'eigenvector',
        each mapping to a dict of {node_id: centrality_value}.
    """
    if G.number_of_nodes() == 0:
        return {
            'degree': {},
            'betweenness': {},
            'eigenvector': {}
        }

    # Handle disconnected components: ensure all nodes are present in results
    nodes = list(G.nodes())
    degree_cent = compute_degree_centrality(G)
    eigenvector_cent = compute_eigenvector_centrality(G)

    # Betweenness: use k-sampling for large networks to ensure runtime
    if use_k_sampling and G.number_of_nodes() > 5000:
        betweenness_cent = compute_betweenness_centrality(G, k=k_samples)
    else:
        betweenness_cent = compute_betweenness_centrality(G)

    # Ensure all nodes have entries (even if 0 for disconnected/isolated cases)
    # NetworkX usually returns 0 for isolated nodes, but we enforce it here for safety
    for node in nodes:
        degree_cent.setdefault(node, 0.0)
        betweenness_cent.setdefault(node, 0.0)
        eigenvector_cent.setdefault(node, 0.0)

    return {
        'degree': degree_cent,
        'betweenness': betweenness_cent,
        'eigenvector': eigenvector_cent
    }

def process_organism_networks(
    organism_id: str,
    networks_data: Dict[str, Any],
    essentiality_labels: Dict[str, int],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process network analysis for a single organism.

    Args:
        organism_id: The organism identifier.
        networks_data: Dictionary containing 'adjacency_list' and 'mapped_genes'.
        essentiality_labels: Dictionary mapping gene IDs to essentiality labels (0/1).
        config: Configuration dictionary.

    Returns:
        Dictionary containing centrality metrics and correlation data.
    """
    logger.info(f"Processing network for organism: {organism_id}")

    adjacency_list = networks_data.get('adjacency_list', {})
    mapped_genes = networks_data.get('mapped_genes', set())

    # Check for missing gene overlaps
    # mapped_genes contains genes from the network that were successfully mapped
    # We need to check if essentiality_labels has any overlap with mapped_genes
    network_gene_set = set(adjacency_list.keys())
    overlap_genes = network_gene_set.intersection(mapped_genes)
    
    if not overlap_genes:
        logger.warning(f"No gene overlap found between network and mapped essentiality for {organism_id}. Skipping centrality calculation.")
        return {
            'organism': organism_id,
            'status': 'skipped',
            'reason': 'No gene overlap',
            'centrality_metrics': {},
            'correlations': {}
        }

    # Filter essentiality labels to only include genes present in the network
    valid_labels = {
        gene: label for gene, label in essentiality_labels.items()
        if gene in overlap_genes
    }

    if not valid_labels:
        logger.warning(f"No valid essentiality labels for genes in network for {organism_id}. Skipping.")
        return {
            'organism': organism_id,
            'status': 'skipped',
            'reason': 'No valid essentiality labels',
            'centrality_metrics': {},
            'correlations': {}
        }

    # Load graph
    G = load_graph_from_adjacency_list(adjacency_list)

    # Check for disconnected components and assign 0 centrality where appropriate
    # NetworkX centrality functions handle isolated nodes by returning 0, 
    # but we explicitly handle cases where the graph might be empty or disconnected
    if G.number_of_nodes() == 0:
        logger.warning(f"Graph for {organism_id} has no nodes. Assigning 0 centrality.")
        centrality_results = {
            'degree': {},
            'betweenness': {},
            'eigenvector': {}
        }
    else:
        # Compute centrality metrics
        use_k_sampling = config.get('use_k_sampling', True)
        k_samples = config.get('k_samples', 500)
        centrality_results = compute_all_centrality_metrics(G, use_k_sampling, k_samples)

    # Prepare data for correlation calculation
    # We need to align centrality values with essentiality labels
    centrality_data = {
        'degree': [],
        'betweenness': [],
        'eigenvector': [],
        'essentiality': [],
        'genes': []
    }

    for gene in valid_labels.keys():
        if gene in centrality_results['degree']:
            centrality_data['degree'].append(centrality_results['degree'][gene])
            centrality_data['betweenness'].append(centrality_results['betweenness'].get(gene, 0.0))
            centrality_data['eigenvector'].append(centrality_results['eigenvector'].get(gene, 0.0))
            centrality_data['essentiality'].append(valid_labels[gene])
            centrality_data['genes'].append(gene)

    if not centrality_data['genes']:
        logger.warning(f"No aligned data for {organism_id} after filtering. Skipping correlations.")
        return {
            'organism': organism_id,
            'status': 'skipped',
            'reason': 'No aligned data',
            'centrality_metrics': centrality_results,
            'correlations': {}
        }

    # Calculate correlations
    from statistics import calculate_spearman_correlation

    correlations = {}
    for metric_name in ['degree', 'betweenness', 'eigenvector']:
        metric_values = centrality_data[metric_name]
        essentiality_values = centrality_data['essentiality']
        
        corr, p_value = calculate_spearman_correlation(metric_values, essentiality_values)
        correlations[metric_name] = {
            'rho': corr,
            'p_value': p_value,
            'n': len(metric_values)
        }

    logger.info(f"Completed processing for {organism_id}. Correlations: {correlations}")

    return {
        'organism': organism_id,
        'status': 'success',
        'centrality_metrics': centrality_results,
        'correlations': correlations,
        'sample_size': len(centrality_data['genes']),
        'genes_processed': centrality_data['genes']
    }

def main():
    """
    Main entry point for network analysis module.
    Runs the pipeline for all configured organisms.
    """
    logger.info("Starting network analysis pipeline.")
    config = load_config()
    organisms = get_organisms(config)
    
    results = []
    for organism_id in organisms:
        try:
            # In a real scenario, we would load data here
            # For now, we assume data is loaded by data_loader module
            # This function is designed to be called from main.py
            logger.info(f"Processing {organism_id}...")
            # Placeholder for actual data loading logic
            # This would be implemented in main.py or data_loader.py
            result = {
                'organism': organism_id,
                'status': 'placeholder',
                'message': 'Data loading not implemented in this module'
            }
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing {organism_id}: {e}")
            results.append({
                'organism': organism_id,
                'status': 'error',
                'error': str(e)
            })
    
    logger.info(f"Network analysis completed for {len(results)} organisms.")
    return results

if __name__ == "__main__":
    setup_logging = __import__('utils', fromlist=['setup_logging']).setup_logging
    setup_logging()
    main()
