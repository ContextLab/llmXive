"""
Clustering analysis module for tag co-occurrence analysis.
Implements Jaccard similarity, hierarchical clustering, and permutation tests.
"""
import json
import os
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

def load_processed_data(processed_dir: Path) -> Dict[str, Any]:
    """Load processed tag frequency data."""
    data_file = processed_dir / "monthly_tag_frequencies.json"
    if not data_file.exists():
        raise FileNotFoundError(f"Processed data file not found: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_taxonomy(taxonomy_dir: Path) -> Dict[str, Any]:
    """Load survey taxonomy data."""
    taxonomy_file = taxonomy_dir / "survey_2023.json"
    if not taxonomy_file.exists():
        return {"metadata": {"version": "unknown"}, "clusters": []}
    
    with open(taxonomy_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def build_cooccurrence_matrix(posts_data: Dict[str, Any]) -> Dict[str, Set[str]]:
    """Build co-occurrence matrix from posts data."""
    tag_cooccurrence: Dict[str, Set[str]] = {}
    
    posts = posts_data.get('posts', [])
    for post in posts:
        tags = post.get('tags', [])
        for i, tag1 in enumerate(tags):
            if tag1 not in tag_cooccurrence:
                tag_cooccurrence[tag1] = set()
            for tag2 in tags[i+1:]:
                tag_cooccurrence[tag1].add(tag2)
                if tag2 not in tag_cooccurrence:
                    tag_cooccurrence[tag2] = set()
                tag_cooccurrence[tag2].add(tag1)
    
    return tag_cooccurrence

def compute_jaccard_similarity_matrix(tag_cooccurrence: Dict[str, Set[str]]) -> Dict[str, float]:
    """Compute Jaccard similarity matrix for all tag pairs."""
    similarity_matrix = {}
    tags = list(tag_cooccurrence.keys())
    
    for i, tag1 in enumerate(tags):
        for j in range(i + 1, len(tags)):
            tag2 = tags[j]
            sim = calculate_jaccard_similarity(tag_cooccurrence[tag1], tag_cooccurrence[tag2])
            # Store with both key formats for flexibility
            key1 = f"{tag1}_{tag2}"
            key2 = f"{tag2}_{tag1}"
            key3 = (tag1, tag2)
            key4 = (tag2, tag1)
            
            similarity_matrix[key1] = sim
            similarity_matrix[key2] = sim
            similarity_matrix[key3] = sim
            similarity_matrix[key4] = sim
    
    return similarity_matrix

def perform_hierarchical_clustering(
    similarity_matrix: Dict[str, float],
    tags: List[str],
    threshold: float = 0.3
) -> Dict[str, Any]:
    """Perform hierarchical clustering based on Jaccard similarity."""
    # Simple agglomerative clustering implementation
    clusters = {tag: {tag} for tag in tags}
    cluster_id = 0
    tag_to_cluster = {tag: cluster_id for tag in tags}
    cluster_id += 1
    
    # Sort pairs by similarity (descending)
    pairs = []
    for key, sim in similarity_matrix.items():
        if isinstance(key, tuple):
            pairs.append((sim, key[0], key[1]))
        else:
            # Parse string key
            parts = key.split('_')
            if len(parts) == 2:
                pairs.append((sim, parts[0], parts[1]))
    
    pairs.sort(reverse=True)
    
    # Merge clusters based on threshold
    for sim, tag1, tag2 in pairs:
        if sim < threshold:
            break
        
        cluster1 = tag_to_cluster[tag1]
        cluster2 = tag_to_cluster[tag2]
        
        if cluster1 != cluster2:
            # Merge smaller into larger
            if len(clusters[cluster1]) < len(clusters[cluster2]):
                target, source = cluster2, cluster1
            else:
                target, source = cluster1, cluster2
            
            clusters[target].update(clusters[source])
            del clusters[source]
            
            # Update tag mappings
            for tag in clusters[target]:
                tag_to_cluster[tag] = target
    
    # Format output
    result_clusters = {}
    for cid, members in clusters.items():
        result_clusters[f"cluster_{cid}"] = list(members)
    
    return {
        "clusters": result_clusters,
        "num_clusters": len(clusters),
        "threshold_used": threshold
    }

def fuzzy_match_tags(cluster_tags: List[str], taxonomy_clusters: List[Dict[str, Any]]) -> List[Tuple[str, str, float]]:
    """
    Match cluster tags to taxonomy clusters using fuzzy matching.
    Returns list of (cluster_id, matched_taxonomy_label, confidence).
    """
    matches = []
    
    for cluster_tags in cluster_tags:
        best_match = None
        best_confidence = 0.0
        
        for tax_cluster in taxonomy_clusters:
            tax_label = tax_cluster.get('label', '').lower()
            tax_tags = [t.lower() for t in tax_cluster.get('tags', [])]
            
            # Simple overlap-based matching
            overlap = len(set(cluster_tags) & set(tax_tags))
            confidence = overlap / max(len(cluster_tags), len(tax_tags))
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = tax_label
        
        if best_match and best_confidence > 0.3:
            matches.append((best_match, best_confidence))
    
    return matches

def calculate_cluster_label_alignment_score(clusters_data: Dict[str, Any], taxonomy_data: Dict[str, Any]) -> float:
    """
    Calculate Cluster Label Alignment Score using fuzzy matching.
    Score is the average confidence of best matches for each cluster.
    """
    cluster_assignments = clusters_data.get('cluster_assignments', {})
    if not cluster_assignments:
        return 0.0
    
    # Group tags by cluster
    cluster_groups = {}
    for tag, cluster_id in cluster_assignments.items():
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(tag)
    
    taxonomy_clusters = taxonomy_data.get('clusters', [])
    if not taxonomy_clusters:
        return 0.0
    
    total_confidence = 0.0
    matched_clusters = 0
    
    for cluster_id, tags in cluster_groups.items():
        matches = fuzzy_match_tags(tags, taxonomy_clusters)
        if matches:
            best_conf = max(conf for _, conf in matches)
            if best_conf > 0.3:
                total_confidence += best_conf
                matched_clusters += 1
    
    if matched_clusters == 0:
        return 0.0
    
    return total_confidence / matched_clusters

def perform_permutation_test(clusters_data: Dict[str, Any], n_iterations: int = 1000) -> Dict[str, Any]:
    """
    Perform permutation test to validate cluster coherence.
    Returns p-value and test statistics.
    """
    import random
    
    similarity_matrix = clusters_data.get('jaccard_similarity', {})
    cluster_assignments = clusters_data.get('cluster_assignments', {})
    
    if not similarity_matrix or not cluster_assignments:
        return {"p_value": 1.0, "statistic": 0.0, "coherent": False}
    
    # Calculate observed intra-cluster similarity
    observed_sim = 0.0
    count = 0
    
    cluster_groups = {}
    for tag, cluster_id in cluster_assignments.items():
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(tag)
    
    for cluster_id, tags in cluster_groups.items():
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                key = f"{tags[i]}_{tags[j]}"
                if key in similarity_matrix:
                    observed_sim += similarity_matrix[key]
                    count += 1
    
    observed_mean = observed_sim / count if count > 0 else 0.0
    
    # Permutation test
    permuted_sims = []
    all_tags = list(cluster_assignments.keys())
    
    for _ in range(n_iterations):
        random.shuffle(all_tags)
        perm_cluster_assignments = {tag: cluster_assignments[tag] for tag in all_tags}
        
        perm_sim = 0.0
        perm_count = 0
        
        perm_cluster_groups = {}
        for tag, cluster_id in perm_cluster_assignments.items():
            if cluster_id not in perm_cluster_groups:
                perm_cluster_groups[cluster_id] = []
            perm_cluster_groups[cluster_id].append(tag)
        
        for cluster_id, tags in perm_cluster_groups.items():
            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    key = f"{tags[i]}_{tags[j]}"
                    if key in similarity_matrix:
                        perm_sim += similarity_matrix[key]
                        perm_count += 1
        
        if perm_count > 0:
            permuted_sims.append(perm_sim / perm_count)
    
    # Calculate p-value
    p_value = sum(1 for s in permuted_sims if s >= observed_mean) / n_iterations
    
    return {
        "p_value": p_value,
        "observed_mean_similarity": observed_mean,
        "mean_permuted_similarity": sum(permuted_sims) / len(permuted_sims) if permuted_sims else 0.0,
        "coherent": p_value < 0.05
    }

def run_clustering_pipeline(processed_dir: Path, taxonomy_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Run the complete clustering pipeline."""
    # Load data
    posts_data = load_processed_data(processed_dir)
    taxonomy_data = load_taxonomy(taxonomy_dir)
    
    # Build co-occurrence matrix
    tag_cooccurrence = build_cooccurrence_matrix(posts_data)
    
    # Compute similarity matrix
    similarity_matrix = compute_jaccard_similarity_matrix(tag_cooccurrence)
    
    # Get all tags
    all_tags = list(tag_cooccurrence.keys())
    
    # Perform hierarchical clustering
    clustering_result = perform_hierarchical_clustering(similarity_matrix, all_tags, threshold=0.3)
    
    # Build cluster assignments
    cluster_assignments = {}
    for cluster_id, members in clustering_result['clusters'].items():
        for tag in members:
            cluster_assignments[tag] = cluster_id
    
    # Perform permutation test
    permutation_result = perform_permutation_test({
        'cluster_assignments': cluster_assignments,
        'jaccard_similarity': similarity_matrix
    })
    
    # Calculate alignment score
    alignment_score = calculate_cluster_label_alignment_score({
        'cluster_assignments': cluster_assignments
    }, taxonomy_data)
    
    # Prepare output
    output = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "version": "1.0",
            "description": "Tag co-occurrence clustering results"
        },
        "clusters": clustering_result['clusters'],
        "cluster_assignments": cluster_assignments,
        "jaccard_similarity": similarity_matrix,
        "taxonomy_matches": fuzzy_match_tags(list(clustering_result['clusters'].values()), taxonomy_data.get('clusters', [])),
        "permutation_test": permutation_result,
        "alignment_score": alignment_score,
        "num_tags": len(all_tags),
        "num_clusters": clustering_result['num_clusters']
    }
    
    # Save results
    output_file = output_dir / "clustering_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return output

def main():
    """Main entry point for clustering analysis."""
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    taxonomy_dir = project_root / "data" / "taxonomy"
    output_dir = processed_dir
    
    if not processed_dir.exists():
        processed_dir.mkdir(parents=True, exist_ok=True)
    
    if not taxonomy_dir.exists():
        taxonomy_dir.mkdir(parents=True, exist_ok=True)
    
    results = run_clustering_pipeline(processed_dir, taxonomy_dir, output_dir)
    print(f"Clustering pipeline complete. Results saved to {output_dir / 'clustering_results.json'}")
    return results

if __name__ == "__main__":
    main()