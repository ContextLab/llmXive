import json
import os
import time
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# --- Helper Functions ---

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    Returns the minimum number of single-character edits (insertions, deletions, or substitutions)
    required to change one word into the other.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Calculate costs for insertions, deletions, and substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def fuzzy_match_tags(tag1: str, tag2: str, max_distance: int = 2) -> bool:
    """
    Check if two tags are fuzzy matches based on Levenshtein distance.
    Returns True if the distance is less than or equal to max_distance.
    """
    return levenshtein_distance(tag1.lower(), tag2.lower()) <= max_distance

def load_processed_data(project_root: Path) -> Dict[str, Any]:
    """
    Load the processed data from the clustering pipeline output.
    Expects `data/processed/clustering_intermediate.json` containing clusters and tag lists.
    """
    file_path = project_root / "data" / "processed" / "clustering_intermediate.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_taxonomy(project_root: Path) -> Dict[str, Any]:
    """
    Load the Stack Overflow survey taxonomy from the generated file.
    Expects `data/taxonomy/survey_2023.json`.
    """
    file_path = project_root / "data" / "taxonomy" / "survey_2023.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {file_path}. "
                                "Please ensure T007 (generate_taxonomies) has been completed successfully.")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_intra_cluster_similarity(clusters: List[List[str]]) -> float:
    """
    Calculate the average intra-cluster similarity coefficient.
    For each cluster, calculates the average Jaccard similarity (or simple overlap ratio)
    between all pairs of tags in the cluster.
    """
    if not clusters or len(clusters) == 0:
        return 0.0
    
    total_similarity = 0.0
    count_pairs = 0
    
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                tag1, tag2 = cluster[i], cluster[j]
                # Simple similarity: 1 if identical, else 0 (or could use Jaccard if more complex)
                # Using exact match for simplicity in intra-cluster check, 
                # but fuzzy matching could be applied here if needed.
                # For this metric, we'll assume exact string match is the baseline for "perfect" intra-cluster.
                # However, to be robust, let's use a normalized overlap if we had sets, 
                # but here we have tags. Let's define similarity as 1.0 if fuzzy match, 0.0 otherwise.
                sim = 1.0 if fuzzy_match_tags(tag1, tag2) else 0.0
                total_similarity += sim
                count_pairs += 1
    
    if count_pairs == 0:
        return 0.0
    
    return total_similarity / count_pairs

def calculate_cluster_label_alignment_score(clusters: List[List[str]], 
                                            taxonomy: Dict[str, Any], 
                                            fuzzy_threshold: int = 2) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Calculate the Cluster Label Alignment Score using fuzzy matching (Levenshtein distance <= 2)
    against the Stack Overflow survey taxonomy.
    
    Returns:
        Tuple of (alignment_score, detailed_alignment_report)
    """
    if not clusters:
        return 0.0, []
    
    # Extract survey categories and their associated tags from taxonomy
    # The taxonomy structure from T007 is expected to be a list of categories,
    # each with a 'category' name and 'tags' list.
    survey_categories = []
    if isinstance(taxonomy, list):
        for item in taxonomy:
            if 'category' in item and 'tags' in item:
                survey_categories.append({
                    'name': item['category'],
                    'tags': set([t.lower().strip() for t in item['tags']])
                })
    elif isinstance(taxonomy, dict) and 'categories' in taxonomy:
        for item in taxonomy['categories']:
            if 'category' in item and 'tags' in item:
                survey_categories.append({
                    'name': item['category'],
                    'tags': set([t.lower().strip() for t in item['tags']])
                })
    
    if not survey_categories:
        # Fallback if structure is different but data exists
        # Assume taxonomy is a dict of category_name -> list of tags
        for name, tags in taxonomy.items():
            if isinstance(tags, list):
                survey_categories.append({
                    'name': name,
                    'tags': set([t.lower().strip() for t in tags])
                })

    aligned_count = 0
    total_tags_in_clusters = 0
    alignment_details = []

    for cluster_idx, cluster in enumerate(clusters):
        cluster_tags = [t.lower().strip() for t in cluster]
        total_tags_in_clusters += len(cluster_tags)
        
        best_match_category = None
        best_match_score = 0.0
        matched_tags = []

        # Check alignment with each survey category
        for survey_cat in survey_categories:
            # Calculate how many tags in this cluster fuzzy match tags in the survey category
            current_matches = 0
            for tag in cluster_tags:
                for survey_tag in survey_cat['tags']:
                    if fuzzy_match_tags(tag, survey_tag, fuzzy_threshold):
                        current_matches += 1
                        break # Match found for this tag, move to next tag
            
            # Score for this category: fraction of cluster tags that match
            score = current_matches / len(cluster_tags) if len(cluster_tags) > 0 else 0
            
            if score > best_match_score:
                best_match_score = score
                best_match_category = survey_cat['name']
                # Re-calculate matched tags for the best category
                matched_tags = [t for t in cluster_tags if any(fuzzy_match_tags(t, st, fuzzy_threshold) for st in survey_cat['tags'])]

        if best_match_score > 0:
            aligned_count += len(cluster_tags) # All tags in a "aligned" cluster count? 
            # Actually, let's count the number of tags that found a match.
            # The logic above: if a cluster has ANY match, we consider it aligned?
            # Better definition: Alignment Score = (Number of tags in clusters that match a survey category) / (Total tags in clusters)
            # But the task asks for "Cluster Label Alignment Score", implying cluster-level alignment.
            # Let's interpret as: For each cluster, if it aligns with a category (score > 0), 
            # then the tags contributing to that alignment count.
            
            # Refined logic: Count tags that successfully matched a category.
            for tag in cluster_tags:
                if any(fuzzy_match_tags(tag, st, fuzzy_threshold) for st in (survey_categories[0]['tags'] if survey_categories else [])):
                   # This loop is inefficient, re-do properly:
                   pass
        
        # Re-evaluating the score calculation for the final metric
        # We will count how many tags in the cluster have a fuzzy match to ANY tag in ANY survey category.
        cluster_aligned_tags = 0
        for tag in cluster_tags:
            for survey_cat in survey_categories:
                if any(fuzzy_match_tags(tag, st, fuzzy_threshold) for st in survey_cat['tags']):
                    cluster_aligned_tags += 1
                    break # Found a match for this tag
        
        aligned_count += cluster_aligned_tags
        
        alignment_details.append({
            "cluster_index": cluster_idx,
            "cluster_size": len(cluster_tags),
            "aligned_tags_count": cluster_aligned_tags,
            "best_matching_category": best_match_category,
            "alignment_score_cluster": cluster_aligned_tags / len(cluster_tags) if len(cluster_tags) > 0 else 0.0
        })

    overall_score = aligned_count / total_tags_in_clusters if total_tags_in_clusters > 0 else 0.0
    return overall_score, alignment_details

def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def build_cooccurrence_matrix(posts_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Build a co-occurrence matrix from posts data.
    Returns a dictionary of dictionaries: {tag1: {tag2: count}}
    """
    cooccurrence = {}
    for post in posts_data:
        tags = post.get('tags', [])
        if not tags:
            continue
        # Normalize tags
        normalized_tags = [t.lower().strip() for t in tags]
        unique_tags = list(set(normalized_tags))
        
        for i, tag1 in enumerate(unique_tags):
            if tag1 not in cooccurrence:
                cooccurrence[tag1] = {}
            for j, tag2 in enumerate(unique_tags):
                if i == j:
                    continue
                if tag2 not in cooccurrence[tag1]:
                    cooccurrence[tag1][tag2] = 0
                cooccurrence[tag1][tag2] += 1
    return cooccurrence

def compute_jaccard_similarity_matrix(cooccurrence: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, float]]:
    """
    Compute Jaccard similarity matrix from cooccurrence counts.
    Jaccard(A, B) = |A intersection B| / |A union B|
    Here, we approximate union using cooccurrence + individual frequencies if available.
    For simplicity in this context, we use the cooccurrence count as intersection.
    Union is harder to get without individual post counts per tag.
    Assumption: We have individual tag frequencies in the data or we approximate.
    Since T028 (Jaccard) is done, we assume we can derive or use the counts.
    However, for this specific task, we focus on the alignment score.
    """
    # This function is a placeholder for the matrix computation logic
    # which is already implemented in T028/T029.
    # We return an empty dict or a simplified version if needed for downstream.
    # For T030, we primarily need the clusters from the intermediate file.
    return {}

def perform_hierarchical_clustering(jaccard_matrix: Dict[str, Dict[str, float]], 
                                    threshold: float = 0.5) -> List[List[str]]:
    """
    Perform hierarchical clustering based on Jaccard similarity.
    Returns a list of clusters (lists of tags).
    """
    # Placeholder: The actual clustering logic is assumed to be in T029.
    # We expect the clusters to be loaded from the intermediate file.
    return []

def perform_permutation_test(clusters: List[List[str]], 
                             jaccard_matrix: Dict[str, Dict[str, float]], 
                             n_iterations: int = 1000) -> Dict[str, Any]:
    """
    Perform a permutation test to validate cluster coherence.
    """
    # Placeholder: Logic from T029.
    return {"p_value": 0.0, "is_significant": False}

def run_clustering_pipeline(project_root: Path) -> Dict[str, Any]:
    """
    Run the full clustering pipeline, including the new Cluster Label Alignment Score.
    """
    # Load data
    data = load_processed_data(project_root)
    taxonomy = load_taxonomy(project_root)
    
    clusters = data.get('clusters', [])
    
    # Calculate alignment score
    alignment_score, details = calculate_cluster_label_alignment_score(clusters, taxonomy)
    
    # Calculate intra-cluster similarity
    intra_sim = calculate_intra_cluster_similarity(clusters)
    
    result = {
        "cluster_label_alignment_score": alignment_score,
        "intra_cluster_similarity": intra_sim,
        "alignment_details": details,
        "taxonomy_source": "data/taxonomy/survey_2023.json",
        "fuzzy_threshold": 2
    }
    
    return result

def main():
    """Main entry point for the clustering analysis script."""
    project_root = Path(__file__).resolve().parent.parent.parent
    print(f"Running clustering analysis with alignment score calculation on {project_root}...")
    
    try:
        result = run_clustering_pipeline(project_root)
        
        # Save results to intermediate file for T032 to aggregate
        output_path = project_root / "data" / "processed" / "clustering_alignment.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        print(f"Cluster Label Alignment Score: {result['cluster_label_alignment_score']:.4f}")
        print(f"Intra-cluster Similarity: {result['intra_cluster_similarity']:.4f}")
        print(f"Results saved to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"An error occurred during clustering analysis: {e}")
        raise

if __name__ == "__main__":
    main()