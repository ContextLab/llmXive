import os
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from data_loader import load_injected_dataset, RedundancyCluster
from models import CandidateList
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class UniqueSubsetResult:
    """Result of generating the unique subset from a redundant candidate list."""
    total_original_items: int
    total_unique_items: int
    removed_duplicates: int
    removal_percentage: float
    unique_indices: List[int]
    output_path: str

def identify_unique_representatives(clusters: List[RedundancyCluster]) -> Tuple[Dict[int, int], List[int]]:
    """
    Identifies the unique representative for each redundancy cluster.
    
    Args:
        clusters: List of RedundancyCluster objects containing indices of near-duplicates.
    
    Returns:
        A tuple containing:
        - A dict mapping original index -> representative index (for items in clusters)
        - A list of indices that are unique representatives (one per cluster)
    """
    representative_map = {}
    unique_indices = []

    for cluster in clusters:
        if not cluster.indices or len(cluster.indices) == 0:
            continue
        
        # Select the first item in the cluster as the representative
        # This is a deterministic choice; could be random or based on score if available
        representative_idx = cluster.indices[0]
        unique_indices.append(representative_idx)
        
        # Map all other items in the cluster to this representative
        for idx in cluster.indices:
            representative_map[idx] = representative_idx

    return representative_map, unique_indices

def filter_to_unique_subset(candidate_list: CandidateList, clusters: List[RedundancyCluster]) -> CandidateList:
    """
    Filters the candidate list to remove near-duplicates, keeping only unique representatives.
    
    Args:
        candidate_list: The original CandidateList with redundant items.
        clusters: List of RedundancyCluster objects identifying near-duplicate groups.
    
    Returns:
        A new CandidateList containing only the unique representatives.
    """
    _, unique_indices = identify_unique_representatives(clusters)
    
    # Sort indices to maintain original order
    unique_indices.sort()
    
    filtered_docs = [candidate_list.documents[i] for i in unique_indices]
    filtered_scores = [candidate_list.scores[i] for i in unique_indices] if candidate_list.scores else None
    filtered_query_ids = [candidate_list.query_ids[i] for i in unique_indices] if candidate_list.query_ids else None
    
    return CandidateList(
        documents=filtered_docs,
        scores=filtered_scores,
        query_ids=filtered_query_ids,
        original_indices=unique_indices
    )

def generate_unique_subset(
    dataset_path: str,
    clusters_path: str,
    output_path: str,
    force_overwrite: bool = False
) -> UniqueSubsetResult:
    """
    Main function to generate the unique subset from an injected dataset.
    
    Args:
        dataset_path: Path to the JSON file containing the injected dataset with clusters.
        clusters_path: Path to the JSON file containing the redundancy clusters.
        output_path: Path where the unique subset will be saved.
        force_overwrite: Whether to overwrite existing output file.
    
    Returns:
        UniqueSubsetResult containing statistics and output path.
    """
    logger.info(f"Loading injected dataset from {dataset_path}")
    dataset = load_injected_dataset(dataset_path)
    
    logger.info(f"Loading redundancy clusters from {clusters_path}")
    with open(clusters_path, 'r', encoding='utf-8') as f:
        clusters_data = json.load(f)
    
    clusters = [RedundancyCluster(**cluster_dict) for cluster_dict in clusters_data]
    
    total_original = len(dataset.documents)
    logger.info(f"Total original items: {total_original}")
    logger.info(f"Number of redundancy clusters: {len(clusters)}")
    
    # Generate unique subset
    unique_subset = filter_to_unique_subset(dataset, clusters)
    total_unique = len(unique_subset.documents)
    
    removed_duplicates = total_original - total_unique
    removal_percentage = (removed_duplicates / total_original * 100) if total_original > 0 else 0.0
    
    logger.info(f"Total unique items: {total_unique}")
    logger.info(f"Removed duplicates: {removed_duplicates}")
    logger.info(f"Removal percentage: {removal_percentage:.2f}%")
    
    # Save output
    if os.path.exists(output_path) and not force_overwrite:
        raise FileExistsError(f"Output file {output_path} already exists. Set force_overwrite=True to overwrite.")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    output_data = {
        "total_original_items": total_original,
        "total_unique_items": total_unique,
        "removed_duplicates": removed_duplicates,
        "removal_percentage": removal_percentage,
        "unique_indices": unique_subset.original_indices or list(range(total_unique)),
        "documents": unique_subset.documents,
        "scores": unique_subset.scores,
        "query_ids": unique_subset.query_ids,
        "cluster_summary": {
            "num_clusters": len(clusters),
            "cluster_sizes": [len(c.indices) for c in clusters]
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Unique subset saved to {output_path}")
    
    return UniqueSubsetResult(
        total_original_items=total_original,
        total_unique_items=total_unique,
        removed_duplicates=removed_duplicates,
        removal_percentage=removal_percentage,
        unique_indices=unique_subset.original_indices or list(range(total_unique)),
        output_path=output_path
    )

def main():
    """CLI entry point for generating the unique subset."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate unique subset from redundant candidate list")
    parser.add_argument("--dataset", type=str, default="data/injected/nfcorpus_injected.json",
                      help="Path to injected dataset JSON")
    parser.add_argument("--clusters", type=str, default="data/injected/redundancy_clusters.json",
                      help="Path to redundancy clusters JSON")
    parser.add_argument("--output", type=str, default="data/unique_subset/nfcorpus_unique.json",
                      help="Path to output unique subset JSON")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing output")
    
    args = parser.parse_args()
    
    try:
        result = generate_unique_subset(
            dataset_path=args.dataset,
            clusters_path=args.clusters,
            output_path=args.output,
            force_overwrite=args.force
        )
        
        print(f"\n=== Unique Subset Generation Complete ===")
        print(f"Original items: {result.total_original_items}")
        print(f"Unique items: {result.total_unique_items}")
        print(f"Removed duplicates: {result.removed_duplicates}")
        print(f"Removal percentage: {result.removal_percentage:.2f}%")
        print(f"Output saved to: {result.output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating unique subset: {e}")
        raise

if __name__ == "__main__":
    main()
