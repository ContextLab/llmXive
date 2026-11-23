import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import logging

from src.entities import RecommendationPath
from src.exceptions import DataFetchError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GroundTruthSession:
    """Represents a ground truth session for evaluation."""
    user_id: str
    seed_item_id: str
    next_item_id: str
    timestamp: float
    history: List[str] = field(default_factory=list)

def load_test_sessions(file_path: str) -> List[GroundTruthSession]:
    """
    Load test sessions from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing test sessions.
        
    Returns:
        List of GroundTruthSession objects.
        
    Raises:
        DataFetchError: If the file cannot be loaded or parsed.
    """
    if not os.path.exists(file_path):
        raise DataFetchError(f"Test sessions file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        sessions = []
        for item in data:
            session = GroundTruthSession(
                user_id=item.get('user_id'),
                seed_item_id=item.get('seed_item_id'),
                next_item_id=item.get('next_item_id'),
                timestamp=item.get('timestamp', 0.0),
                history=item.get('history', [])
            )
            sessions.append(session)
        
        logger.info(f"Loaded {len(sessions)} test sessions from {file_path}")
        return sessions
    except Exception as e:
        raise DataFetchError(f"Failed to load test sessions: {e}")

def save_metrics_to_json(metrics: Dict[str, Any], file_path: str) -> None:
    """
    Save metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics to save.
        file_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {file_path}")

def compare_metrics(
    greedy_results: List[Dict[str, Any]],
    prorl_results: List[Dict[str, Any]],
    test_sessions: List[GroundTruthSession]
) -> Dict[str, Any]:
    """
    Compare metrics between Greedy and ProRL scored paths.
    
    This function calculates Precision@K, Recall@K, Diversity, and Coverage
    for both Greedy and ProRL results and returns a comparison dictionary.
    
    Args:
        greedy_results: List of dictionaries containing Greedy path results.
                        Each dict should have 'paths' and 'metrics' keys.
        prorl_results: List of dictionaries containing ProRL path results.
                       Each dict should have 'paths' and 'metrics' keys.
        test_sessions: List of GroundTruthSession objects for evaluation.
        
    Returns:
        Dictionary with keys 'greedy', 'prorl', and 'delta' containing
        the respective metrics.
    """
    if not greedy_results or not prorl_results:
        logger.warning("Empty results provided for comparison")
        return {
            "greedy": {},
            "prorl": {},
            "delta": {},
            "status": "incomplete"
        }
    
    # Calculate metrics for Greedy results
    greedy_metrics = _aggregate_metrics(greedy_results, test_sessions)
    
    # Calculate metrics for ProRL results
    prorl_metrics = _aggregate_metrics(prorl_results, test_sessions)
    
    # Calculate delta
    delta = {}
    for key in greedy_metrics:
        if key in prorl_metrics:
            delta[key] = prorl_metrics[key] - greedy_metrics[key]
        else:
            delta[key] = None
    
    comparison = {
        "greedy": greedy_metrics,
        "prorl": prorl_metrics,
        "delta": delta,
        "status": "complete"
    }
    
    return comparison

def _aggregate_metrics(
    results: List[Dict[str, Any]],
    test_sessions: List[GroundTruthSession]
) -> Dict[str, float]:
    """
    Aggregate metrics across all results.
    
    Args:
        results: List of result dictionaries.
        test_sessions: List of ground truth sessions.
        
    Returns:
        Dictionary of aggregated metrics.
    """
    precision_scores = []
    recall_scores = []
    diversity_scores = []
    coverage_scores = []
    
    # Create a mapping of seed_item_id to ground truth next_item_id
    ground_truth_map = {
        session.seed_item_id: session.next_item_id 
        for session in test_sessions
    }
    
    # Create item feature map for diversity calculation
    # Assuming results contain item features or we use item IDs
    all_items = set()
    for result in results:
        if 'paths' in result:
            for path in result['paths']:
                if 'items' in path:
                    all_items.update(path['items'])
    
    # For each result, calculate metrics
    for result in results:
        if 'paths' not in result or not result['paths']:
            continue
        
        for path in result['paths']:
            seed_item = path.get('seed_item_id')
            if seed_item not in ground_truth_map:
                continue
            
            ground_truth_next = ground_truth_map[seed_item]
            recommended_items = path.get('items', [])
            
            # Calculate Precision@K and Recall@K (K=5)
            k = min(5, len(recommended_items))
            top_k = recommended_items[:k]
            
            if ground_truth_next in top_k:
                precision_scores.append(1.0)
                recall_scores.append(1.0)
            else:
                precision_scores.append(0.0)
                recall_scores.append(0.0)
            
            # Calculate Diversity (1 - avg pairwise similarity)
            # Simplified: using item ID hash as proxy for features
            if len(recommended_items) > 1:
                diversity = 1.0 - _calculate_avg_similarity(recommended_items)
                diversity_scores.append(diversity)
            else:
                diversity_scores.append(1.0)
            
            # Calculate Coverage (unique items / total possible)
            # Simplified: count of unique items in recommendations
            unique_items = len(set(recommended_items))
            coverage_scores.append(unique_items / max(len(recommended_items), 1))
    
    if not precision_scores:
        return {
            "precision_at_5": 0.0,
            "recall_at_5": 0.0,
            "diversity": 0.0,
            "coverage": 0.0
        }
    
    return {
        "precision_at_5": float(np.mean(precision_scores)),
        "recall_at_5": float(np.mean(recall_scores)),
        "diversity": float(np.mean(diversity_scores)),
        "coverage": float(np.mean(coverage_scores))
    }

def _calculate_avg_similarity(items: List[str]) -> float:
    """
    Calculate average pairwise similarity between items.
    
    Simplified implementation using item ID characteristics.
    In a real implementation, this would use item embeddings.
    
    Args:
        items: List of item IDs.
        
    Returns:
        Average similarity score (0.0 to 1.0).
    """
    if len(items) <= 1:
        return 0.0
    
    # Simple similarity proxy: hash-based similarity
    # In practice, this would use actual item features/embeddings
    similarities = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            # Placeholder: random similarity for demonstration
            # Replace with actual cosine similarity on embeddings
            sim = np.random.uniform(0.0, 1.0)
            similarities.append(sim)
    
    return float(np.mean(similarities)) if similarities else 0.0

def load_paths_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load paths from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        List of path dictionaries.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Paths file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_paths_to_json(paths: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save paths to a JSON file.
    
    Args:
        paths: List of path dictionaries.
        file_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(paths, f, indent=2)
    logger.info(f"Saved {len(paths)} paths to {file_path}")