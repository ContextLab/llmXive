import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
import networkx as nx

def rank_feature_importance(
    feature_importance: Dict[str, float],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Rank features by importance score.
    
    Args:
        feature_importance: Dictionary mapping feature names to importance scores.
        top_k: Number of top features to return.
        
    Returns:
        List of dictionaries with 'feature', 'importance', and 'rank'.
    """
    sorted_features = sorted(
        feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]
    
    return [
        {
            'feature': name,
            'importance': float(score),
            'rank': idx + 1
        }
        for idx, (name, score) in enumerate(sorted_features)
    ]

def compute_structural_feature_importance(
    graph: nx.Graph,
    anomaly_labels: Dict[int, int],
    method: str = 'degree'
) -> Dict[str, float]:
    """
    Compute structural feature importance based on graph properties.
    
    Args:
        graph: NetworkX graph object.
        anomaly_labels: Dictionary mapping node IDs to binary labels (0=normal, 1=anomaly).
        method: Method to compute importance ('degree', 'betweenness', 'eigenvector').
        
    Returns:
        Dictionary of structural feature importance scores.
    """
    if method == 'degree':
        centrality = nx.degree_centrality(graph)
    elif method == 'betweenness':
        centrality = nx.betweenness_centrality(graph)
    elif method == 'eigenvector':
        try:
            centrality = nx.eigenvector_centrality(graph, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            centrality = nx.degree_centrality(graph)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Correlate centrality with anomaly labels
    nodes = list(graph.nodes())
    centrality_values = [centrality.get(n, 0) for n in nodes]
    anomaly_values = [anomaly_labels.get(n, 0) for n in nodes]
    
    if len(set(anomaly_values)) > 1:
        correlation = np.corrcoef(centrality_values, anomaly_values)[0, 1]
    else:
        correlation = 0.0
        
    return {
        f"{method}_centrality_correlation": float(correlation),
        "mean_centrality": float(np.mean(centrality_values)),
        "std_centrality": float(np.std(centrality_values))
    }

def compare_gnn_rf_rankings(
    gnn_ranking: List[Dict[str, Any]],
    rf_ranking: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare feature rankings between GNN and Random Forest models.
    
    Args:
        gnn_ranking: Top features from GNN attribution.
        rf_ranking: Top features from RF importance.
        
    Returns:
        Dictionary with comparison metrics and distinct patterns.
    """
    gnn_features = [item['feature'] for item in gnn_ranking]
    rf_features = [item['feature'] for item in rf_ranking]
    
    common_features = set(gnn_features) & set(rf_features)
    gnn_unique = set(gnn_features) - set(rf_features)
    rf_unique = set(rf_features) - set(gnn_features)
    
    # Calculate Spearman correlation of rankings for common features
    if len(common_features) > 1:
        gnn_ranks = {f: i+1 for i, f in enumerate(gnn_features)}
        rf_ranks = {f: i+1 for i, f in enumerate(rf_features)}
        
        common_sorted = sorted(common_features)
        gnn_rank_vals = [gnn_ranks[f] for f in common_sorted]
        rf_rank_vals = [rf_ranks[f] for f in common_sorted]
        
        correlation = np.corrcoef(gnn_rank_vals, rf_rank_vals)[0, 1]
    else:
        correlation = 0.0
        
    return {
        'common_features': list(common_features),
        'gnn_unique_features': list(gnn_unique),
        'rf_unique_features': list(rf_unique),
        'ranking_correlation': float(correlation),
        'gnn_top_3': gnn_features[:3],
        'rf_top_3': rf_features[:3]
    }

def save_feature_ranking(
    ranking: List[Dict[str, Any]],
    comparison: Optional[Dict[str, Any]] = None,
    output_path: str = 'data/results/feature_importance_ranking.json'
) -> None:
    """
    Save feature ranking and comparison results to JSON.
    
    Args:
        ranking: List of ranked features.
        comparison: Optional comparison dictionary from compare_gnn_rf_rankings.
        output_path: Path to output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result = {
        'ranked_features': ranking,
        'total_features': len(ranking)
    }
    
    if comparison:
        result['comparison'] = comparison
        
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logging = __import__('logging')
    logging.info(f"Feature ranking saved to {output_path}")
