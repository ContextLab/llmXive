"""
Topology Extractor for GraphCompass.

Calculates topological metrics (modularity, avg path length, centrality)
and extracts features for the entire corpus or specific retrieved documents.
"""
import json
import logging
import networkx as nx
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

from code.config import PROCESSED_DIR, RESULTS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_graphs(graphs_path: Optional[Path] = None) -> Dict[str, nx.Graph]:
    """Load pre-computed graphs from JSON."""
    if graphs_path is None:
        graphs_path = PROCESSED_DIR / "graphs.json"

    logger.info(f"Loading graphs from {graphs_path}")
    with open(graphs_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    graphs = {}
    for doc_id, graph_data in data.items():
        G = nx.Graph()
        G.add_nodes_from(graph_data['nodes'])
        G.add_edges_from(graph_data['edges'])
        graphs[doc_id] = G
    
    logger.info(f"Loaded {len(graphs)} graphs")
    return graphs


def calculate_topological_metrics(G: nx.Graph) -> Dict[str, float]:
    """
    Calculate topological metrics for a single graph.
    
    Returns a dictionary with:
    - modularity
    - average_path_length
    - average_degree
    - average_betweenness_centrality
    """
    metrics = {}
    
    if G.number_of_nodes() == 0:
        return {
            'modularity': 0.0,
            'average_path_length': 0.0,
            'average_degree': 0.0,
            'average_betweenness_centrality': 0.0
        }

    # Modularity (requires communities, use greedy modularity optimization)
    try:
        if G.number_of_edges() > 0:
            # Use greedy modularity optimization to get communities
            communities = list(nx.community.greedy_modularity_communities(G))
            if len(communities) > 1:
                metrics['modularity'] = nx.community.modularity(G, communities)
            else:
                metrics['modularity'] = 0.0
        else:
            metrics['modularity'] = 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate modularity: {e}")
        metrics['modularity'] = 0.0

    # Average Path Length
    if nx.is_connected(G):
        try:
            avg_path = nx.average_shortest_path_length(G)
            metrics['average_path_length'] = avg_path
        except Exception as e:
            logger.warning(f"Failed to calculate avg path length: {e}")
            metrics['average_path_length'] = 0.0
    else:
        # For disconnected graphs, calculate average over largest connected component
        try:
            largest_cc = max(nx.connected_components(G), key=len)
            subgraph = G.subgraph(largest_cc)
            metrics['average_path_length'] = nx.average_shortest_path_length(subgraph)
        except Exception as e:
            logger.warning(f"Failed to calculate avg path length for largest CC: {e}")
            metrics['average_path_length'] = 0.0

    # Average Degree
    if G.number_of_nodes() > 0:
        metrics['average_degree'] = sum(dict(G.degree()).values()) / G.number_of_nodes()
    else:
        metrics['average_degree'] = 0.0

    # Average Betweenness Centrality
    if G.number_of_nodes() > 1:
        try:
            betweenness = nx.betweenness_centrality(G)
            metrics['average_betweenness_centrality'] = sum(betweenness.values()) / len(betweenness)
        except Exception as e:
            logger.warning(f"Failed to calculate betweenness centrality: {e}")
            metrics['average_betweenness_centrality'] = 0.0
    else:
        metrics['average_betweenness_centrality'] = 0.0

    return metrics


def extract_topological_features(graphs: Dict[str, nx.Graph]) -> List[Dict[str, Any]]:
    """Extract topological features for all graphs."""
    features = []
    for doc_id, G in graphs.items():
        metrics = calculate_topological_metrics(G)
        feature_row = {
            'doc_id': doc_id,
            **metrics
        }
        features.append(feature_row)
    return features


def save_features(features: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """Save features to CSV."""
    if output_path is None:
        output_path = PROCESSED_DIR / "features.csv"
    
    logger.info(f"Saving features to {output_path}")
    if not features:
        logger.warning("No features to save")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = None
        for row in features:
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
            writer.writerow(row)


def extract_features_for_retrieved_docs(
    graphs: Dict[str, nx.Graph],
    retrieved_doc_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Extract topological features ONLY for the set of documents 
    returned by the TF-IDF ranking.
    
    Args:
        graphs: Dictionary of doc_id -> nx.Graph
        retrieved_doc_ids: List of doc_ids that were retrieved by the ranking system
    
    Returns:
        List of feature dictionaries for the retrieved documents
    """
    features = []
    missing_ids = []
    
    for doc_id in retrieved_doc_ids:
        if doc_id in graphs:
          G = graphs[doc_id]
          metrics = calculate_topological_metrics(G)
          feature_row = {
              'doc_id': doc_id,
              **metrics
          }
          features.append(feature_row)
        else:
            missing_ids.append(doc_id)
            logger.warning(f"Graph for retrieved doc_id '{doc_id}' not found in graphs dictionary.")
    
    if missing_ids:
        logger.warning(f"Skipped {len(missing_ids)} retrieved documents because their graphs were not found.")
        
    return features


def save_retrieved_features(
    features: List[Dict[str, Any]],
    output_path: Optional[Path] = None
):
    """
    Save retrieved document features to CSV.
    
    Args:
        features: List of feature dictionaries for retrieved documents
        output_path: Path to output CSV file (defaults to data/results/retrieved_features.csv)
    """
    if output_path is None:
        output_path = RESULTS_DIR / "retrieved_features.csv"
    
    logger.info(f"Saving retrieved features to {output_path}")
    if not features:
        logger.warning("No retrieved features to save")
        # Create empty file with headers to satisfy schema if needed, or just return
        # Per requirement: write real output. If empty, write empty file or just return.
        # We'll write an empty file if no data, but with headers if we knew them.
        # Since we don't know headers without data, we'll just return if empty.
        return

    # Determine headers from the first row
    fieldnames = list(features[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)


def run_pipeline_from_retrieval_scores(
    graphs_path: Optional[Path] = None,
    retrieval_scores_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main pipeline function to extract topological signatures from retrieved documents.
    
    This function:
    1. Loads graphs from the graph builder output.
    2. Loads retrieval scores to identify which documents were retrieved.
    3. Extracts topological features ONLY for those retrieved documents.
    4. Saves the results to the specified output path.
    
    Args:
        graphs_path: Path to graphs.json (default: data/processed/graphs.json)
        retrieval_scores_path: Path to retrieval_scores.csv (default: data/results/retrieval_scores.csv)
        output_path: Path to output CSV (default: data/results/retrieved_features.csv)
    
    Returns:
        List of feature dictionaries for the retrieved documents.
    """
    if graphs_path is None:
        graphs_path = PROCESSED_DIR / "graphs.json"
    if retrieval_scores_path is None:
        retrieval_scores_path = RESULTS_DIR / "retrieval_scores.csv"
    if output_path is None:
        output_path = RESULTS_DIR / "retrieved_features.csv"

    logger.info("Starting topological feature extraction for retrieved documents...")

    # 1. Load graphs
    graphs = load_graphs(graphs_path)
    if not graphs:
        logger.error("No graphs found. Cannot proceed.")
        return []

    # 2. Load retrieval scores to get retrieved document IDs
    logger.info(f"Loading retrieval scores from {retrieval_scores_path}")
    retrieved_doc_ids = []
    try:
        with open(retrieval_scores_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assuming 'doc_id' column exists in retrieval_scores.csv
                if 'doc_id' in row:
                    retrieved_doc_ids.append(row['doc_id'])
                elif 'document_id' in row:
                    retrieved_doc_ids.append(row['document_id'])
                else:
                    # Fallback: use first column that looks like an ID
                    for key, val in row.items():
                        if val and not key.startswith('rank'):
                            retrieved_doc_ids.append(val)
                            break
    except FileNotFoundError:
        logger.error(f"Retrieval scores file not found: {retrieval_scores_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading retrieval scores: {e}")
        return []

    logger.info(f"Found {len(retrieved_doc_ids)} retrieved documents.")

    # 3. Extract features for retrieved documents only
    features = extract_features_for_retrieved_docs(graphs, retrieved_doc_ids)

    # 4. Save results
    save_retrieved_features(features, output_path)

    logger.info(f"Successfully extracted features for {len(features)} retrieved documents.")
    logger.info(f"Output saved to {output_path}")

    return features


def run_pipeline(
    graphs_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Run the full topology extraction pipeline for ALL documents.
    (Used for T016 - full corpus features)
    """
    if graphs_path is None:
        graphs_path = PROCESSED_DIR / "graphs.json"
    if output_path is None:
        output_path = PROCESSED_DIR / "features.csv"

    graphs = load_graphs(graphs_path)
    if not graphs:
        logger.error("No graphs found.")
        return []

    features = extract_topological_features(graphs)
    save_features(features, output_path)
    return features


def main():
    """Entry point for direct execution."""
    # Default execution: extract features for retrieved documents (T023)
    run_pipeline_from_retrieval_scores()


if __name__ == "__main__":
    main()
