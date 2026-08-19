import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from src.entities import ItemNode
from src.graph_builder import build_item_vectors
from src.exceptions import DataFetchError

@dataclass
class GroundTruthSession:
    """Represents a held-out test session for cold-start evaluation."""
    user_id: str
    seed_item_id: str
    next_item_id: str
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class Evaluator:
    """
    Evaluates recommendation paths against held-out test sessions.
    Computes Precision@K, Recall@K, Diversity, and Coverage.
    """

    def __init__(self, item_vectors: Dict[str, np.ndarray], k: int = 5):
        """
        Initialize the evaluator.

        Args:
            item_vectors: Dictionary mapping item_id to feature vector (numpy array).
            k: The cutoff K for Precision@K and Recall@K.
        """
        self.item_vectors = item_vectors
        self.k = k

    def load_test_sessions(self, file_path: str) -> List[GroundTruthSession]:
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
            raise DataFetchError(f"Test session file not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise DataFetchError(f"Failed to parse test sessions JSON: {e}")

        sessions = []
        for item in data:
            session = GroundTruthSession(
                user_id=item['user_id'],
                seed_item_id=item['seed_item_id'],
                next_item_id=item['next_item_id'],
                timestamp=item.get('timestamp'),
                metadata=item.get('metadata', {})
            )
            sessions.append(session)
        
        return sessions

    def calculate_precision_recall(self, recommended_items: List[str], ground_truth_item: str) -> Tuple[float, float]:
        """
        Calculate Precision@K and Recall@K.

        Args:
            recommended_items: List of recommended item IDs (ordered by score).
            ground_truth_item: The ground truth next item ID.

        Returns:
            Tuple of (precision, recall).
        """
        top_k_items = recommended_items[:self.k]
        hits = 1 if ground_truth_item in top_k_items else 0

        precision = hits / self.k if self.k > 0 else 0.0
        recall = hits / 1.0  # Since there is exactly one ground truth next item

        return precision, recall

    def calculate_diversity_coverage(self, recommended_items: List[str]) -> Tuple[float, float]:
        """
        Calculate Diversity and Coverage for a list of recommended items.

        Diversity is defined as 1 - average pairwise cosine similarity.
        Coverage is the proportion of unique items in the recommendation list
        relative to the total number of items in the item_vectors.

        Args:
            recommended_items: List of recommended item IDs.

        Returns:
            Tuple of (diversity, coverage).
        """
        if not recommended_items:
            return 0.0, 0.0

        # Filter to items that exist in our vectors
        valid_items = [item for item in recommended_items if item in self.item_vectors]
        
        if len(valid_items) == 0:
            return 0.0, 0.0

        # Calculate Diversity: 1 - avg cosine similarity
        # We need pairwise similarities. If only 1 item, diversity is 1.0 (no pairs to compare)
        if len(valid_items) == 1:
            diversity = 1.0
        else:
            # Build matrix of vectors
            vectors = np.array([self.item_vectors[item] for item in valid_items])
            
            # Compute cosine similarity matrix
            # sklearn cosine_similarity returns a matrix where [i, j] is sim between i and j
            sim_matrix = cosine_similarity(vectors)
            
            # We only want off-diagonal elements (pairs of distinct items)
            # Number of unique pairs
            n = len(valid_items)
            total_pairs = n * (n - 1)
            
            # Sum of off-diagonal elements
            off_diag_sum = np.sum(sim_matrix) - np.trace(sim_matrix)
            
            avg_sim = off_diag_sum / total_pairs if total_pairs > 0 else 0.0
            diversity = 1.0 - avg_sim

        # Calculate Coverage: unique items / total items in catalog
        unique_recommended = set(valid_items)
        total_catalog_size = len(self.item_vectors)
        
        coverage = len(unique_recommended) / total_catalog_size if total_catalog_size > 0 else 0.0

        return diversity, coverage

    def evaluate_sessions(self, sessions: List[GroundTruthSession], 
                          recommendations: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Evaluate a batch of sessions.

        Args:
            sessions: List of test sessions.
            recommendations: Dictionary mapping seed_item_id to list of recommended items.

        Returns:
            Dictionary containing aggregate metrics.
        """
        precisions = []
        recalls = []
        diversities = []
        coverages = []

        for session in sessions:
            seed_id = session.seed_item_id
            next_id = session.next_item_id

            if seed_id not in recommendations:
                continue

            recs = recommendations[seed_id]
            
            # Precision/Recall
            p, r = self.calculate_precision_recall(recs, next_id)
            precisions.append(p)
            recalls.append(r)

            # Diversity/Coverage
            d, c = self.calculate_diversity_coverage(recs)
            diversities.append(d)
            coverages.append(c)

        return {
            'precision_at_k': float(np.mean(precisions)) if precisions else 0.0,
            'recall_at_k': float(np.mean(recalls)) if recalls else 0.0,
            'diversity': float(np.mean(diversities)) if diversities else 0.0,
            'coverage': float(np.mean(coverages)) if coverages else 0.0,
            'num_sessions_evaluated': len(precisions)
        }

def load_test_sessions(file_path: str) -> List[GroundTruthSession]:
    """Convenience function to load test sessions."""
    # Dummy evaluator to access method, or just inline logic
    # Since load_test_sessions is stateless regarding vectors, we can implement directly
    if not os.path.exists(file_path):
        raise DataFetchError(f"Test session file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataFetchError(f"Failed to parse test sessions JSON: {e}")
    
    sessions = []
    for item in data:
        session = GroundTruthSession(
            user_id=item['user_id'],
            seed_item_id=item['seed_item_id'],
            next_item_id=item['next_item_id'],
            timestamp=item.get('timestamp'),
            metadata=item.get('metadata', {})
        )
        sessions.append(session)
    return sessions

def save_metrics_to_json(metrics: Dict[str, Any], output_path: str) -> None:
    """Save evaluation metrics to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def calculate_diversity_coverage(item_vectors: Dict[str, np.ndarray], 
                                 recommended_items: List[str]) -> Tuple[float, float]:
    """
    Standalone function to calculate diversity and coverage.
    Used primarily for T023 implementation verification.
    
    Args:
        item_vectors: Dict of item_id -> vector.
        recommended_items: List of item IDs.
        
    Returns:
        Tuple (diversity, coverage).
    """
    evaluator = Evaluator(item_vectors, k=len(recommended_items))
    return evaluator.calculate_diversity_coverage(recommended_items)

def compute_item_vectors_from_dataframe(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, np.ndarray]:
    """
    Helper to build item vectors from a dataframe.
    
    Args:
        df: DataFrame with 'item_id' and feature columns.
        feature_cols: List of column names to use as features.
        
    Returns:
        Dict mapping item_id to numpy vector.
    """
    vectors = {}
    for _, row in df.iterrows():
        item_id = row['item_id']
        vec = row[feature_cols].values.astype(float)
        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        vectors[item_id] = vec
    return vectors

def save_paths_to_json(paths: List[Dict[str, Any]], file_path: str) -> None:
    """Save a list of paths to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(paths, f, indent=2)

def load_paths_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load a list of paths from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def compare_metrics(greedy_metrics: Dict[str, Any], 
                    prorl_metrics: Dict[str, Any], 
                    output_path: str) -> Dict[str, Any]:
    """
    Compare two sets of metrics and save the comparison.
    
    Args:
        greedy_metrics: Metrics from the greedy baseline.
        prorl_metrics: Metrics from the ProRL rectified method.
        output_path: Path to save the comparison JSON.
        
    Returns:
        Dictionary containing the comparison results.
    """
    comparison = {
        'precision_at_k_diff': prorl_metrics.get('precision_at_k', 0) - greedy_metrics.get('precision_at_k', 0),
        'recall_at_k_diff': prorl_metrics.get('recall_at_k', 0) - greedy_metrics.get('recall_at_k', 0),
        'diversity_diff': prorl_metrics.get('diversity', 0) - greedy_metrics.get('diversity', 0),
        'coverage_diff': prorl_metrics.get('coverage', 0) - greedy_metrics.get('coverage', 0),
        'greedy': greedy_metrics,
        'prorl': prorl_metrics
    }
    
    save_metrics_to_json(comparison, output_path)
    return comparison

def calculate_sc005_status(raw_scores: List[float], rectified_scores: List[float]) -> Dict[str, Any]:
    """
    Calculate the SC-005 status: verify mean absolute difference >= 0.01.
    
    Args:
        raw_scores: List of raw path scores.
        rectified_scores: List of rectified path scores.
        
    Returns:
        Dictionary with status (pass/fail) and details.
    """
    if len(raw_scores) != len(rectified_scores):
        return {
            'status': 'fail',
            'reason': 'Score lists have different lengths',
            'mean_absolute_difference': 0.0
        }
    
    if not raw_scores:
        return {
            'status': 'fail',
            'reason': 'Empty score lists',
            'mean_absolute_difference': 0.0
        }
        
    diffs = [abs(r - p) for r, p in zip(raw_scores, rectified_scores)]
    mad = np.mean(diffs)
    
    status = 'pass' if mad >= 0.01 else 'fail'
    
    return {
        'status': status,
        'mean_absolute_difference': float(mad),
        'threshold': 0.01
    }

def save_sc005_status(status_data: Dict[str, Any], output_path: str) -> None:
    """Save SC-005 status to a JSON file."""
    save_metrics_to_json(status_data, output_path)

def load_item_vectors_from_dataframe(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, np.ndarray]:
    """
    Load item vectors from a dataframe.
    
    Args:
        df: DataFrame containing item data.
        feature_cols: Columns to use as features.
        
    Returns:
        Dict mapping item_id to vector.
    """
    vectors = {}
    for _, row in df.iterrows():
        item_id = str(row['item_id'])
        vec = row[feature_cols].values.astype(float)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        vectors[item_id] = vec
    return vectors