import json
import logging
import networkx as nx
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict

from code.config import PROCESSED_DIR, RESULTS_DIR, RANDOM_SEED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_graphs(graphs_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load pre-computed graphs from JSON."""
    if graphs_path is None:
        graphs_path = PROCESSED_DIR / "graphs.json"
    
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found: {graphs_path}")
    
    with open(graphs_path, 'r') as f:
        return json.load(f)

def calculate_topological_metrics(graph: nx.Graph) -> Dict[str, float]:
    """Calculate topological metrics for a single graph."""
    metrics = {}
    
    if len(graph.nodes()) == 0:
        # Default values for empty graphs
        return {
            'modularity': 0.0,
            'avg_path_length': 0.0,
            'avg_degree': 0.0,
            'avg_betweenness': 0.0,
            'avg_closeness': 0.0,
            'avg_eigenvector': 0.0,
            'num_nodes': 0,
            'num_edges': 0
        }
    
    metrics['num_nodes'] = graph.number_of_nodes()
    metrics['num_edges'] = graph.number_of_edges()
    
    if metrics['num_nodes'] > 0:
        metrics['avg_degree'] = sum(dict(graph.degree()).values()) / metrics['num_nodes']
    else:
        metrics['avg_degree'] = 0.0
    
    # Modularity (requires communities)
    try:
        # Use Louvain algorithm for community detection
        communities = list(nx.community.louvain_communities(graph, seed=RANDOM_SEED))
        if len(communities) > 1:
            metrics['modularity'] = nx.community.modularity(graph, communities)
        else:
            metrics['modularity'] = 0.0
    except Exception as e:
        logger.warning(f"Could not compute modularity: {e}")
        metrics['modularity'] = 0.0
    
    # Average path length (only for connected graphs or largest component)
    try:
        if nx.is_connected(graph):
            metrics['avg_path_length'] = nx.average_shortest_path_length(graph)
        else:
            # Use largest connected component
            largest_cc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(largest_cc)
            if len(largest_cc) > 1:
                metrics['avg_path_length'] = nx.average_shortest_path_length(subgraph)
            else:
                metrics['avg_path_length'] = 0.0
    except Exception as e:
        logger.warning(f"Could not compute average path length: {e}")
        metrics['avg_path_length'] = 0.0
    
    # Centrality measures
    try:
        betweenness = nx.betweenness_centrality(graph)
        metrics['avg_betweenness'] = sum(betweenness.values()) / len(betweenness) if betweenness else 0.0
    except Exception as e:
        logger.warning(f"Could not compute betweenness centrality: {e}")
        metrics['avg_betweenness'] = 0.0
    
    try:
        closeness = nx.closeness_centrality(graph)
        metrics['avg_closeness'] = sum(closeness.values()) / len(closeness) if closeness else 0.0
    except Exception as e:
        logger.warning(f"Could not compute closeness centrality: {e}")
        metrics['avg_closeness'] = 0.0
    
    try:
        eigenvector = nx.eigenvector_centrality(graph, max_iter=1000)
        metrics['avg_eigenvector'] = sum(eigenvector.values()) / len(eigenvector) if eigenvector else 0.0
    except Exception as e:
        logger.warning(f"Could not compute eigenvector centrality: {e}")
        metrics['avg_eigenvector'] = 0.0
    
    return metrics

def extract_topological_features(graphs_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract topological features for all documents."""
    features = []
    
    for doc_id, graph_data in graphs_data.items():
        # Reconstruct graph from edge list
        G = nx.Graph()
        edges = graph_data.get('edges', [])
        G.add_edges_from(edges)
        
        metrics = calculate_topological_metrics(G)
        metrics['doc_id'] = doc_id
        features.append(metrics)
    
    return features

def save_features(features: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save features to CSV."""
    if output_path is None:
        output_path = PROCESSED_DIR / "features.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not features:
        logger.warning("No features to save")
        return
    
    fieldnames = list(features[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)
    
    logger.info(f"Saved {len(features)} feature vectors to {output_path}")

def extract_features_for_retrieved_docs(
    graphs_data: Dict[str, Any], 
    retrieved_doc_ids: List[str]
) -> List[Dict[str, Any]]:
    """Extract topological features ONLY for retrieved documents."""
    features = []
    missing_docs = []
    
    for doc_id in retrieved_doc_ids:
        if doc_id in graphs_data:
            graph_data = graphs_data[doc_id]
            G = nx.Graph()
            edges = graph_data.get('edges', [])
            G.add_edges_from(edges)
            
            metrics = calculate_topological_metrics(G)
            metrics['doc_id'] = doc_id
            metrics['is_retrieved'] = True
            features.append(metrics)
        else:
            missing_docs.append(doc_id)
    
    if missing_docs:
        logger.warning(f"Missing graph data for {len(missing_docs)} retrieved documents: {missing_docs[:5]}...")
    
    return features

def save_retrieved_features(
    features: List[Dict[str, Any]], 
    output_path: Optional[Path] = None
) -> None:
    """Save retrieved document features to CSV."""
    if output_path is None:
        output_path = RESULTS_DIR / "retrieved_features.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not features:
        logger.warning("No retrieved features to save")
        # Create empty file with headers
        with open(output_path, 'w', newline='') as f:
            f.write("doc_id,modularity,avg_path_length,avg_degree,avg_betweenness,avg_closeness,avg_eigenvector,num_nodes,num_edges,is_retrieved\n")
        return
    
    fieldnames = list(features[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)
    
    logger.info(f"Saved {len(features)} retrieved feature vectors to {output_path}")

def load_retrieval_scores(retrieval_scores_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load retrieval scores from CSV."""
    if retrieval_scores_path is None:
        retrieval_scores_path = RESULTS_DIR / "retrieval_scores.csv"
    
    if not retrieval_scores_path.exists():
        raise FileNotFoundError(f"Retrieval scores file not found: {retrieval_scores_path}")
    
    with open(retrieval_scores_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def run_pipeline_from_retrieval_scores(
    graphs_path: Optional[Path] = None,
    retrieval_scores_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Main pipeline: Extract topological features ONLY from retrieved documents.
    
    This ensures no topology data is used to generate ranking scores - 
    topology is extracted AFTER TF-IDF ranking.
    """
    logger.info("Starting topological feature extraction for retrieved documents")
    
    # Load graphs
    graphs_data = load_graphs(graphs_path)
    logger.info(f"Loaded {len(graphs_data)} graphs")
    
    # Load retrieval scores to get retrieved document IDs
    retrieval_scores = load_retrieval_scores(retrieval_scores_path)
    logger.info(f"Loaded {len(retrieval_scores)} retrieval score entries")
    
    # Extract unique retrieved document IDs
    retrieved_doc_ids = list(set(row['doc_id'] for row in retrieval_scores))
    logger.info(f"Found {len(retrieved_doc_ids)} unique retrieved documents")
    
    # Extract features for retrieved documents only
    features = extract_features_for_retrieved_docs(graphs_data, retrieved_doc_ids)
    logger.info(f"Extracted features for {len(features)} retrieved documents")
    
    # Save results
    save_retrieved_features(features, output_path)
    
    return features

def run_pipeline(
    graphs_path: Optional[Path] = None,
    retrieval_scores_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Run the full topological feature extraction pipeline."""
    return run_pipeline_from_retrieval_scores(graphs_path, retrieval_scores_path, output_path)

def main():
    """Entry point for command-line execution."""
    logger.info("Running topological feature extraction for retrieved documents")
    
    try:
        features = run_pipeline_from_retrieval_scores()
        logger.info(f"Successfully extracted {len(features)} feature vectors")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
