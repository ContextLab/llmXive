import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict
import numpy as np
from src.entities import ItemNode, SimilarityEdge, RecommendationPath
from src.config import get_config

logger = logging.getLogger(__name__)

def generate_greedy_paths(
    seed_id: str,
    graph: Dict[str, Dict[str, float]],
    length: int = 5
) -> List[RecommendationPath]:
    """
    Generate standard greedy heuristic baseline paths of length L=5.
    
    Args:
        seed_id: The starting item ID.
        graph: The item similarity graph (adjacency dict).
        length: Path length L (default 5).
        
    Returns:
        List containing a single RecommendationPath.
    """
    config = get_config()
    L = length
    
    if seed_id not in graph:
        logger.warning(f"Seed node {seed_id} not found in graph.")
        return []
    
    current = seed_id
    path_items = [current]
    path_scores = [0.0]  # Seed has no incoming score
    
    for step in range(L - 1):
        neighbors = graph.get(current, {})
        if not neighbors:
            logger.debug(f"Path terminated at step {step}: no neighbors for {current}")
            break
        
        # Greedy selection: max similarity
        next_item = max(neighbors, key=neighbors.get)
        score = neighbors[next_item]
        
        if score == 0.0:
            logger.debug(f"Path terminated at step {step}: zero similarity edge to {next_item}")
            break
            
        path_items.append(next_item)
        path_scores.append(score)
        current = next_item
        
    # Calculate raw path score (sum of edge scores)
    raw_score = sum(path_scores[1:]) if len(path_scores) > 1 else 0.0
    
    return [
        RecommendationPath(
            items=path_items,
            raw_score=raw_score,
            scores=path_scores,
            generation_method="greedy"
        )
    ]

def generate_beam_paths(
    seed_id: str,
    graph: Dict[str, Dict[str, float]],
    beam_width: int = 50,
    length: int = 5
) -> List[RecommendationPath]:
    """
    Generate a diverse candidate pool of paths using Beam Search.
    
    Args:
        seed_id: The starting item ID.
        graph: The item similarity graph.
        beam_width: Number of beams B (default 50).
        length: Path length L (default 5).
        
    Returns:
        List of RecommendationPath objects.
    """
    config = get_config()
    B = beam_width
    L = length
    
    if seed_id not in graph:
        logger.warning(f"Seed node {seed_id} not found in graph.")
        return []
    
    # Beam state: list of (current_item, path_items, path_scores, current_cumulative_score)
    beams = [(seed_id, [seed_id], [0.0], 0.0)]
    
    for step in range(L - 1):
        next_beams = []
        for current_item, path_items, path_scores, cum_score in beams:
            neighbors = graph.get(current_item, {})
            # Sort neighbors by score descending
            sorted_neighbors = sorted(neighbors.items(), key=lambda x: x[1], reverse=True)
            
            # Take top B neighbors to expand
            for next_item, score in sorted_neighbors[:B]:
                if score == 0.0:
                    continue
                
                new_path_items = path_items + [next_item]
                new_path_scores = path_scores + [score]
                new_cum_score = cum_score + score
                next_beams.append((next_item, new_path_items, new_path_scores, new_cum_score))
        
        if not next_beams:
            break
            
        # Sort by cumulative score descending and keep top B
        next_beams.sort(key=lambda x: x[3], reverse=True)
        beams = next_beams[:B]
        
    paths = []
    for current_item, path_items, path_scores, cum_score in beams:
        paths.append(
            RecommendationPath(
                items=path_items,
                raw_score=cum_score,
                scores=path_scores,
                generation_method="beam"
            )
        )
        
    return paths

def apply_src(paths: List[RecommendationPath]) -> List[RecommendationPath]:
    """
    Apply Stepwise Reward Centering (SRC).
    S_rect = S_raw - mu_batch
    
    Args:
        paths: List of paths to rectify.
        
    Returns:
        New list of paths with rectified scores.
    """
    if not paths:
        return []
        
    raw_scores = [p.raw_score for p in paths]
    mu_batch = np.mean(raw_scores)
    
    logger.debug(f"Applying SRC: mu_batch = {mu_batch:.4f}")
    
    rectified_paths = []
    for p in paths:
        rect_score = p.raw_score - mu_batch
        # Update the path's raw_score to the rectified score
        # Note: We keep original scores list as-is, but update the aggregate raw_score
        rectified_paths.append(
            RecommendationPath(
                items=p.items,
                raw_score=rect_score,
                scores=p.scores,
                generation_method=p.generation_method,
                metadata={**p.metadata, "src_applied": True, "mu_batch": mu_batch}
            )
        )
        
    return rectified_paths

def apply_psa(paths: List[RecommendationPath], alpha: float = 0.1) -> List[RecommendationPath]:
    """
    Apply Position-Specific Advantage (PSA).
    S_final = S_rect * (1 + alpha * pos)
    Note: This is applied to the aggregate path score based on the final position (length).
    
    Args:
        paths: List of paths (already SRC-rectified).
        alpha: The alpha parameter (default 0.1 from config).
        
    Returns:
        New list of paths with PSA-applied scores.
    """
    if not paths:
        return []
        
    final_paths = []
    for p in paths:
        length = len(p.items)
        # Position factor based on path length (1-indexed effectively for the last step)
        # Spec: (1 + alpha * pos). Usually pos refers to the step index. 
        # For a path of length L, the final score adjustment uses L.
        pos_factor = 1 + (alpha * length)
        
        final_score = p.raw_score * pos_factor
        
        final_paths.append(
            RecommendationPath(
                items=p.items,
                raw_score=final_score,
                scores=p.scores,
                generation_method=p.generation_method,
                metadata={
                    **p.metadata, 
                    "psa_applied": True, 
                    "alpha": alpha, 
                    "pos_factor": pos_factor
                }
            )
        )
        
    return final_paths

def apply_prorl_rectification(
    paths: List[RecommendationPath],
    alpha: Optional[float] = None
) -> List[RecommendationPath]:
    """
    Apply full ProRL rectification: SRC followed by PSA.
    
    Args:
        paths: List of paths to rectify.
        alpha: Override alpha from config.
        
    Returns:
        List of fully rectified paths.
    """
    config = get_config()
    if alpha is None:
        alpha = config.get('alpha', 0.1)
        
    rectified = apply_src(paths)
    final = apply_psa(rectified, alpha=alpha)
    
    return final