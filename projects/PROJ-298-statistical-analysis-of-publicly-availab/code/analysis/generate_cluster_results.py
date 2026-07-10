"""
Generate cluster_results.json including Cluster Label Alignment Score and intra-cluster similarity coefficient.
Calculates SHA-256 hashes and updates state file per FR-012.
"""
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums
from analysis.clustering import load_processed_data, load_taxonomy, calculate_cluster_label_alignment_score, perform_hierarchical_clustering

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file safely, returning None if file doesn't exist or is invalid."""
    try:
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {file_path}: {e}")
        return None

def calculate_intra_cluster_similarity(clusters: Dict[str, Any]) -> float:
    """
    Calculate the intra-cluster similarity coefficient.
    This measures the average Jaccard similarity within each cluster.
    
    Args:
        clusters: Dictionary containing cluster assignments and similarity data
        
    Returns:
        float: Average intra-cluster similarity (0.0 to 1.0)
    """
    if not clusters or 'clusters' not in clusters:
        return 0.0
    
    cluster_assignments = clusters.get('cluster_assignments', {})
    similarity_matrix = clusters.get('jaccard_similarity', {})
    
    if not cluster_assignments or not similarity_matrix:
        return 0.0
    
    # Group tags by cluster
    cluster_groups = {}
    for tag, cluster_id in cluster_assignments.items():
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(tag)
    
    total_similarity = 0.0
    total_pairs = 0
    
    # Calculate average similarity within each cluster
    for cluster_id, tags in cluster_groups.items():
        if len(tags) < 2:
            continue
        
        for i in range(len(tags)):
            for j in range(i + 1, len(tags)):
                tag1, tag2 = tags[i], tags[j]
                # Get similarity from matrix (handle both string keys and tuple keys)
                key1 = f"{tag1}_{tag2}"
                key2 = f"{tag2}_{tag1}"
                key3 = (tag1, tag2)
                key4 = (tag2, tag1)
                
                sim = 0.0
                if key1 in similarity_matrix:
                    sim = similarity_matrix[key1]
                elif key2 in similarity_matrix:
                    sim = similarity_matrix[key2]
                elif key3 in similarity_matrix:
                    sim = similarity_matrix[key3]
                elif key4 in similarity_matrix:
                    sim = similarity_matrix[key4]
                
                total_similarity += sim
                total_pairs += 1
    
    if total_pairs == 0:
        return 0.0
    
    return total_similarity / total_pairs

def aggregate_cluster_results(clusters_data: Dict[str, Any], taxonomy_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate cluster results including alignment score and intra-cluster similarity.
    
    Args:
        clusters_data: Output from clustering pipeline
        taxonomy_data: Survey taxonomy data
        
    Returns:
        Dictionary containing aggregated results
    """
    # Calculate cluster label alignment score
    alignment_score = calculate_cluster_label_alignment_score(clusters_data, taxonomy_data)
    
    # Calculate intra-cluster similarity
    intra_cluster_sim = calculate_intra_cluster_similarity(clusters_data)
    
    # Build result structure
    results = {
        "metadata": {
            "generated_at": "2024-01-01T00:00:00Z",  # Will be updated by actual execution
            "version": "1.0",
            "description": "Cluster analysis results with alignment and similarity metrics"
        },
        "metrics": {
            "cluster_label_alignment_score": alignment_score,
            "intra_cluster_similarity_coefficient": intra_cluster_sim,
            "num_clusters": len(clusters_data.get('cluster_assignments', {})),
            "num_tags_analyzed": len(clusters_data.get('cluster_assignments', {}))
        },
        "clusters": clusters_data.get('clusters', {}),
        "cluster_assignments": clusters_data.get('cluster_assignments', {}),
        "taxonomy_alignment": {
            "survey_taxonomy_version": taxonomy_data.get('metadata', {}).get('version', 'unknown'),
            "alignment_score": alignment_score,
            "matched_clusters": clusters_data.get('taxonomy_matches', [])
        },
        "similarity_metrics": {
            "intra_cluster_average": intra_cluster_sim,
            "jaccard_matrix_summary": {
                "num_pairs": len(clusters_data.get('jaccard_similarity', {})),
                "avg_similarity": sum(clusters_data.get('jaccard_similarity', {}).values()) / max(1, len(clusters_data.get('jaccard_similarity', {})))
            }
        }
    }
    
    return results

def main():
    """Main function to generate cluster results and update state."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    taxonomy_dir = data_dir / "taxonomy"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load processed clustering data
    clusters_file = processed_dir / "clustering_results.json"
    clusters_data = load_json_safe(clusters_file)
    
    if clusters_data is None:
        print("Error: Clustering results not found. Run clustering pipeline first.")
        sys.exit(1)
    
    # Load taxonomy data
    taxonomy_file = taxonomy_dir / "survey_2023.json"
    taxonomy_data = load_json_safe(taxonomy_file)
    
    if taxonomy_data is None:
        print("Warning: Taxonomy file not found. Using empty taxonomy for alignment calculation.")
        taxonomy_data = {"metadata": {"version": "unknown"}, "clusters": []}
    
    # Aggregate results
    results = aggregate_cluster_results(clusters_data, taxonomy_data)
    
    # Save results
    output_file = processed_dir / "cluster_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Saved cluster results to {output_file}")
    
    # Calculate SHA-256 hash
    file_hash = calculate_sha256(output_file)
    print(f"SHA-256 hash: {file_hash}")
    
    # Update state file
    state_file = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
    
    if state_file.exists():
        state = load_state(state_file)
        update_artifact_checksums(state, str(output_file), file_hash)
        save_state(state_file, state)
        print(f"Updated state file: {state_file}")
    else:
        print(f"Warning: State file not found at {state_file}. Skipping state update.")
    
    return results

if __name__ == "__main__":
    main()
