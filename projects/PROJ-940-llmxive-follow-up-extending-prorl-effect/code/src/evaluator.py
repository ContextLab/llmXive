import json
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

@dataclass
class GroundTruthSession:
    user_id: str
    seed_item_id: str
    next_item_id: str
    timestamp: Optional[float] = None
    context_features: Optional[Dict[str, Any]] = None

class Evaluator:
    def __init__(self, test_sessions: List[GroundTruthSession]):
        self.test_sessions = test_sessions

    def calculate_precision_recall(self, 
                                  predicted_items: List[str], 
                                  ground_truth_items: List[str], 
                                  k: Optional[int] = None) -> Tuple[float, float]:
        if k is not None:
            predicted_items = predicted_items[:k]
        
        if not ground_truth_items:
            return 0.0, 0.0
        
        pred_set = set(predicted_items)
        gt_set = set(ground_truth_items)
        
        intersection = pred_set.intersection(gt_set)
        
        precision = len(intersection) / len(predicted_items) if predicted_items else 0.0
        recall = len(intersection) / len(gt_set) if gt_set else 0.0
        
        return precision, recall

    def calculate_diversity_coverage(self, 
                                    predicted_items: List[str], 
                                    item_vectors: Dict[str, np.ndarray]) -> Tuple[float, float]:
        if len(predicted_items) < 2:
            return 1.0, 1.0 if predicted_items else 0.0
        
        covered_items = set(predicted_items)
        coverage = len(covered_items) / len(item_vectors) if item_vectors else 0.0
        
        similarities = []
        for i in range(len(predicted_items)):
            for j in range(i + 1, len(predicted_items)):
                if predicted_items[i] in item_vectors and predicted_items[j] in item_vectors:
                    vec_i = item_vectors[predicted_items[i]]
                    vec_j = item_vectors[predicted_items[j]]
                    sim = np.dot(vec_i, vec_j) / (np.linalg.norm(vec_i) * np.linalg.norm(vec_j) + 1e-8)
                    similarities.append(sim)
        
        diversity = 1.0 - (np.mean(similarities) if similarities else 0.0)
        
        return diversity, coverage

    def compare_metrics(self, 
                       greedy_paths_file: str, 
                       rectified_paths_file: str, 
                       item_vectors: Optional[Dict[str, np.ndarray]] = None,
                       k: int = 10) -> Dict[str, Any]:
        """
        Compare metrics between greedy and rectified paths.
        
        Args:
            greedy_paths_file: Path to JSON file containing greedy paths
            rectified_paths_file: Path to JSON file containing rectified paths
            item_vectors: Dictionary mapping item_id to feature vectors for diversity/coverage
            k: Number of top items to consider for precision/recall
        
        Returns:
            Dictionary containing comparison metrics
        """
        # Load paths
        with open(greedy_paths_file, 'r') as f:
            greedy_data = json.load(f)
        
        with open(rectified_paths_file, 'r') as f:
            rectified_data = json.load(f)
        
        # Aggregate metrics
        greedy_metrics = []
        rectified_metrics = []
        
        # Ensure both datasets have same keys for comparison
        all_seed_ids = set(greedy_data.keys()) & set(rectified_data.keys())
        
        for seed_id in all_seed_ids:
            greedy_paths = greedy_data[seed_id]
            rectified_paths = rectified_data[seed_id]
            
            # Find corresponding ground truth
            gt_session = next((s for s in self.test_sessions if s.seed_item_id == seed_id), None)
            if not gt_session:
                continue
            
            ground_truth = [gt_session.next_item_id]
            
            # Calculate metrics for greedy paths
            greedy_predicted = []
            for path in greedy_paths:
                greedy_predicted.extend(path.get('items', []))
            greedy_predicted = list(dict.fromkeys(greedy_predicted))[:k]
            
            greedy_prec, greedy_rec = self.calculate_precision_recall(greedy_predicted, ground_truth, k)
            greedy_div, greedy_cov = 0.0, 0.0
            if item_vectors:
                greedy_div, greedy_cov = self.calculate_diversity_coverage(greedy_predicted, item_vectors)
            
            greedy_metrics.append({
                'precision': greedy_prec,
                'recall': greedy_rec,
                'diversity': greedy_div,
                'coverage': greedy_cov
            })
            
            # Calculate metrics for rectified paths
            rectified_predicted = []
            for path in rectified_paths:
                rectified_predicted.extend(path.get('items', []))
            rectified_predicted = list(dict.fromkeys(rectified_predicted))[:k]
            
            rectified_prec, rectified_rec = self.calculate_precision_recall(rectified_predicted, ground_truth, k)
            rectified_div, rectified_cov = 0.0, 0.0
            if item_vectors:
                rectified_div, rectified_cov = self.calculate_diversity_coverage(rectified_predicted, item_vectors)
            
            rectified_metrics.append({
                'precision': rectified_prec,
                'recall': rectified_rec,
                'diversity': rectified_div,
                'coverage': rectified_cov
            })
        
        # Calculate aggregate statistics
        if not greedy_metrics or not rectified_metrics:
            return {
                'status': 'no_data',
                'message': 'No matching seed IDs found between greedy and rectified paths',
                'greedy_aggregate': {},
                'rectified_aggregate': {},
                'improvements': {}
            }
        
        greedy_agg = {
            'precision': np.mean([m['precision'] for m in greedy_metrics]),
            'recall': np.mean([m['recall'] for m in greedy_metrics]),
            'diversity': np.mean([m['diversity'] for m in greedy_metrics]),
            'coverage': np.mean([m['coverage'] for m in greedy_metrics]),
            'precision_std': np.std([m['precision'] for m in greedy_metrics]),
            'recall_std': np.std([m['recall'] for m in greedy_metrics]),
            'diversity_std': np.std([m['diversity'] for m in greedy_metrics]),
            'coverage_std': np.std([m['coverage'] for m in greedy_metrics])
        }
        
        rectified_agg = {
            'precision': np.mean([m['precision'] for m in rectified_metrics]),
            'recall': np.mean([m['recall'] for m in rectified_metrics]),
            'diversity': np.mean([m['diversity'] for m in rectified_metrics]),
            'coverage': np.mean([m['coverage'] for m in rectified_metrics]),
            'precision_std': np.std([m['precision'] for m in rectified_metrics]),
            'recall_std': np.std([m['recall'] for m in rectified_metrics]),
            'diversity_std': np.std([m['diversity'] for m in rectified_metrics]),
            'coverage_std': np.std([m['coverage'] for m in rectified_metrics])
        }
        
        improvements = {
            'precision_change': rectified_agg['precision'] - greedy_agg['precision'],
            'recall_change': rectified_agg['recall'] - greedy_agg['recall'],
            'diversity_change': rectified_agg['diversity'] - greedy_agg['diversity'],
            'coverage_change': rectified_agg['coverage'] - greedy_agg['coverage'],
            'precision_percent_change': (rectified_agg['precision'] - greedy_agg['precision']) / (greedy_agg['precision'] + 1e-8) * 100,
            'recall_percent_change': (rectified_agg['recall'] - greedy_agg['recall']) / (greedy_agg['recall'] + 1e-8) * 100,
            'diversity_percent_change': (rectified_agg['diversity'] - greedy_agg['diversity']) / (greedy_agg['diversity'] + 1e-8) * 100,
            'coverage_percent_change': (rectified_agg['coverage'] - greedy_agg['coverage']) / (greedy_agg['coverage'] + 1e-8) * 100
        }
        
        comparison_result = {
            'status': 'success',
            'sample_size': len(greedy_metrics),
            'k': k,
            'greedy_aggregate': greedy_agg,
            'rectified_aggregate': rectified_agg,
            'improvements': improvements,
            'individual_results': list(zip(all_seed_ids, greedy_metrics, rectified_metrics))
        }
        
        return comparison_result

    def save_comparison_results(self, 
                               comparison_results: Dict[str, Any], 
                               output_path: str) -> None:
        """Save comparison results to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)