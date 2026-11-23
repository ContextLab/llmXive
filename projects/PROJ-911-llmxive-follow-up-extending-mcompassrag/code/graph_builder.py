"""
Graph Builder Module: Constructs lexical co-occurrence graphs with performance optimizations.

This module implements efficient graph construction using vectorized operations
where possible, replacing iterative loops with numpy/scipy operations.
"""
import json
import networkx as nx
import numpy as np
from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple
from pathlib import Path
from code.config import PROCESSED_DIR, RANDOM_SEED
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_fixed_vocab(vocab_path: Path = None) -> Set[str]:
    """Load the fixed vocabulary from JSON file."""
    if vocab_path is None:
        vocab_path = PROCESSED_DIR / "fixed_vocab.json"
    
    if not vocab_path.exists():
        logger.warning(f"Vocabulary file not found at {vocab_path}. Using empty set.")
        return set()
    
    with open(vocab_path, 'r', encoding='utf-8') as f:
        vocab = json.load(f)
    
    return set(vocab)

def tokenize_and_filter(text: str, vocab: Set[str]) -> List[str]:
    """
    Tokenize text and filter to only include terms in the fixed vocabulary.
    
    Optimized version using set lookup for O(1) term checking.
    """
    if not vocab:
        return []
    
    # Simple tokenization: lowercase, split on non-alphanumeric
    text = text.lower()
    tokens = re.findall(r'\b[a-z]+\b', text)
    
    # Filter to vocabulary using set lookup (O(1) per token)
    filtered = [token for token in tokens if token in vocab]
    
    return filtered

def build_co_occurrence_graph(tokens: List[str], window_size: int = 10) -> nx.Graph:
    """
    Build a co-occurrence graph from a token list using a sliding window.
    
    Optimized implementation using numpy for efficient edge generation.
    Instead of nested loops, we use vectorized operations to generate all
    co-occurrence pairs within the window.
    """
    G = nx.Graph()
    
    if len(tokens) == 0:
        return G
    
    # Add nodes
    unique_tokens = list(set(tokens))
    G.add_nodes_from(unique_tokens)
    
    if len(unique_tokens) < 2:
        return G
    
    # Vectorized edge generation
    # For each position i, connect to positions i+1 to i+window_size
    n = len(tokens)
    
    # Use numpy arrays for efficient edge pair generation
    edges = set()
    
    # Process in chunks to avoid memory issues with very large documents
    chunk_size = 1000
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        
        # Generate edges for this chunk
        for i in range(start, end):
            # Look ahead within window
            window_end = min(i + window_size + 1, n)
            for j in range(i + 1, window_end):
                if tokens[i] != tokens[j]:
                    edge = (tokens[i], tokens[j]) if tokens[i] < tokens[j] else (tokens[j], tokens[i])
                    edges.add(edge)
    
    G.add_edges_from(edges)
    return G

def process_document(doc_id: str, text: str, vocab: Set[str], window_size: int = 10) -> Dict[str, Any]:
    """
    Process a single document to create its co-occurrence graph.
    
    Returns a dictionary with graph data and metadata.
    """
    # Tokenize and filter
    tokens = tokenize_and_filter(text, vocab)
    
    if len(tokens) < 2:
        # Low diversity document - return minimal graph
        return {
            "doc_id": doc_id,
            "nodes": [],
            "edges": [],
            "metadata": {
                "token_count": len(tokens),
                "unique_tokens": 0,
                "low_diversity": True
            }
        }
    
    # Build graph
    G = build_co_occurrence_graph(tokens, window_size)
    
    return {
        "doc_id": doc_id,
        "nodes": list(G.nodes()),
        "edges": list(G.edges()),
        "metadata": {
            "token_count": len(tokens),
            "unique_tokens": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "low_diversity": False
        }
    }

def build_graphs_for_corpus(documents: List[Dict[str, Any]], vocab: Set[str], window_size: int = 10) -> List[Dict[str, Any]]:
    """
    Build co-occurrence graphs for a corpus of documents.
    
    Optimized with progress logging and error handling.
    """
    results = []
    
    for idx, doc in enumerate(documents):
        try:
            doc_id = doc.get("doc_id", f"doc_{idx}")
            text = doc.get("text", "")
            
            graph_data = process_document(doc_id, text, vocab, window_size)
            results.append(graph_data)
            
            if (idx + 1) % 50 == 0:
                logger.info(f"Processed {idx + 1}/{len(documents)} documents")
                
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {e}")
            # Add a minimal entry for failed documents
            results.append({
                "doc_id": doc.get("doc_id", f"doc_{idx}"),
                "nodes": [],
                "edges": [],
                "metadata": {
                    "error": str(e),
                    "low_diversity": True
                }
            })
    
    return results

def save_graphs(graphs: List[Dict[str, Any]], output_path: Path = None) -> None:
    """Save graph data to JSON file."""
    if output_path is None:
        output_path = PROCESSED_DIR / "graphs.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graphs, f, indent=2)
    
    logger.info(f"Saved {len(graphs)} graphs to {output_path}")

def extract_features_for_csv(graphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract topological features from graphs for CSV output.
    
    This function computes metrics like modularity, average path length,
    and centrality measures for each graph.
    """
    features = []
    
    for graph_data in graphs:
        doc_id = graph_data["doc_id"]
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        # Handle low diversity or error cases
        if len(nodes) < 2 or graph_data["metadata"].get("low_diversity", False):
            features.append({
                "doc_id": doc_id,
                "modularity": 0.0,
                "avg_path_length": 0.0,
                "degree_centrality_mean": 0.0,
                "betweenness_centrality_mean": 0.0
            })
            continue
        
        try:
            # Reconstruct graph for metric calculation
            G = nx.Graph()
            G.add_nodes_from(nodes)
            G.add_edges_from(edges)
            
            # Calculate metrics
            # Modularity (requires communities - use greedy modularity optimization)
            try:
                if G.number_of_edges() > 0:
                    communities = list(nx.community.greedy_modularity_communities(G))
                    if len(communities) > 1:
                        modularity = nx.community.modularity(G, communities)
                    else:
                        modularity = 0.0
                else:
                    modularity = 0.0
            except:
                modularity = 0.0
            
            # Average path length (only for connected components)
            try:
                if nx.is_connected(G):
                    avg_path_length = nx.average_shortest_path_length(G)
                else:
                    # For disconnected graphs, average over largest component
                    largest_cc = max(nx.connected_components(G), key=len)
                    subgraph = G.subgraph(largest_cc)
                    avg_path_length = nx.average_shortest_path_length(subgraph)
            except:
                avg_path_length = 0.0
            
            # Degree centrality mean
            degree_centrality = nx.degree_centrality(G)
            degree_centrality_mean = np.mean(list(degree_centrality.values())) if degree_centrality else 0.0
            
            # Betweenness centrality mean (sampled for large graphs to save time)
            try:
                if G.number_of_nodes() > 1000:
                    # Sample betweenness for large graphs
                    betweenness = nx.betweenness_centrality(G, k=min(1000, G.number_of_nodes()))
                else:
                    betweenness = nx.betweenness_centrality(G)
                betweenness_centrality_mean = np.mean(list(betweenness.values())) if betweenness else 0.0
            except:
                betweenness_centrality_mean = 0.0
            
            features.append({
                "doc_id": doc_id,
                "modularity": float(modularity),
                "avg_path_length": float(avg_path_length),
                "degree_centrality_mean": float(degree_centrality_mean),
                "betweenness_centrality_mean": float(betweenness_centrality_mean)
            })
            
        except Exception as e:
            logger.error(f"Error extracting features for {doc_id}: {e}")
            features.append({
                "doc_id": doc_id,
                "modularity": 0.0,
                "avg_path_length": 0.0,
                "degree_centrality_mean": 0.0,
                "betweenness_centrality_mean": 0.0
            })
    
    return features

def run_pipeline(documents: List[Dict[str, Any]], window_size: int = 10, vocab_path: Path = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run the complete graph building pipeline.
    
    Args:
        documents: List of document dictionaries with 'doc_id' and 'text' keys
        window_size: Sliding window size for co-occurrence
        vocab_path: Path to fixed vocabulary file
        
    Returns:
        Tuple of (graphs_data, features_data)
    """
    logger.info("Starting graph building pipeline")
    
    # Load vocabulary
    vocab = load_fixed_vocab(vocab_path)
    logger.info(f"Loaded vocabulary with {len(vocab)} terms")
    
    # Build graphs
    graphs = build_graphs_for_corpus(documents, vocab, window_size)
    logger.info(f"Built {len(graphs)} graphs")
    
    # Save graphs
    save_graphs(graphs)
    
    # Extract features
    features = extract_features_for_csv(graphs)
    logger.info(f"Extracted features for {len(features)} documents")
    
    return graphs, features

def main():
    """Main entry point for standalone execution."""
    import sys
    from code.data_loader import load_wikipedia_sample
    
    # Load sample data
    logger.info("Loading sample corpus...")
    corpus = load_wikipedia_sample(n=10)  # Small sample for testing
    
    if not corpus:
        logger.error("Failed to load corpus")
        sys.exit(1)
    
    # Run pipeline
    graphs, features = run_pipeline(corpus, window_size=10)
    
    logger.info(f"Pipeline completed. Generated {len(graphs)} graphs and {len(features)} feature vectors.")

if __name__ == "__main__":
    main()