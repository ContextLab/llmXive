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
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

def build_item_vectors(items: List[Dict]) -> Dict[str, np.ndarray]:
    """Build item feature vectors from raw data."""
    vectors = {}
    for item in items:
        item_id = str(item['id'])
        features = np.array(item.get('features', []), dtype=float)
        vectors[item_id] = features
    return vectors

def find_similar_neighbors(
    item_id: str,
    vectors: Dict[str, np.ndarray],
    top_k: int = 10,
    threshold: float = 0.0
) -> List[Tuple[str, float]]:
    """Find similar neighbors for a given item based on cosine similarity."""
    if item_id not in vectors:
        return []
    
    target_vec = vectors[item_id]
    similarities = []
    
    for other_id, other_vec in vectors.items():
        if other_id == item_id:
            continue
        sim = compute_cosine_similarity(target_vec, other_vec)
        if sim >= threshold:
            similarities.append((other_id, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

def build_graph(
    items: List[Dict],
    top_k: int = 10,
    similarity_threshold: float = 0.0
) -> Dict[str, List[SimilarityEdge]]:
    """Build an item-similarity graph."""
    vectors = build_item_vectors(items)
    graph = defaultdict(list)
    
    for item in items:
        item_id = str(item['id'])
        neighbors = find_similar_neighbors(
            item_id, vectors, top_k=top_k, threshold=similarity_threshold
        )
        for neighbor_id, score in neighbors:
            edge = SimilarityEdge(
                source=item_id,
                target=neighbor_id,
                weight=score
            )
            graph[item_id].append(edge)
    
    return dict(graph)

def get_connected_component(
    graph: Dict[str, List[SimilarityEdge]],
    start_node: str
) -> Set[str]:
    """Get the connected component containing start_node using BFS."""
    if start_node not in graph and not any(start_node in [e.target for edges in graph.values() for e in edges]):
        return set()
    
    visited = set()
    queue = [start_node]
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        # Check outgoing edges
        if current in graph:
            for edge in graph[current]:
                if edge.target not in visited:
                    queue.append(edge.target)
        
        # Check incoming edges (for undirected traversal)
        for source, edges in graph.items():
            for edge in edges:
                if edge.target == current and source not in visited:
                    queue.append(source)
    
    return visited

def is_node_connected(
    graph: Dict[str, List[SimilarityEdge]],
    node_a: str,
    node_b: str
) -> bool:
    """Check if two nodes are in the same connected component."""
    if node_a not in graph and node_b not in graph:
        return False
    
    component = get_connected_component(graph, node_a)
    return node_b in component

def validate_path_connectivity(
    graph: Dict[str, List[SimilarityEdge]],
    path: List[str]
) -> Tuple[bool, int]:
    """
    Validate that a path is connected in the graph.
    Returns (is_valid, break_index) where break_index is the first edge that fails.
    """
    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]
        
        if current not in graph:
            return False, i
        
        neighbors = [e.target for e in graph[current]]
        if next_node not in neighbors:
            return False, i
    
    return True, -1

def truncate_path_at_disconnection(
    graph: Dict[str, List[SimilarityEdge]],
    path: List[str]
) -> Tuple[Optional[List[str]], bool]:
    """
    Handle disconnected components by truncating paths.
    
    Args:
        graph: The similarity graph
        path: A list of item IDs representing a path
        
    Returns:
        Tuple of (truncated_path, was_truncated)
        - If path is fully connected: (path, False)
        - If path has disconnection: (valid_prefix, True)
        - If path is invalid from start (length < 2): (None, True)
    """
    if len(path) < 2:
        return path, False if len(path) <= 1 else (None, True)
    
    is_valid, break_idx = validate_path_connectivity(graph, path)
    
    if is_valid:
        return path, False
    
    # Path is disconnected at break_idx
    # Truncate to include only the valid prefix (up to the break point)
    truncated = path[:break_idx + 1]
    
    logger.warning(
        f"Path truncated at index {break_idx}: "
        f"edge from '{path[break_idx]}' to '{path[break_idx + 1]}' not found. "
        f"Resulting path length: {len(truncated)}"
    )
    
    return truncated, True