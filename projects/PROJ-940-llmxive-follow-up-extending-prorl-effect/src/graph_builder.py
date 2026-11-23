"""
Graph builder module for constructing item-similarity graphs.
Handles disconnected components by truncating paths or returning null results.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import logging

from src.entities import ItemNode, SimilarityEdge, RecommendationPath
from src.exceptions import GraphDisconnectionError, DataFetchError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def build_item_vectors(items: List[Dict]) -> Dict[str, np.ndarray]:
    """Build item vectors from item data (e.g., genre, features)."""
    vectors = {}
    for item in items:
        # Extract features (assuming 'features' or 'genres' key exists)
        features = item.get('features') or item.get('genres') or []
        # Convert to one-hot or bag-of-words representation
        if isinstance(features, list):
            # Simple one-hot encoding for demonstration
            # In real implementation, use proper feature extraction
            vec = np.zeros(len(features) + 1)
            for i, f in enumerate(features):
                vec[i] = 1.0
            vec[-1] = 1.0  # Bias term
            vectors[item['id']] = vec
        else:
            # Assume features is already a numeric array
            vectors[item['id']] = np.array(features)
    return vectors

def find_similar_neighbors(
    item_id: str,
    item_vectors: Dict[str, np.ndarray],
    graph: Dict[str, List[Tuple[str, float]]],
    threshold: float = 0.01
) -> List[Tuple[str, float]]:
    """Find similar neighbors for an item based on cosine similarity."""
    if item_id not in item_vectors:
        return []
    
    target_vec = item_vectors[item_id]
    neighbors = []
    
    for other_id, other_vec in item_vectors.items():
        if other_id == item_id:
            continue
        
        sim = compute_cosine_similarity(target_vec, other_vec)
        if sim >= threshold:
            neighbors.append((other_id, sim))
    
    return sorted(neighbors, key=lambda x: x[1], reverse=True)

def build_graph(
    items: List[Dict],
    threshold: float = 0.01
) -> Tuple[Dict[str, ItemNode], Dict[str, List[Tuple[str, float]]]]:
    """
    Build a static item-similarity graph using cosine similarity.
    Returns nodes and adjacency list.
    """
    item_vectors = build_item_vectors(items)
    nodes = {}
    adjacency = defaultdict(list)
    
    for item in items:
        item_id = item['id']
        nodes[item_id] = ItemNode(
            id=item_id,
            metadata=item.get('metadata', {}),
            vector=item_vectors.get(item_id)
        )
    
    # Build adjacency list
    for item_id in nodes:
        neighbors = find_similar_neighbors(item_id, item_vectors, adjacency, threshold)
        # Handle zero-overlap neighbors by assigning score 0.0 and skipping them
        # (Already handled by threshold check above)
        adjacency[item_id] = [(n_id, sim) for n_id, sim in neighbors if sim > 0.0]
    
    return nodes, dict(adjacency)

def get_connected_component(
    start_node: str,
    adjacency: Dict[str, List[Tuple[str, float]]]
) -> Set[str]:
    """Get all nodes in the connected component containing start_node."""
    visited = set()
    stack = [start_node]
    
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        
        for neighbor, _ in adjacency.get(node, []):
            if neighbor not in visited:
                stack.append(neighbor)
    
    return visited

def is_node_connected(
    node_id: str,
    adjacency: Dict[str, List[Tuple[str, float]]]
) -> bool:
    """Check if a node has any connections in the graph."""
    return len(adjacency.get(node_id, [])) > 0

def validate_path_connectivity(
    path: List[str],
    adjacency: Dict[str, List[Tuple[str, float]]]
) -> bool:
    """Validate that all consecutive nodes in a path are connected."""
    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]
        
        # Check if next_node is a neighbor of current
        neighbors = [n for n, _ in adjacency.get(current, [])]
        if next_node not in neighbors:
            return False
    
    return True

def truncate_path_at_disconnection(
    path: List[str],
    adjacency: Dict[str, List[Tuple[str, float]]]
) -> List[str]:
    """
    Truncate a path at the first point of disconnection.
    Returns the valid prefix of the path.
    If the path is empty or has only one node, returns the path as-is.
    """
    if len(path) <= 1:
        return path
    
    valid_prefix = [path[0]]
    
    for i in range(1, len(path)):
        current = path[i - 1]
        next_node = path[i]
        
        # Check if next_node is connected to current
        neighbors = [n for n, _ in adjacency.get(current, [])]
        if next_node not in neighbors:
            # Disconnection detected, truncate here
            logger.warning(
                f"Path disconnection detected between {current} and {next_node}. "
                f"Truncating path to length {len(valid_prefix)}."
            )
            break
        
        valid_prefix.append(next_node)
    
    return valid_prefix