import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GroundTruthSession:
    """Represents a test session with a seed and ground truth next item."""
    user_id: str
    seed_item_id: str
    ground_truth_item_id: str
    timestamp: Optional[int] = None

class Evaluator:
    """Handles evaluation metrics and comparisons."""

    def __init__(self, k_values: List[int] = None):
        self.k_values = k_values or [5, 10, 20]

    def load_test_sessions(self, path: str) -> List[GroundTruthSession]:
        """Load test sessions from a JSON file."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Test sessions file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        sessions = []
        for item in data:
            sessions.append(GroundTruthSession(
                user_id=item['user_id'],
                seed_item_id=item['seed_item_id'],
                ground_truth_item_id=item['ground_truth_item_id'],
                timestamp=item.get('timestamp')
            ))
        return sessions

    def calculate_precision_recall(self, 
                                   recommendations: List[str], 
                                   ground_truth: str, 
                                   k_values: List[int] = None) -> Dict[str, float]:
        """Calculate Precision@K and Recall@K."""
        k_values = k_values or self.k_values
        metrics = {}
        
        for k in k_values:
            top_k = recommendations[:k]
            hits = 1 if ground_truth in top_k else 0
            
            precision = hits / k if k > 0 else 0.0
            recall = hits / 1.0 if ground_truth else 0.0  # Assuming single ground truth
            
            metrics[f'Precision@{k}'] = precision
            metrics[f'Recall@{k}'] = recall
        
        return metrics

    def calculate_diversity_coverage(self, 
                                     recommendations: List[str], 
                                     item_embeddings: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate Diversity (1 - avg pairwise cosine sim) and Coverage."""
        if not recommendations or len(recommendations) < 2:
            return {'Diversity': 0.0, 'Coverage': 0.0}
        
        # Calculate pairwise cosine similarity
        similarities = []
        unique_items = set()
        
        for i in range(len(recommendations)):
            for j in range(i + 1, len(recommendations)):
                item_a = recommendations[i]
                item_b = recommendations[j]
                
                if item_a in item_embeddings and item_b in item_embeddings:
                    vec_a = item_embeddings[item_a]
                    vec_b = item_embeddings[item_b]
                    
                    norm_a = np.linalg.norm(vec_a)
                    norm_b = np.linalg.norm(vec_b)
                    
                    if norm_a > 0 and norm_b > 0:
                        sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
                        similarities.append(sim)
            
            unique_items.add(recommendations[i])
        
        avg_sim = np.mean(similarities) if similarities else 0.0
        diversity = 1.0 - avg_sim
        coverage = len(unique_items) / len(recommendations) if recommendations else 0.0
        
        return {'Diversity': diversity, 'Coverage': coverage}

    def compare_metrics(self, 
                        greedy_paths_file: str, 
                        rectified_paths_file: str, 
                        output_file: str) -> Dict[str, Any]:
        """
        Compare metrics between greedy and rectified paths.
        Reads paths from JSON files, calculates metrics for each, and outputs comparison.
        """
        logger.info(f"Loading greedy paths from: {greedy_paths_file}")
        logger.info(f"Loading rectified paths from: {rectified_paths_file}")
        
        if not os.path.exists(greedy_paths_file):
            raise FileNotFoundError(f"Greedy paths file not found: {greedy_paths_file}")
        if not os.path.exists(rectified_paths_file):
            raise FileNotFoundError(f"Rectified paths file not found: {rectified_paths_file}")
        
        with open(greedy_paths_file, 'r') as f:
            greedy_data = json.load(f)
        
        with open(rectified_paths_file, 'r') as f:
            rectified_data = json.load(f)
        
        # Aggregate metrics for comparison
        comparison_results = {
            'greedy': {
                'total_paths': 0,
                'avg_score': 0.0,
                'metrics': {}
            },
            'rectified': {
                'total_paths': 0,
                'avg_score': 0.0,
                'metrics': {}
            },
            'comparison': {}
        }
        
        # Process Greedy Paths
        greedy_scores = []
        for path_entry in greedy_data:
            if 'score' in path_entry:
                greedy_scores.append(path_entry['score'])
            if 'path' in path_entry:
                comparison_results['greedy']['total_paths'] += 1
        
        comparison_results['greedy']['avg_score'] = np.mean(greedy_scores) if greedy_scores else 0.0
        
        # Process Rectified Paths
        rectified_scores = []
        for path_entry in rectified_data:
            if 'score' in path_entry:
                rectified_scores.append(path_entry['score'])
            if 'path' in path_entry:
                comparison_results['rectified']['total_paths'] += 1
        
        comparison_results['rectified']['avg_score'] = np.mean(rectified_scores) if rectified_scores else 0.0
        
        # Calculate differences
        score_diff = comparison_results['rectified']['avg_score'] - comparison_results['greedy']['avg_score']
        comparison_results['comparison'] = {
            'score_difference': score_diff,
            'score_improvement_pct': (score_diff / comparison_results['greedy']['avg_score'] * 100) if comparison_results['greedy']['avg_score'] != 0 else 0.0,
            'path_count_difference': comparison_results['rectified']['total_paths'] - comparison_results['greedy']['total_paths']
        }
        
        # Save to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        
        logger.info(f"Metrics comparison saved to: {output_file}")
        return comparison_results

def load_test_sessions(path: str) -> List[GroundTruthSession]:
    """Convenience function to load test sessions."""
    evaluator = Evaluator()
    return evaluator.load_test_sessions(path)

def save_metrics_to_json(metrics: Dict[str, Any], path: str) -> None:
    """Convenience function to save metrics to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
