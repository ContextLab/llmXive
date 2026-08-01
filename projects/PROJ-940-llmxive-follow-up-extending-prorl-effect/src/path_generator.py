import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict
import numpy as np
from src.entities import ItemNode, SimilarityEdge, RecommendationPath
from src.config import get_config
from src.graph_builder import build_graph, find_similar_neighbors, get_connected_component
from src.exceptions import GraphDisconnectionError

logger = logging.getLogger(__name__)

def generate_greedy_paths(
    seed_item_id: str,
    graph_nodes: Dict[str, ItemNode],
    graph_edges: Dict[str, List[SimilarityEdge]],
    path_length: int = 5
) -> List[RecommendationPath]:
    """
    Generate standard greedy heuristic baseline paths of length L.
    
    Starts from the seed item and greedily selects the neighbor with the 
    highest similarity score at each step until the path reaches the 
    specified length or a dead end is encountered.
    
    Args:
        seed_item_id: The ID of the starting item.
        graph_nodes: Dictionary mapping item IDs to ItemNode objects.
        graph_edges: Dictionary mapping item IDs to lists of SimilarityEdge objects.
        path_length: Target length of the path (L).
        
    Returns:
        A list containing a single RecommendationPath object representing 
        the greedy path, or an empty list if the seed is invalid or 
        disconnected.
        
    Raises:
        GraphDisconnectionError: If the seed item is not in the graph.
    """
    config = get_config()
    L = config.get('path_length', path_length)
    
    if seed_item_id not in graph_nodes:
        logger.error(f"Seed item '{seed_item_id}' not found in graph nodes.")
        raise GraphDisconnectionError(f"Seed item '{seed_item_id}' not in graph.")
    
    current_id = seed_item_id
    path_items = [graph_nodes[current_id]]
    path_edges = []
    
    # Check if the seed node has any neighbors
    if current_id not in graph_edges or not graph_edges[current_id]:
        logger.warning(f"Seed item '{seed_item_id}' has no neighbors. Path truncated at length 1.")
        return [RecommendationPath(
            items=path_items,
            edges=path_edges,
            raw_score=0.0,
            rectified_score=0.0,
            method="greedy"
        )]
    
    for step in range(L - 1):
        neighbors = graph_edges.get(current_id, [])
        
        if not neighbors:
            logger.warning(f"Dead end reached at step {step+1} (item: {current_id}). Path truncated.")
            break
        
        # Greedy selection: pick neighbor with highest similarity
        # Filter out edges with score 0.0 (zero-overlap neighbors as per FR-009)
        valid_neighbors = [edge for edge in neighbors if edge.similarity_score > 0.0]
        
        if not valid_neighbors:
            logger.warning(f"No valid neighbors (score > 0) at step {step+1}. Path truncated.")
            break
        
        best_edge = max(valid_neighbors, key=lambda e: e.similarity_score)
        next_item_id = best_edge.target_id
        
        if next_item_id not in graph_nodes:
            logger.error(f"Neighbor '{next_item_id}' not found in nodes. Skipping.")
            continue
        
        next_node = graph_nodes[next_item_id]
        
        # Avoid cycles: check if item already in path
        if next_node in path_items:
            # If cycle detected, try the next best neighbor
            sorted_neighbors = sorted(valid_neighbors, key=lambda e: e.similarity_score, reverse=True)
            found = False
            for edge in sorted_neighbors[1:]:
                candidate_id = edge.target_id
                if candidate_id in graph_nodes:
                    candidate_node = graph_nodes[candidate_id]
                    if candidate_node not in path_items:
                        best_edge = edge
                        next_node = candidate_node
                        found = True
                        break
            if not found:
                logger.warning(f"Only neighbors lead to cycles. Path truncated at step {step+1}.")
                break
        
        path_items.append(next_node)
        path_edges.append(best_edge)
        current_id = next_item_id
    
    # Calculate raw score as the sum of edge similarities
    raw_score = sum(edge.similarity_score for edge in path_edges)
    
    return [RecommendationPath(
        items=path_items,
        edges=path_edges,
        raw_score=raw_score,
        rectified_score=raw_score, # Rectification applied in a separate step
        method="greedy"
    )]