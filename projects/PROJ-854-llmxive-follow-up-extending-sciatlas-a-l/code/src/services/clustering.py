import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

def perform_kmeans_clustering(
    embeddings: np.ndarray, 
    k: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform K-Means clustering on embeddings.
    Returns cluster labels and centroids.
    """
    if embeddings.shape[0] == 0:
        return np.array([]), np.array([])
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    centroids = kmeans.cluster_centers_
    return labels, centroids

def assign_topic_clusters_to_dataframe(
    df: pd.DataFrame, 
    labels: np.ndarray
) -> pd.DataFrame:
    """
    Assign topic cluster labels to the dataframe.
    """
    df = df.copy()
    df['topic_cluster'] = labels
    return df

def compute_cluster_centroids(
    embeddings: np.ndarray, 
    labels: np.ndarray
) -> np.ndarray:
    """
    Compute centroids for each cluster.
    """
    unique_labels = np.unique(labels)
    centroids = []
    for label in unique_labels:
        cluster_points = embeddings[labels == label]
        if len(cluster_points) > 0:
            centroids.append(np.mean(cluster_points, axis=0))
        else:
            centroids.append(np.zeros(embeddings.shape[1]))
    return np.array(centroids)

def get_cluster_statistics(
    labels: np.ndarray
) -> Dict[str, Any]:
    """
    Get statistics about the clusters.
    """
    unique, counts = np.unique(labels, return_counts=True)
    return {
        'num_clusters': len(unique),
        'cluster_sizes': dict(zip(unique, counts)),
        'min_size': np.min(counts),
        'max_size': np.max(counts)
    }
