"""
MinHash-LSH implementation for near-duplicate detection.
Groups near-duplicate passages with Jaccard similarity > threshold.
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from datasketch import MinHash, MinHashLSH
from data_loader import load_injected_dataset, RedundancyCluster
from config import get_config, format_bytes
from logging_config import init_logging, log_pairwise_comparison

logger = init_logging(__name__)


@dataclass
class MinHashCluster:
    """Represents a cluster of near-duplicate documents."""
    cluster_id: int
    representative_id: str
    member_ids: List[str]
    member_texts: List[str]
    avg_jaccard: float
    size: int


def create_minhash(text: str, num_perm: int = 128) -> MinHash:
    """
    Create a MinHash signature for a given text.
    Uses character n-grams (shingles) for text representation.
    """
    if not text:
        text = ""
    
    # Use character 5-grams as shingles
    shingles = set()
    n = 5
    if len(text) >= n:
        for i in range(len(text) - n + 1):
            shingles.add(text[i:i+n])
    else:
        # For very short texts, use the whole text as a single shingle
        shingles.add(text)
    
    m = MinHash(num_perm=num_perm)
    for shingle in shingles:
        m.update(shingle.encode('utf8'))
    
    return m


def estimate_jaccard(m1: MinHash, m2: MinHash) -> float:
    """Estimate Jaccard similarity between two MinHash signatures."""
    return m1.jaccard(m2)


def cluster_documents(
    documents: List[Dict[str, Any]],
    threshold: float = 0.95,
    num_perm: int = 128,
    num_bands: int = None,
    num_rows: int = None
) -> List[MinHashCluster]:
    """
    Cluster documents using MinHash-LSH.
    
    Args:
        documents: List of dicts with 'id' and 'text' keys
        threshold: Jaccard similarity threshold (0.0 to 1.0)
        num_perm: Number of permutations for MinHash
        num_bands: Number of bands for LSH (auto-calculated if None)
        num_rows: Number of rows per band (auto-calculated if None)
    
    Returns:
        List of MinHashCluster objects representing near-duplicate groups
    """
    if not documents:
        return []
    
    # Auto-calculate bands and rows if not provided
    if num_bands is None or num_rows is None:
        # Standard formula: threshold = (1/b)^(1/r) where b=bands, r=rows
        # For threshold=0.95, we want high precision
        if num_perm is None:
            num_perm = 128
        num_rows = max(1, int(num_perm * 0.5))  # Use half for rows
        num_bands = max(1, num_perm // num_rows)
    
    logger.info(f"Creating MinHash-LSH with threshold={threshold}, "
               f"num_perm={num_perm}, num_bands={num_bands}, num_rows={num_rows}")
    
    # Create LSH index
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    
    # Create MinHash signatures for all documents
    minhashes: Dict[str, MinHash] = {}
    for doc in documents:
        doc_id = doc['id']
        text = doc.get('text', doc.get('body', ''))
        minhashes[doc_id] = create_minhash(text, num_perm)
    
    # Insert into LSH
    for doc_id, minhash in minhashes.items():
        lsh.insert(doc_id, minhash)
    
    # Query for clusters
    clusters: Dict[int, Set[str]] = {}
    cluster_id = 0
    processed: Set[str] = set()
    
    for doc_id in minhashes.keys():
        if doc_id in processed:
            continue
        
        # Get candidates from LSH
        candidates = lsh.query(minhashes[doc_id])
        
        # Filter candidates by actual Jaccard similarity
        actual_cluster = {doc_id}
        for candidate_id in candidates:
            if candidate_id != doc_id and candidate_id not in processed:
                jaccard = estimate_jaccard(minhashes[doc_id], minhashes[candidate_id])
                if jaccard >= threshold:
                    actual_cluster.add(candidate_id)
        
        if len(actual_cluster) > 1:
            clusters[cluster_id] = actual_cluster
            cluster_id += 1
            processed.update(actual_cluster)
        else:
            processed.add(doc_id)
    
    # Convert to MinHashCluster objects
    result_clusters = []
    for cid, member_ids in clusters.items():
        member_docs = [doc for doc in documents if doc['id'] in member_ids]
        member_texts = [doc.get('text', doc.get('body', '')) for doc in member_docs]
        
        # Calculate average pairwise Jaccard within cluster
        if len(member_docs) > 1:
            jaccard_sum = 0.0
            pair_count = 0
            member_minhashes = [minhashes[doc['id']] for doc in member_docs]
            for i in range(len(member_minhashes)):
                for j in range(i + 1, len(member_minhashes)):
                    jaccard_sum += estimate_jaccard(member_minhashes[i], member_minhashes[j])
                    pair_count += 1
            avg_jaccard = jaccard_sum / pair_count if pair_count > 0 else 0.0
        else:
            avg_jaccard = 1.0
        
        result_clusters.append(MinHashCluster(
            cluster_id=cid,
            representative_id=member_docs[0]['id'],
            member_ids=list(member_ids),
            member_texts=member_texts,
            avg_jaccard=avg_jaccard,
            size=len(member_ids)
        ))
    
    logger.info(f"Found {len(result_clusters)} near-duplicate clusters with "
               f"Jaccard >= {threshold}")
    
    return result_clusters


def filter_candidates_by_clustering(
    documents: List[Dict[str, Any]],
    threshold: float = 0.95,
    num_perm: int = 128
) -> Tuple[List[Dict[str, Any]], List[MinHashCluster]]:
    """
    Filter a candidate list by removing near-duplicates using MinHash-LSH.
    Keeps only the representative from each cluster.
    
    Args:
        documents: List of document dicts
        threshold: Jaccard similarity threshold
        num_perm: Number of permutations for MinHash
    
    Returns:
        Tuple of (filtered_documents, clusters)
    """
    if not documents:
        return [], []
    
    clusters = cluster_documents(documents, threshold, num_perm)
    
    # Keep only representatives
    kept_ids = {cluster.representative_id for cluster in clusters}
    
    # For documents not in any cluster, keep them
    all_doc_ids = {doc['id'] for doc in documents}
    unique_ids = all_doc_ids - kept_ids
    
    filtered_docs = [doc for doc in documents 
                   if doc['id'] in kept_ids or doc['id'] in unique_ids]
    
    # Ensure we keep the representative
    kept_docs = [doc for doc in filtered_docs if doc['id'] in kept_ids]
    unique_docs = [doc for doc in filtered_docs if doc['id'] in unique_ids]
    
    # Deduplicate: if a doc is in a cluster, only keep the representative
    final_docs = unique_docs.copy()
    for cluster in clusters:
        final_docs.append(next(doc for doc in documents if doc['id'] == cluster.representative_id))
    
    reduction_ratio = 1.0 - (len(final_docs) / len(documents)) if documents else 0.0
    logger.info(f"Clustering reduced {len(documents)} docs to {len(final_docs)} "
               f"(reduction: {reduction_ratio:.2%})")
    
    return final_docs, clusters


def run_clustering_pipeline(
    dataset_name: str = "nfcorpus",
    threshold: float = 0.95,
    output_dir: str = "data/results"
) -> Dict[str, Any]:
    """
    Run the full clustering pipeline on a dataset.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'nfcorpus', 'scifact')
        threshold: Jaccard similarity threshold
        output_dir: Directory to save results
    
    Returns:
        Dictionary with clustering results and statistics
    """
    config = get_config()
    os.makedirs(output_dir, exist_ok=True)
    
    # Load dataset (assuming injected dataset exists from T012)
    try:
        data_path = os.path.join("data", f"{dataset_name}_injected.json")
        if os.path.exists(data_path):
            documents = load_injected_dataset(data_path)
        else:
            # Fallback to loading from BEIR
            from data_loader import load_beir_corpus
            documents = load_beir_corpus(dataset_name)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    logger.info(f"Loaded {len(documents)} documents from {dataset_name}")
    
    # Run clustering
    clusters = cluster_documents(documents, threshold=threshold)
    
    # Calculate statistics
    total_docs = len(documents)
    clustered_docs = sum(len(c.member_ids) for c in clusters)
    unique_docs = total_docs - clustered_docs + len(clusters)
    reduction_ratio = (total_docs - unique_docs) / total_docs if total_docs > 0 else 0.0
    
    # Save results
    results = {
        "dataset": dataset_name,
        "threshold": threshold,
        "total_documents": total_docs,
        "num_clusters": len(clusters),
        "clustered_documents": clustered_docs,
        "unique_documents": unique_docs,
        "reduction_ratio": reduction_ratio,
        "clusters": [asdict(c) for c in clusters]
    }
    
    output_path = os.path.join(output_dir, f"{dataset_name}_clustering_{threshold}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved clustering results to {output_path}")
    
    return results


def main():
    """Main entry point for clustering script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MinHash-LSH clustering")
    parser.add_argument("--dataset", default="nfcorpus", help="Dataset name")
    parser.add_argument("--threshold", type=float, default=0.95, help="Jaccard threshold")
    parser.add_argument("--num_perm", type=int, default=128, help="Number of permutations")
    parser.add_argument("--output_dir", default="data/results", help="Output directory")
    
    args = parser.parse_args()
    
    results = run_clustering_pipeline(
        dataset_name=args.dataset,
        threshold=args.threshold,
        output_dir=args.output_dir
    )
    
    print(f"Clustering complete: {results['num_clusters']} clusters found, "
          f"{results['reduction_ratio']:.2%} reduction")


if __name__ == "__main__":
    main()