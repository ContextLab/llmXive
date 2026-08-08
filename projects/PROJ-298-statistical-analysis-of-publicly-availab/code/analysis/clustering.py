import json
import os
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Levenshtein distance implementation (no external dependency required for this simple metric)
def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein distance between two strings."""
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

def fuzzy_match_tags(cluster_label: str, taxonomy_labels: List[str], max_distance: int = 2) -> Optional[str]:
    """
    Find a matching label in the taxonomy for a given cluster label using fuzzy matching.
    Returns the matched taxonomy label if distance <= max_distance, else None.
    """
    cluster_label_lower = cluster_label.lower().strip()
    for tax_label in taxonomy_labels:
        tax_label_lower = tax_label.lower().strip()
        dist = levenshtein_distance(cluster_label_lower, tax_label_lower)
        if dist <= max_distance:
            return tax_label
    return None

def load_processed_data(file_path: str) -> Dict[str, Any]:
    """Load processed clustering data from JSON."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_taxonomy(file_path: str) -> Dict[str, Any]:
    """Load taxonomy data from JSON."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_intra_cluster_similarity(cluster: List[str], jaccard_matrix: Dict[str, Dict[str, float]]) -> float:
    """Calculate the average intra-cluster similarity for a given cluster."""
    if len(cluster) < 2:
        return 1.0
    
    total_similarity = 0.0
    count = 0
    for i in range(len(cluster)):
        for j in range(i + 1, len(cluster)):
            tag1, tag2 = cluster[i], cluster[j]
            if tag1 in jaccard_matrix and tag2 in jaccard_matrix[tag1]:
                total_similarity += jaccard_matrix[tag1][tag2]
                count += 1
            elif tag2 in jaccard_matrix and tag1 in jaccard_matrix[tag2]:
                total_similarity += jaccard_matrix[tag2][tag1]
                count += 1
    
    if count == 0:
        return 0.0
    return total_similarity / count

def calculate_cluster_label_alignment_score(clusters: List[List[str]], taxonomy: Dict[str, Any], max_distance: int = 2) -> float:
    """
    Calculate the Cluster Label Alignment Score.
    This score represents the fraction of cluster labels that can be fuzzy-matched
    to a label in the provided taxonomy.
    """
    if not clusters:
        return 0.0

    # Extract all unique labels from the taxonomy
    # Assuming taxonomy structure: {"categories": [{"name": "...", "tags": [...]}]} or similar
    # We need a flat list of all valid category names or tag group names from the taxonomy
    taxonomy_labels = []
    
    # Robust extraction of taxonomy labels based on common survey JSON structures
    if "categories" in taxonomy:
        for cat in taxonomy["categories"]:
            if isinstance(cat, dict):
                if "name" in cat:
                    taxonomy_labels.append(str(cat["name"]))
                if "label" in cat:
                    taxonomy_labels.append(str(cat["label"]))
    elif "categories" in taxonomy:
        # Fallback if structure is slightly different
        for key, value in taxonomy["categories"].items():
            taxonomy_labels.append(str(key))
    
    # If the taxonomy is a flat dict of categories
    if not taxonomy_labels and isinstance(taxonomy, dict):
        for key in taxonomy.keys():
            if key not in ["metadata", "info"]:
                taxonomy_labels.append(str(key))

    if not taxonomy_labels:
        # If we still can't find labels, we might be looking at a different structure.
        # As a fallback, we might assume the taxonomy is a list of strings or similar, 
        # but based on T007 description, it maps tags to categories.
        # Let's assume the taxonomy has a 'categories' key with a list of objects having 'name'.
        pass

    matched_count = 0
    total_clusters = len(clusters)

    for cluster in clusters:
        if not cluster:
            continue
        
        # Heuristic: Use the most frequent tag or the first tag as the representative label for the cluster
        # Or, if the cluster has a "label" attribute stored elsewhere, use that.
        # Since we only have a list of tags here, we try to match the "concept" of the cluster.
        # A simple approach for this metric: Check if ANY tag in the cluster matches a taxonomy label,
        # OR if the cluster's "dominant" tag (most common) matches.
        # However, the task says "Cluster Label Alignment Score". Usually, clusters are assigned labels.
        # If we don't have explicit labels, we assume the cluster is named after its most frequent tag 
        # or we check if the set of tags in the cluster maps to a taxonomy category.
        
        # Simpler interpretation for this specific task:
        # Does the cluster contain a tag that matches a taxonomy label?
        # Or does the cluster's "name" (if we derive it) match?
        # Let's assume we derive the cluster label from the first tag or the most frequent tag in the cluster.
        
        # Let's use the first tag as the representative for simplicity in this context, 
        # or better: check if any tag in the cluster fuzzy matches a taxonomy label.
        # But the metric is usually about the *cluster's assigned label* matching the taxonomy.
        # If the clustering algorithm didn't assign a label, we might use the centroid tag.
        
        # Let's assume the "label" of the cluster is the most frequent tag in it (or the first one).
        representative_tag = cluster[0] if cluster else ""
        
        if fuzzy_match_tags(representative_tag, taxonomy_labels, max_distance):
            matched_count += 1
        else:
            # Try other tags in the cluster as potential labels
            found = False
            for tag in cluster:
                if fuzzy_match_tags(tag, taxonomy_labels, max_distance):
                    found = True
                    break
            if found:
                matched_count += 1

    return matched_count / total_clusters if total_clusters > 0 else 0.0

def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def build_cooccurrence_matrix(posts_data: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """Build a co-occurrence map: tag -> set of tags that appear with it."""
    cooccur_map = defaultdict(set)
    for post in posts_data:
        tags = post.get("tags", [])
        if len(tags) < 2:
            continue
        for i, tag1 in enumerate(tags):
            for tag2 in tags[i+1:]:
                cooccur_map[tag1].add(tag2)
                cooccur_map[tag2].add(tag1)
    return cooccur_map

def compute_jaccard_similarity_matrix(cooccur_map: Dict[str, Set[str]], all_tags: List[str]) -> Dict[str, Dict[str, float]]:
    """Compute Jaccard similarity matrix for all pairs of tags."""
    matrix = {}
    tag_set = set(all_tags)
    for tag1 in all_tags:
        matrix[tag1] = {}
        set1 = cooccur_map.get(tag1, set())
        for tag2 in all_tags:
            if tag1 == tag2:
                matrix[tag1][tag2] = 1.0
            else:
                set2 = cooccur_map.get(tag2, set())
                matrix[tag1][tag2] = calculate_jaccard_similarity(set1, set2)
    return matrix

def perform_hierarchical_clustering(jaccard_matrix: Dict[str, Dict[str, float]], threshold: float = 0.3) -> List[List[str]]:
    """Perform simple hierarchical clustering based on Jaccard similarity."""
    # Using a simple greedy agglomerative approach for demonstration
    # In a real scenario, scipy.cluster.hierarchy would be used.
    tags = list(jaccard_matrix.keys())
    clusters = [[tag] for tag in tags]
    
    # This is a simplified version. A full implementation would merge closest clusters.
    # For this task, we assume the upstream task (T029) has already produced the clusters
    # and we are just validating them. However, if we need to generate them here:
    
    # Let's assume T029 produces the clusters and we just load them or we use a simple method.
    # Since T029 is "requires T028" and implements the logic, we assume the clusters are available
    # in the processed data or we re-run a simple version if needed.
    # To be safe and self-contained for T030 which requires T029:
    # We will assume the clusters are passed in or loaded.
    # But the function signature here is for the module.
    
    # Let's implement a basic single-linkage clustering to ensure we have clusters if needed.
    # But T029 already does this. So we might just return the input if it was processed.
    # For the sake of this task being a "logic implementation", we assume we are calculating the score
    # on the result of T029.
    
    return clusters # Placeholder, actual clusters come from T029's output

def perform_permutation_test(clusters: List[List[str]], jaccard_matrix: Dict[str, Dict[str, float]], n_iterations: int = 1000) -> Tuple[float, float]:
    """Perform permutation test for cluster coherence."""
    # This is a placeholder. T029 implements this.
    return 0.0, 0.0

def run_clustering_pipeline(data_path: str, taxonomy_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full clustering pipeline including alignment score calculation.
    This function is called by main to orchestrate the process.
    """
    # Load processed data (should contain clusters from T029)
    # The processed data from T029 should contain the clusters and the jaccard matrix
    processed_data = load_processed_data(data_path)
    
    # Load taxonomy
    taxonomy = load_taxonomy(taxonomy_path)
    
    clusters = processed_data.get("clusters", [])
    jaccard_matrix = processed_data.get("jaccard_matrix", {})
    
    if not clusters:
        raise ValueError("No clusters found in processed data. Ensure T029 has run.")
    
    # Calculate intra-cluster similarity
    intra_cluster_sims = []
    for cluster in clusters:
        sim = calculate_intra_cluster_similarity(cluster, jaccard_matrix)
        intra_cluster_sims.append(sim)
    
    avg_intra_cluster_sim = sum(intra_cluster_sims) / len(intra_cluster_sims) if intra_cluster_sims else 0.0
    
    # Calculate Cluster Label Alignment Score
    alignment_score = calculate_cluster_label_alignment_score(clusters, taxonomy)
    
    result = {
        "cluster_label_alignment_score": alignment_score,
        "average_intra_cluster_similarity": avg_intra_cluster_sim,
        "num_clusters": len(clusters),
        "threshold_used": 0.3, # Example threshold
        "status": "completed"
    }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    """Main entry point for the clustering alignment task."""
    # Paths relative to project root
    base_path = Path(__file__).resolve().parent.parent.parent
    processed_data_path = base_path / "data" / "processed" / "clustering_intermediate.json" # Assuming T029 output
    taxonomy_path = base_path / "data" / "taxonomy" / "survey_2023.json"
    output_path = base_path / "data" / "processed" / "cluster_alignment.json"
    
    # Check if T029 output exists
    if not processed_data_path.exists():
        print(f"Error: Processed data file not found at {processed_data_path}. Run T029 first.")
        return
    
    # Check if taxonomy exists
    if not taxonomy_path.exists():
        print(f"Error: Taxonomy file not found at {taxonomy_path}. Run T007 first.")
        return
    
    try:
        result = run_clustering_pipeline(str(processed_data_path), str(taxonomy_path), str(output_path))
        print(f"Cluster Label Alignment Score: {result['cluster_label_alignment_score']:.4f}")
        print(f"Average Intra-Cluster Similarity: {result['average_intra_cluster_similarity']:.4f}")
        print(f"Results saved to {output_path}")
        
        # Verify score >= 0.8 as per requirement (though it might not be in reality)
        if result['cluster_label_alignment_score'] < 0.8:
            print(f"Warning: Alignment score ({result['cluster_label_alignment_score']:.4f}) is below the 0.8 threshold.")
        else:
            print("Alignment score meets the 0.8 threshold.")
            
    except Exception as e:
        print(f"Error during clustering alignment analysis: {e}")
        raise

if __name__ == "__main__":
    main()
