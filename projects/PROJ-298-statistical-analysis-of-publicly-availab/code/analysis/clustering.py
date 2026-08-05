"""
Clustering analysis module for tag co-occurrence and taxonomy alignment.
Implements Jaccard similarity, hierarchical clustering, and permutation tests.
"""
import json
import os
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np


def load_processed_data() -> Optional[Dict]:
    """
    Load processed tag frequency data.
    
    Returns:
        Dictionary containing processed data or None if not found
    """
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "processed"
    data_file = data_path / "processed_data.json"
    
    if not data_file.exists():
        return None
        
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_taxonomy() -> Optional[Dict]:
    """
    Load survey taxonomy from file.
    
    Returns:
        Dictionary containing taxonomy or None if not found
    """
    base_path = Path(__file__).parent.parent.parent
    taxonomy_path = base_path / "data" / "taxonomy"
    taxonomy_file = taxonomy_path / "survey_2023.json"
    
    if not taxonomy_file.exists():
        return None
        
    with open(taxonomy_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        int: Minimum number of single-character edits
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def fuzzy_match_tags(tag: str, taxonomy_labels: List[str], max_distance: int = 2) -> Optional[str]:
    """
    Find best fuzzy match for a tag in taxonomy labels.
    
    Args:
        tag: Tag to match
        taxonomy_labels: List of taxonomy labels to search
        max_distance: Maximum Levenshtein distance for a match
        
    Returns:
        Matching label or None if no match found
    """
    tag_lower = tag.lower().strip()
    best_match = None
    best_distance = max_distance + 1
    
    for label in taxonomy_labels:
        label_lower = label.lower().strip()
        dist = levenshtein_distance(tag_lower, label_lower)
        if dist < best_distance:
            best_distance = dist
            best_match = label
    
    return best_match if best_distance <= max_distance else None


def calculate_cluster_label_alignment_score(
    clusters: Dict[str, List[str]],
    jaccard_matrix: Dict[str, Dict[str, float]]
) -> float:
    """
    Calculate Cluster Label Alignment Score against survey taxonomy.
    
    Uses fuzzy matching (Levenshtein distance <= 2) to match cluster tags
    to taxonomy labels, then computes alignment percentage.
    
    Args:
        clusters: Dictionary of cluster_id -> [tag1, tag2, ...]
        jaccard_matrix: Jaccard similarity matrix (not used directly but required for signature)
        
    Returns:
        float: Alignment score (0.0 to 1.0)
    """
    taxonomy = load_taxonomy()
    if not taxonomy or "labels" not in taxonomy:
        return 0.0
    
    taxonomy_labels = taxonomy["labels"]
    total_tags = 0
    matched_tags = 0
    
    for cluster_id, tags in clusters.items():
        for tag in tags:
            total_tags += 1
            if fuzzy_match_tags(tag, taxonomy_labels) is not None:
                matched_tags += 1
    
    return matched_tags / total_tags if total_tags > 0 else 0.0


def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard similarity between two sets.
    
    Args:
        set1: First set of tags
        set2: Second set of tags
        
    Returns:
        float: Jaccard similarity coefficient (0.0 to 1.0)
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def build_cooccurrence_matrix(processed_data: Dict) -> Dict[str, Set[str]]:
    """
    Build co-occurrence sets from processed data.
    
    For each post, collect all tags and create sets of co-occurring tags.
    
    Args:
        processed_data: Processed data containing posts and tags
        
    Returns:
        Dictionary mapping tag -> set of co-occurring tags
    """
    cooccurrence = {}
    posts = processed_data.get("posts", [])
    
    for post in posts:
        tags = post.get("tags", [])
        if len(tags) < 2:
            continue
        
        tag_set = set(tags)
        for tag in tags:
            if tag not in cooccurrence:
                cooccurrence[tag] = set()
            # Add all other tags in this post as co-occurring
            cooccurrence[tag].update(tag_set - {tag})
    
    return cooccurrence


def compute_jaccard_similarity_matrix(
    cooccurrence: Dict[str, Set[str]]
) -> Dict[str, Dict[str, float]]:
    """
    Compute Jaccard similarity matrix for all tag pairs.
    
    Args:
        cooccurrence: Co-occurrence dictionary from build_cooccurrence_matrix
        
    Returns:
        Nested dictionary of Jaccard similarities
    """
    tags = list(cooccurrence.keys())
    similarity_matrix = {}
    
    for i, tag1 in enumerate(tags):
        similarity_matrix[tag1] = {}
        for j, tag2 in enumerate(tags):
            if i == j:
                similarity_matrix[tag1][tag2] = 1.0
            elif tag2 in similarity_matrix and tag1 in similarity_matrix[tag2]:
                # Use precomputed value
                similarity_matrix[tag1][tag2] = similarity_matrix[tag2][tag1]
            else:
                sim = calculate_jaccard_similarity(cooccurrence[tag1], cooccurrence[tag2])
                similarity_matrix[tag1][tag2] = sim
    
    return similarity_matrix


def perform_hierarchical_clustering(
    processed_data: Dict,
    distance_threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Perform hierarchical clustering based on Jaccard similarity.
    
    Args:
        processed_data: Processed data containing posts and tags
        distance_threshold: Distance threshold for clustering (1 - Jaccard)
        
    Returns:
        Dictionary containing clusters, Jaccard matrix, and metadata
    """
    # Build co-occurrence matrix
    cooccurrence = build_cooccurrence_matrix(processed_data)
    
    # Compute Jaccard similarity matrix
    jaccard_matrix = compute_jaccard_similarity_matrix(cooccurrence)
    
    # Perform simple hierarchical clustering using average linkage
    tags = list(jaccard_matrix.keys())
    n = len(tags)
    
    if n == 0:
        return {"clusters": {}, "jaccard_matrix": {}, "total_tags": 0}
    
    # Convert similarity to distance
    distance_matrix = {t1: {t2: 1.0 - jaccard_matrix[t1][t2] for t2 in tags} for t1 in tags}
    
    # Simple agglomerative clustering
    clusters = {i: {tag} for i, tag in enumerate(tags)}
    cluster_map = {tag: i for i, tag in enumerate(tags)}
    
    while True:
        # Find closest pair
        min_dist = float('inf')
        pair = None
        
        cluster_ids = list(clusters.keys())
        for i in range(len(cluster_ids)):
            for j in range(i + 1, len(cluster_ids)):
                c1, c2 = cluster_ids[i], cluster_ids[j]
                
                # Calculate average distance between clusters
                total_dist = 0.0
                count = 0
                for t1 in clusters[c1]:
                    for t2 in clusters[c2]:
                        total_dist += distance_matrix[t1][t2]
                        count += 1
                
                avg_dist = total_dist / count if count > 0 else float('inf')
                
                if avg_dist < min_dist:
                    min_dist = avg_dist
                    pair = (c1, c2)
        
        if pair is None or min_dist > distance_threshold:
            break
        
        # Merge clusters
        c1, c2 = pair
        clusters[c1] = clusters[c1].union(clusters[c2])
        del clusters[c2]
        
        # Update cluster_map
        for tag in clusters[c1]:
            cluster_map[tag] = c1
    
    # Format output
    result_clusters = {}
    for cluster_id, tag_set in clusters.items():
        result_clusters[f"cluster_{cluster_id}"] = sorted(list(tag_set))
    
    # Perform permutation test for cluster coherence
    perm_test = perform_permutation_test(jaccard_matrix, result_clusters)
    
    return {
        "clusters": result_clusters,
        "jaccard_matrix": jaccard_matrix,
        "total_tags": n,
        "permutation_test": perm_test
    }


def perform_permutation_test(
    jaccard_matrix: Dict[str, Dict[str, float]],
    clusters: Dict[str, List[str]],
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Perform permutation test to validate cluster coherence.
    
    Randomly shuffle tags and calculate intra-cluster similarity
    to establish a null distribution.
    
    Args:
        jaccard_matrix: Jaccard similarity matrix
        clusters: Cluster assignments
        n_permutations: Number of permutations
        
    Returns:
        Dictionary containing p-value and significance
    """
    # Calculate observed intra-cluster similarity
    observed_sim = 0.0
    count = 0
    for cluster_id, tags in clusters.items():
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                t1, t2 = tags[i], tags[j]
                if t1 in jaccard_matrix and t2 in jaccard_matrix[t1]:
                    observed_sim += jaccard_matrix[t1][t2]
                    count += 1
    
    observed_sim = observed_sim / count if count > 0 else 0.0
    
    # Generate null distribution
    all_tags = []
    for tags in clusters.values():
        all_tags.extend(tags)
    
    np.random.seed(42)  # For reproducibility
    null_distribution = []
    
    for _ in range(n_permutations):
        shuffled = np.random.permutation(all_tags)
        perm_sim = 0.0
        perm_count = 0
        idx = 0
        
        for cluster_id, tags in clusters.items():
            cluster_tags = shuffled[idx:idx + len(tags)]
            idx += len(tags)
            
            for i in range(len(cluster_tags)):
                for j in range(i + 1, len(cluster_tags)):
                    t1, t2 = cluster_tags[i], cluster_tags[j]
                    if t1 in jaccard_matrix and t2 in jaccard_matrix[t1]:
                        perm_sim += jaccard_matrix[t1][t2]
                        perm_count += 1
        
        if perm_count > 0:
            null_distribution.append(perm_sim / perm_count)
    
    # Calculate p-value
    if null_distribution:
        p_value = sum(1 for x in null_distribution if x >= observed_sim) / len(null_distribution)
    else:
        p_value = 1.0
    
    return {
        "p_value": p_value,
        "significant": p_value < 0.05,
        "observed_similarity": observed_sim,
        "n_permutations": n_permutations
    }


def calculate_intra_cluster_similarity(
    clusters: Dict[str, List[str]],
    jaccard_matrix: Dict[str, Dict[str, float]]
) -> float:
    """
    Calculate average intra-cluster similarity coefficient.
    
    Args:
        clusters: Cluster assignments
        jaccard_matrix: Jaccard similarity matrix
        
    Returns:
        float: Average intra-cluster similarity
    """
    total_sim = 0.0
    total_pairs = 0
    
    for cluster_id, tags in clusters.items():
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                t1, t2 = tags[i], tags[j]
                if t1 in jaccard_matrix and t2 in jaccard_matrix[t1]:
                    total_sim += jaccard_matrix[t1][t2]
                    total_pairs += 1
    
    return total_sim / total_pairs if total_pairs > 0 else 0.0


def run_clustering_pipeline(processed_data: Dict) -> Dict[str, Any]:
    """
    Run the full clustering analysis pipeline.
    
    Args:
        processed_data: Processed data dictionary
        
    Returns:
        Complete clustering results
    """
    result = perform_hierarchical_clustering(processed_data)
    return result


def main():
    """
    Demo/main entry point for clustering module.
    """
    print("Clustering Module")
    print("-" * 40)
    
    data = load_processed_data()
    if data:
        print(f"Loaded processed data with {len(data.get('posts', []))} posts")
        result = run_clustering_pipeline(data)
        print(f"Found {len(result.get('clusters', {}))} clusters")
        print(f"Permutation test p-value: {result.get('permutation_test', {}).get('p_value', 'N/A')}")
    else:
        print("No processed data found. Run preprocessing first.")


if __name__ == "__main__":
    main()