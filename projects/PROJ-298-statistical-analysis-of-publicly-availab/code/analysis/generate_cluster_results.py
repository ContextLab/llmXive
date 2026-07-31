import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums
from analysis.clustering import load_processed_data, load_taxonomy, calculate_cluster_label_alignment_score, perform_hierarchical_clustering

def load_json_safe(file_path: Path) -> Optional[Dict]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None

def calculate_intra_cluster_similarity(clusters: Dict[str, list], similarity_matrix: Dict[str, Dict[str, float]]) -> float:
    """
    Calculate the average intra-cluster similarity coefficient.
    Returns the mean similarity of all pairs within the same cluster.
    """
    if not clusters or not similarity_matrix:
        return 0.0

    total_similarity = 0.0
    pair_count = 0

    for cluster_name, tags in clusters.items():
        if len(tags) < 2:
            continue
        
        # Compare every pair in the cluster
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                tag_a = tags[i]
                tag_b = tags[j]
                
                # Retrieve similarity (handle potential missing keys gracefully)
                sim = 0.0
                if tag_a in similarity_matrix and tag_b in similarity_matrix[tag_a]:
                    sim = similarity_matrix[tag_a][tag_b]
                elif tag_b in similarity_matrix and tag_a in similarity_matrix[tag_b]:
                    sim = similarity_matrix[tag_b][tag_a]
                
                total_similarity += sim
                pair_count += 1

    if pair_count == 0:
        return 0.0
    
    return total_similarity / pair_count

def aggregate_cluster_results(clustering_results: Dict, taxonomy: Dict, similarity_matrix: Dict) -> Dict:
    """
    Aggregate clustering results, calculate alignment scores, and intra-cluster similarity.
    """
    if not clustering_results:
        return {}

    # Extract clusters from the hierarchical clustering result
    # Assuming structure: {'clusters': {cluster_name: [tag1, tag2, ...]}}
    clusters = clustering_results.get('clusters', {})
    
    # Calculate Cluster Label Alignment Score
    alignment_score = calculate_cluster_label_alignment_score(clusters, taxonomy)
    
    # Calculate Intra-cluster Similarity Coefficient
    intra_cluster_sim = calculate_intra_cluster_similarity(clusters, similarity_matrix)

    # Construct the final result object
    result = {
        "clusters": clusters,
        "cluster_label_alignment_score": alignment_score,
        "intra_cluster_similarity_coefficient": intra_cluster_sim,
        "metadata": {
            "num_clusters": len(clusters),
            "total_tags_clustered": sum(len(tags) for tags in clusters.values()),
            "taxonomy_source": "survey_2023.json"
        }
    }

    return result

def main():
    """
    Main entry point for T032: Generate cluster_results.json, calculate SHA-256, and update state.
    """
    # Define paths relative to project root
    data_dir = PROJECT_ROOT / "data"
    processed_dir = data_dir / "processed"
    taxonomy_dir = data_dir / "taxonomy"
    
    # Input files
    clustering_results_path = processed_dir / "clustering_results.json"
    taxonomy_path = taxonomy_dir / "survey_2023.json"
    
    # Output file
    output_path = processed_dir / "cluster_results.json"
    state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

    print(f"Loading clustering results from {clustering_results_path}...")
    clustering_data = load_json_safe(clustering_results_path)
    
    if not clustering_data:
        print("Error: Clustering results not found. Please run T029 first.")
        sys.exit(1)

    print(f"Loading taxonomy from {taxonomy_path}...")
    taxonomy_data = load_json_safe(taxonomy_path)
    
    if not taxonomy_data:
        print("Error: Taxonomy file not found. Please run T007 first.")
        sys.exit(1)

    # Extract similarity matrix from clustering results if available, otherwise re-calculate or load
    # Assuming clustering_results.json contains the matrix or we load it from a separate file
    # For this task, we assume clustering_results.json has the matrix under 'similarity_matrix'
    similarity_matrix = clustering_data.get('similarity_matrix', {})
    
    if not similarity_matrix:
        # Fallback: try to load from a separate file if the main result didn't have it
        sim_matrix_path = processed_dir / "jaccard_similarity_matrix.json"
        sim_matrix_data = load_json_safe(sim_matrix_path)
        if sim_matrix_data:
            similarity_matrix = sim_matrix_data
        else:
            print("Warning: Similarity matrix not found in clustering results or separate file. Alignment score may be inaccurate.")

    print("Aggregating cluster results...")
    final_results = aggregate_cluster_results(clustering_data, taxonomy_data, similarity_matrix)

    # Write the output file
    print(f"Writing results to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)

    # Calculate SHA-256 hash
    print("Calculating SHA-256 hash...")
    file_hash = calculate_sha256(output_path)
    print(f"Hash for cluster_results.json: {file_hash}")

    # Update state file
    print(f"Updating state file at {state_path}...")
    try:
        state = load_state(state_path)
        update_artifact_checksums(state, "cluster_results.json", file_hash)
        save_state(state_path, state)
        print("State file updated successfully.")
    except Exception as e:
        print(f"Warning: Could not update state file: {e}")

    print("T032 completed successfully.")

if __name__ == "__main__":
    main()