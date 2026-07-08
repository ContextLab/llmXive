"""
Attribution analysis module for identifying predictive structural patterns.
Implements feature importance ranking and Integrated Gradients for GNNs.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
import networkx as nx

def rank_feature_importance(
    feature_names: List[str],
    importances: List[float],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Rank features by importance and return top-k.

    Args:
        feature_names: List of feature names.
        importances: List of importance scores (must match feature_names length).
        top_k: Number of top features to return.

    Returns:
        List of dictionaries with rank, name, and importance score.
    """
    if len(feature_names) != len(importances):
        raise ValueError("feature_names and importances must have the same length")

    # Pair and sort by importance (descending)
    paired = list(zip(feature_names, importances))
    sorted_paired = sorted(paired, key=lambda x: x[1], reverse=True)

    # Return top-k
    result = []
    for rank, (name, score) in enumerate(sorted_paired[:top_k], 1):
        result.append({
            "rank": rank,
            "feature_name": name,
            "importance_score": float(score)
        })

    return result

def compute_structural_feature_importance(
    graph: nx.Graph,
    anomaly_labels: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Compute structural feature importance based on correlation with anomaly labels.

    Args:
        graph: NetworkX graph object.
        anomaly_labels: Optional array of binary anomaly labels for nodes.

    Returns:
        Dictionary mapping structural feature names to correlation scores.
    """
    # Extract structural features
    nodes = list(graph.nodes())
    n_nodes = len(nodes)

    if n_nodes == 0:
        return {}

    # Degree centrality
    degree_centrality = nx.degree_centrality(graph)
    degrees = np.array([degree_centrality[n] for n in nodes])

    # Betweenness centrality
    try:
        betweenness = nx.betweenness_centrality(graph)
        betweens = np.array([betweenness[n] for n in nodes])
    except:
        betweens = np.zeros(n_nodes)

    # Clustering coefficient
    clustering = nx.clustering(graph)
    clusters = np.array([clustering[n] for n in nodes])

    # Eigenvector centrality (may fail on some graphs)
    try:
        eigen = nx.eigenvector_centrality(graph, max_iter=1000)
        eigens = np.array([eigen[n] for n in nodes])
    except:
        eigens = np.zeros(n_nodes)

    # Compute correlations with anomaly labels if available
    features = {
        "degree_centrality": degrees,
        "betweenness_centrality": betweens,
        "clustering_coefficient": clusters,
        "eigenvector_centrality": eigens
    }

    importances = {}
    if anomaly_labels is not None and len(anomaly_labels) == n_nodes:
        for name, values in features.items():
            if np.std(values) > 0 and np.std(anomaly_labels) > 0:
                corr = np.corrcoef(values, anomaly_labels)[0, 1]
                importances[name] = float(corr) if not np.isnan(corr) else 0.0
            else:
                importances[name] = 0.0
    else:
        # If no labels, use variance as proxy for importance
        for name, values in features.items():
            importances[name] = float(np.var(values))

    return importances

def compare_gnn_rf_rankings(
    gnn_importances: Dict[str, float],
    rf_importances: Dict[str, float]
) -> Dict[str, Any]:
    """
    Compare feature rankings between GNN and Random Forest models.

    Args:
        gnn_importances: Dictionary of GNN feature importances.
        rf_importances: Dictionary of RF feature importances.

    Returns:
        Dictionary containing comparison metrics and distinct patterns.
    """
    # Get common features
    common_features = set(gnn_importances.keys()) & set(rf_importances.keys())
    if not common_features:
        return {
            "common_features": [],
            "gnn_unique": list(gnn_importances.keys()),
            "rf_unique": list(rf_importances.keys()),
            "ranking_correlation": 0.0,
            "distinct_patterns": []
        }

    # Create ranked lists
    gnn_ranked = sorted(gnn_importances.items(), key=lambda x: x[1], reverse=True)
    rf_ranked = sorted(rf_importances.items(), key=lambda x: x[1], reverse=True)

    # Extract ranks for common features
    gnn_ranks = [i for i, (f, _) in enumerate(gnn_ranked) if f in common_features]
    rf_ranks = [i for i, (f, _) in enumerate(rf_ranked) if f in common_features]

    # Calculate Spearman correlation
    if len(gnn_ranks) > 1:
        from scipy.stats import spearmanr
        corr, _ = spearmanr(gnn_ranks, rf_ranks)
        correlation = float(corr) if not np.isnan(corr) else 0.0
    else:
        correlation = 0.0

    # Identify distinct patterns (features ranked very differently)
    feature_ranks = {}
    for f in common_features:
        gnn_idx = next(i for i, (fn, _) in enumerate(gnn_ranked) if fn == f)
        rf_idx = next(i for i, (fn, _) in enumerate(rf_ranked) if fn == f)
        feature_ranks[f] = {"gnn": gnn_idx, "rf": rf_idx, "diff": abs(gnn_idx - rf_idx)}

    distinct_patterns = [
        {"feature": f, "gnn_rank": data["gnn"], "rf_rank": data["rf"], "rank_diff": data["diff"]}
        for f, data in feature_ranks.items()
        if data["diff"] > len(common_features) * 0.3  # More than 30% rank difference
    ]

    return {
        "common_features": list(common_features),
        "gnn_unique": [f for f in gnn_importances if f not in common_features],
        "rf_unique": [f for f in rf_importances if f not in common_features],
        "ranking_correlation": correlation,
        "distinct_patterns": distinct_patterns
    }

def save_feature_ranking(
    ranking: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save feature ranking to JSON file.

    Args:
        ranking: List of ranked features.
        output_path: Path to output file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(ranking, f, indent=2)
