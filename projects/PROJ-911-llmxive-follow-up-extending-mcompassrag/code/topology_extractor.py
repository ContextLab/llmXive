import json
import logging
import networkx as nx
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict
from code.config import PROCESSED_DIR, RESULTS_DIR, RANDOM_SEED
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_graphs(graphs_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load pre-computed graphs from JSON file."""
    if graphs_path is None:
        graphs_path = PROCESSED_DIR / "graphs.json"
    
    if not graphs_path.exists():
        raise FileNotFoundError(f"Graphs file not found at {graphs_path}")
    
    with open(graphs_path, 'r') as f:
        return json.load(f)

def calculate_topological_metrics(graph_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate topological metrics for a single graph."""
    try:
        G = nx.Graph()
        edges = graph_data.get("edges", [])
        G.add_edges_from(edges)
        
        metrics = {}
        
        # Degree centrality (average)
        if len(G.nodes()) > 0:
            metrics["avg_degree"] = sum(dict(G.degree()).values()) / len(G.nodes())
        else:
            metrics["avg_degree"] = 0.0
        
        # Betweenness centrality (average)
        if len(G.nodes()) > 2:
            betweenness = nx.betweenness_centrality(G)
            metrics["avg_betweenness"] = sum(betweenness.values()) / len(betweenness)
        else:
            metrics["avg_betweenness"] = 0.0
        
        # Modularity (requires communities, using default for isolated nodes)
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            if len(G.nodes()) > 0:
                communities = greedy_modularity_communities(G)
                metrics["modularity"] = nx.community.modularity(G, communities)
            else:
                metrics["modularity"] = 0.0
        except Exception:
            metrics["modularity"] = 0.0
        
        # Clustering coefficient
        if len(G.nodes()) > 0:
            metrics["avg_clustering"] = nx.average_clustering(G)
        else:
            metrics["avg_clustering"] = 0.0
        
        # Number of nodes and edges
        metrics["num_nodes"] = len(G.nodes())
        metrics["num_edges"] = len(G.edges())
        
        return metrics
    except Exception as e:
        logger.warning(f"Error calculating metrics for graph: {e}")
        return {
            "avg_degree": 0.0,
            "avg_betweenness": 0.0,
            "modularity": 0.0,
            "avg_clustering": 0.0,
            "num_nodes": 0,
            "num_edges": 0
        }

def extract_topological_features(graphs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract topological features for all graphs."""
    features = []
    for doc_id, graph_data in graphs.items():
        metrics = calculate_topological_metrics(graph_data)
        metrics["doc_id"] = doc_id
        features.append(metrics)
    return features

def save_features(features: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save features to CSV file."""
    if output_path is None:
        output_path = PROCESSED_DIR / "features.csv"
    
    if not features:
        logger.warning("No features to save.")
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=features[0].keys())
        writer.writeheader()
        writer.writerows(features)
    
    logger.info(f"Saved {len(features)} feature rows to {output_path}")

def extract_features_for_retrieved_docs(retrieved_doc_ids: List[str], graphs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract topological features ONLY for the set of documents returned by TF-IDF ranking."""
    features = []
    for doc_id in retrieved_doc_ids:
        if doc_id in graphs:
            metrics = calculate_topological_metrics(graphs[doc_id])
            metrics["doc_id"] = doc_id
            features.append(metrics)
        else:
            logger.warning(f"Document {doc_id} not found in graphs, skipping.")
    return features

def save_retrieved_features(features: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save retrieved document features to CSV file."""
    if output_path is None:
        output_path = RESULTS_DIR / "retrieved_features.csv"
    
    if not features:
        logger.warning("No retrieved features to save.")
        # Create empty file with headers if no data
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["doc_id", "avg_degree", "avg_betweenness", "modularity", "avg_clustering", "num_nodes", "num_edges"])
            writer.writeheader()
        logger.info(f"Created empty retrieved features file at {output_path}")
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=features[0].keys())
        writer.writeheader()
        writer.writerows(features)
    
    logger.info(f"Saved {len(features)} retrieved feature rows to {output_path}")

def run_pipeline(retrieved_doc_ids: List[str], graphs_path: Optional[Path] = None, output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Main pipeline: load graphs, extract features for retrieved docs, and save."""
    logger.info(f"Starting topology extraction pipeline for {len(retrieved_doc_ids)} retrieved documents.")
    
    graphs = load_graphs(graphs_path)
    features = extract_features_for_retrieved_docs(retrieved_doc_ids, graphs)
    save_retrieved_features(features, output_path)
    
    return features

def run_pipeline_from_retrieval_scores(retrieval_scores_path: Optional[Path] = None, graphs_path: Optional[Path] = None, output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Extract topological signatures from documents returned by TF-IDF ranking.
    
    This function:
    1. Loads retrieval scores from data/results/retrieval_scores.csv
    2. Extracts the list of document IDs that were retrieved (ranked)
    3. Loads pre-computed graphs from data/processed/graphs.json
    4. Calculates topological metrics ONLY for those retrieved documents
    5. Saves results to data/results/retrieved_features.csv
    
    CRITICAL: No topology data is used to generate the ranking scores.
    """
    if retrieval_scores_path is None:
        retrieval_scores_path = RESULTS_DIR / "retrieval_scores.csv"
    
    if not retrieval_scores_path.exists():
        raise FileNotFoundError(f"Retrieval scores file not found at {retrieval_scores_path}")
    
    # Load retrieval scores and extract unique document IDs
    retrieved_doc_ids = []
    with open(retrieval_scores_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming the CSV has a 'doc_id' column from the ranking
            if 'doc_id' in row:
                retrieved_doc_ids.append(row['doc_id'])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_doc_ids = []
    for doc_id in retrieved_doc_ids:
        if doc_id not in seen:
            seen.add(doc_id)
            unique_doc_ids.append(doc_id)
    
    logger.info(f"Found {len(unique_doc_ids)} unique retrieved documents from retrieval scores.")
    
    # Extract features for these documents
    return run_pipeline(unique_doc_ids, graphs_path, output_path)

if __name__ == "__main__":
    # Example usage: run pipeline from retrieval scores
    run_pipeline_from_retrieval_scores()
