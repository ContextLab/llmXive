"""
Path generation module for ProRL pipeline.

Implements greedy and beam search path generation, plus ProRL rectification
formulas (Stepwise Reward Centering and Position-Specific Advantage).
"""
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict
import numpy as np

from src.entities import ItemNode, SimilarityEdge, RecommendationPath
from src.config import get_config

logger = logging.getLogger(__name__)


def generate_greedy_paths(
    seed_item: ItemNode,
    graph: Dict[str, List[SimilarityEdge]],
    path_length: int = 5
) -> List[RecommendationPath]:
    """
    Generate paths using the standard greedy heuristic.
    
    Starting from the seed item, repeatedly select the neighbor with the 
    highest similarity score until the path reaches the target length.
    
    Args:
        seed_item: The starting item node.
        graph: Adjacency list of item similarities.
        path_length: Maximum length of the path (L).
        
    Returns:
        A list containing the single greedy path (or multiple if ties exist).
    """
    config = get_config()
    L = config.get('path_length', path_length)
    
    if seed_item.id not in graph:
        logger.warning(f"Seed item {seed_item.id} not found in graph.")
        return []
    
    paths = []
    current_node = seed_item
    current_path = [current_node]
    visited = {current_node.id}
    
    while len(current_path) < L:
        neighbors = graph.get(current_node.id, [])
        # Filter out visited nodes and zero-similarity edges
        valid_neighbors = [
            edge for edge in neighbors 
            if edge.target_id not in visited and edge.score > 0.0
        ]
        
        if not valid_neighbors:
            logger.info(f"Path terminated early at node {current_node.id} (no valid neighbors).")
            break
        
        # Sort by score descending
        valid_neighbors.sort(key=lambda x: x.score, reverse=True)
        
        # Take the best neighbor (greedy)
        best_edge = valid_neighbors[0]
        next_node = ItemNode(
            id=best_edge.target_id,
            features=best_edge.target_features or {},
            score=best_edge.score
        )
        
        current_path.append(next_node)
        visited.add(next_node.id)
        current_node = next_node
    
    if len(current_path) > 0:
        # Calculate raw path score as sum of edge scores
        raw_score = sum(edge.score for edge in current_path[:-1]) # Exclude seed's own score if any
        # Actually, path score usually sums edge weights. Let's reconstruct edges for the path
        path_edges = []
        for i in range(len(current_path) - 1):
            # Find the edge used
            neighbors = graph.get(current_path[i].id, [])
            for n in neighbors:
                if n.target_id == current_path[i+1].id:
                    path_edges.append(n)
                    break
        
        total_score = sum(e.score for e in path_edges)
        
        path_obj = RecommendationPath(
            items=current_path,
            edges=path_edges,
            score=total_score,
            method="greedy"
        )
        paths.append(path_obj)
        
    return paths


def generate_beam_paths(
    seed_item: ItemNode,
    graph: Dict[str, List[SimilarityEdge]],
    beam_width: int = 50,
    path_length: int = 5
) -> List[RecommendationPath]:
    """
    Generate diverse candidate paths using Beam Search.
    
    Maintains a beam of the top-K partial paths at each step, expanding
    all neighbors and keeping the best candidates based on cumulative score.
    
    Args:
        seed_item: The starting item node.
        graph: Adjacency list of item similarities.
        beam_width: Number of paths to keep at each step (B).
        path_length: Target length of paths (L).
        
    Returns:
        A list of top candidate paths sorted by score.
    """
    config = get_config()
    L = config.get('path_length', path_length)
    B = config.get('beam_width', beam_width)
    
    if seed_item.id not in graph:
        logger.warning(f"Seed item {seed_item.id} not found in graph.")
        return []
    
    # Beam state: list of (current_node, path_items, path_edges, cumulative_score)
    # Initial state: just the seed
    beam = [(seed_item, [seed_item], [], 0.0)]
    
    for step in range(L - 1):
        next_beam = []
        for current_node, path_items, path_edges, cum_score in beam:
            neighbors = graph.get(current_node.id, [])
            valid_neighbors = [
                edge for edge in neighbors 
                if edge.target_id not in {n.id for n in path_items} and edge.score > 0.0
            ]
            
            if not valid_neighbors:
                # Path ends here, keep it as a candidate if length > 1
                if len(path_items) > 1:
                    next_beam.append((current_node, path_items, path_edges, cum_score))
                continue
            
            for edge in valid_neighbors:
                next_node = ItemNode(
                    id=edge.target_id,
                    features=edge.target_features or {},
                    score=edge.score
                )
                new_items = path_items + [next_node]
                new_edges = path_edges + [edge]
                new_score = cum_score + edge.score
                next_beam.append((next_node, new_items, new_edges, new_score))
        
        # Sort by cumulative score descending and keep top B
        next_beam.sort(key=lambda x: x[3], reverse=True)
        beam = next_beam[:B]
    
    # Convert beam states to RecommendationPath objects
    results = []
    for current_node, path_items, path_edges, score in beam:
        if len(path_items) >= 2: # Valid path
            path_obj = RecommendationPath(
                items=path_items,
                edges=path_edges,
                score=score,
                method="beam"
            )
            results.append(path_obj)
    
    return results


def apply_prorl_rectification(
    paths: List[RecommendationPath],
    alpha: Optional[float] = None
) -> List[RecommendationPath]:
    """
    Apply ProRL rectification formulas to a list of paths.
    
    Calculates:
    1. Stepwise Reward Centering (SRC): S_rect = S_raw - mu_batch
    2. Position-Specific Advantage (PSA): S_final = S_rect * (1 + alpha * pos)
    
    Where:
    - S_raw is the original cumulative path score.
    - mu_batch is the mean score of the input batch of paths.
    - pos is the 0-indexed position in the path (or 1-indexed? Spec says pos, usually 1-based in such formulas, 
      but let's assume 0-based index of the step or 1-based position count. 
      Standard ProRL often uses 1-based position for the multiplier. Let's use 1-based index for the step number 1..L).
    
    Args:
        paths: List of paths to rectify (from Greedy or Beam generation).
        alpha: The alpha parameter for PSA. Defaults to config value.
        
    Returns:
        The same path objects with updated 'score' attribute reflecting the rectified score.
    """
    if not paths:
        return []
    
    config = get_config()
    if alpha is None:
        alpha = config.get('alpha', 0.1)
    
    # 1. Calculate mu_batch (mean of raw scores)
    raw_scores = [p.score for p in paths]
    mu_batch = np.mean(raw_scores)
    
    logger.debug(f"Batch size: {len(paths)}, Raw Mean Score (mu_batch): {mu_batch:.6f}")
    
    rectified_paths = []
    
    for path in paths:
        S_raw = path.score
        
        # Step 1: Stepwise Reward Centering
        S_rect = S_raw - mu_batch
        
        # Step 2: Position-Specific Advantage
        # The formula S_final = S_rect * (1 + alpha * pos)
        # We need to determine 'pos'. Usually, this applies a bonus based on path length or position.
        # Given the context of "Position-Specific", it likely scales the reward based on the position index.
        # However, the path has a single score. The formula might imply scaling the *total* score based on the 
        # average position or the final position (length).
        # Let's interpret 'pos' as the path length (number of edges) or the index of the last item.
        # If the path has L items, there are L-1 edges. Let's use the number of steps (edges) as 'pos'.
        # Or, if the formula is applied per-step and summed, it would be different.
        # But the input is a path with a single score.
        # Interpretation: The rectification is applied to the aggregate score.
        # "Position-Specific Advantage" often means later steps are weighted more.
        # If we treat the path score as a sum of rewards, and we want to apply (1 + alpha * pos) to each step?
        # That would require re-calculating the sum.
        # Alternative interpretation: The formula is a post-hoc adjustment to the total score based on the path's 
        # "position" in the sequence of recommendations (e.g. if this path is the k-th best).
        # But the task says "Position-Specific Advantage (S_final = S_rect * (1 + alpha * pos))".
        # Let's assume 'pos' refers to the path length (number of items or steps) to encourage longer paths?
        # Or perhaps 'pos' is the 1-based index of the path in the sorted list? No, that's ranking.
        # Let's look at the standard ProRL literature context (simulated): 
        # Often, it's about the position in the recommendation list. But here we are scoring paths.
        # Let's assume 'pos' is the number of steps (edges) in the path, i.e., len(path.items) - 1.
        # This encourages longer paths if alpha > 0.
        
        num_steps = len(path.items) - 1
        if num_steps <= 0:
            num_steps = 1 # Avoid zero or negative multiplier if path is just seed
        
        # Using 1-based index for position if it refers to step number, or just the count.
        # Let's use the count of steps as 'pos'.
        pos = float(num_steps)
        
        S_final = S_rect * (1.0 + alpha * pos)
        
        # Create a new path object or modify in place? 
        # To be safe and functional, let's create a new one with the updated score.
        # We need to copy the path but update the score.
        # RecommendationPath is a dataclass, so we can use replace or create new.
        # Since we don't have dataclasses.replace imported explicitly and it's standard, we can use it.
        # But to avoid import issues, let's just modify the score if mutable, or create new.
        # Assuming RecommendationPath is mutable or we can reconstruct.
        # Let's reconstruct to be safe.
        
        rectified_path = RecommendationPath(
            items=path.items,
            edges=path.edges,
            score=S_final,
            method=path.method
        )
        rectified_paths.append(rectified_path)
        
        logger.debug(f"Path {path.method}: Raw={S_raw:.4f}, Rectified={S_rect:.4f}, Final={S_final:.4f} (pos={pos})")
    
    return rectified_paths