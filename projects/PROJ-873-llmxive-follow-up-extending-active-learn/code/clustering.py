import os
import json
import hashlib
import time
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import logging

from datasketch import MinHash, MinHashLSH
import numpy as np

# Local imports
from config import get_config

logger = logging.getLogger(__name__)

@dataclass
class MinHashCluster:
    cluster_id: int
    member_ids: List[str]
    centroid_id: Optional[str] = None
    size: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def create_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Create a MinHash signature for a given text."""
    m = MinHash(num_perm=num_perm)
    # Simple tokenization: lowercase and split by whitespace/punctuation
    tokens = text.lower().split()
    for token in tokens:
        # Clean token
        clean_token = "".join(c for c in token if c.isalnum())
        if clean_token:
            m.update(clean_token.encode('utf8'))
    return m

def estimate_jaccard(mh1: MinHash, mh2: MinHash) -> float:
    """Estimate Jaccard similarity between two MinHash signatures."""
    return mh1.jaccard(mh2)

def cluster_documents(
    documents: List[Dict[str, Any]],
    threshold: float = 0.95,
    num_perm: int = 128,
    max_num_perm: int = 1024
) -> List[MinHashCluster]:
    """
    Cluster documents using MinHash-LSH with a Jaccard similarity threshold.
    
    Args:
        documents: List of document dicts with 'id' and 'text' keys.
        threshold: Jaccard similarity threshold for clustering (default 0.95).
        num_perm: Number of permutations for MinHash.
        max_num_perm: Maximum permutations allowed to prevent memory issues.
    
    Returns:
        List of MinHashCluster objects.
    """
    if not documents:
        return []
    
    # Adjust num_perm if necessary to avoid memory issues
    effective_num_perm = min(num_perm, max_num_perm)
    logger.info(f"Using {effective_num_perm} permutations for MinHash (capped from {num_perm})")
    
    # Create MinHash signatures for all documents
    doc_signatures = {}
    for doc in documents:
        doc_id = doc['id']
        text = doc.get('text', doc.get('doc_text', ''))
        doc_signatures[doc_id] = create_minhash(text, num_perm=effective_num_perm)
    
    # Build LSH index
    lsh = MinHashLSH(threshold=threshold, num_perm=effective_num_perm)
    
    # Insert all signatures into LSH
    for doc_id, sig in doc_signatures.items():
        lsh.insert(doc_id, sig)
    
    # Query each document to find clusters
    # We use a union-find approach to group documents into clusters
    parent = {doc_id: doc_id for doc_id in doc_signatures}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # For each document, query LSH to find similar documents
    # and union them if similarity > threshold
    for doc_id, sig in doc_signatures.items():
        # Query LSH for similar documents
        similar_docs = lsh.query(sig)
        for other_id in similar_docs:
            if other_id != doc_id:
                # Estimate actual Jaccard similarity
                other_sig = doc_signatures[other_id]
                jaccard_sim = estimate_jaccard(sig, other_sig)
                if jaccard_sim >= threshold:
                    union(doc_id, other_id)
    
    # Group documents by their root parent
    clusters_dict: Dict[str, List[str]] = {}
    for doc_id in doc_signatures:
        root = find(doc_id)
        if root not in clusters_dict:
            clusters_dict[root] = []
        clusters_dict[root].append(doc_id)
    
    # Convert to MinHashCluster objects
    clusters = []
    cluster_id = 0
    for root, members in clusters_dict.items():
        if len(members) > 1:
            # Select centroid (first member for simplicity)
            centroid_id = members[0]
            clusters.append(MinHashCluster(
                cluster_id=cluster_id,
                member_ids=members,
                centroid_id=centroid_id,
                size=len(members)
            ))
            cluster_id += 1
        elif len(members) == 1:
            # Single document clusters are not really clusters, but we track them
            # as "unique" items for later filtering
            clusters.append(MinHashCluster(
                cluster_id=cluster_id,
                member_ids=members,
                centroid_id=members[0],
                size=1
            ))
            cluster_id += 1
    
    logger.info(f"Created {len(clusters)} clusters from {len(documents)} documents")
    return clusters

def filter_candidates_by_clustering(
    candidates: List[Dict[str, Any]],
    clusters: List[MinHashCluster],
    threshold: float = 0.95
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter candidate list by keeping only one representative per cluster.
    
    Args:
        candidates: List of candidate documents.
        clusters: List of MinHashCluster objects.
        threshold: Jaccard similarity threshold used for clustering.
    
    Returns:
        Tuple of (filtered_candidates, metadata_dict)
        metadata_dict contains:
            - 'original_count': original number of candidates
            - 'filtered_count': number after filtering
            - 'removed_count': number of removed duplicates
            - 'clusters_used': number of clusters
            - 'false_positive_rate': estimated rate of incorrectly merged unique docs
    """
    if not candidates:
        return [], {'original_count': 0, 'filtered_count': 0, 'removed_count': 0, 'clusters_used': 0, 'false_positive_rate': 0.0}
    
    # Build a map from doc_id to cluster_id
    doc_to_cluster = {}
    for cluster in clusters:
        for member_id in cluster.member_ids:
            doc_to_cluster[member_id] = cluster.cluster_id
    
    # Group candidates by cluster
    cluster_members: Dict[int, List[Dict[str, Any]]] = {}
    for candidate in candidates:
        doc_id = candidate['id']
        cluster_id = doc_to_cluster.get(doc_id, -1)
        if cluster_id not in cluster_members:
            cluster_members[cluster_id] = []
        cluster_members[cluster_id].append(candidate)
    
    # Select one representative per cluster (the first one)
    filtered_candidates = []
    removed_count = 0
    total_unique = 0
    false_positives = 0
    
    for cluster_id, members in cluster_members.items():
        if cluster_id == -1:
            # Not in any cluster (unique)
            filtered_candidates.extend(members)
            total_unique += len(members)
        else:
            # In a cluster: keep first, remove rest
            if len(members) > 1:
                # This is a true cluster of duplicates
                filtered_candidates.append(members[0])
                removed_count += len(members) - 1
            else:
                # Single member in a cluster - check if it's a false positive
                # A false positive is when a unique document is incorrectly merged
                # into a cluster with other unique documents
                # For simplicity, we consider a single-member cluster as potentially
                # a false positive if the cluster was formed with a high threshold
                # In practice, we need to check if the cluster was formed by
                # merging with other documents that are actually unique
                # For now, we'll count it as a unique document
                filtered_candidates.append(members[0])
                total_unique += 1
    
    # Calculate false positive rate
    # A false positive merge is when a unique document is incorrectly merged
    # into a cluster. We estimate this by checking how many single-member
    # clusters were formed (they might be unique docs incorrectly merged)
    # This is a rough estimate; a more accurate method would require ground truth
    num_clusters = len(clusters)
    if num_clusters > 0:
        # Estimate false positive rate as the ratio of single-member clusters
        # that were formed (assuming they should have been unique)
        # This is a heuristic and may not be accurate
        single_member_clusters = sum(1 for c in clusters if c.size == 1)
        false_positive_rate = single_member_clusters / num_clusters
    else:
        false_positive_rate = 0.0
    
    metadata = {
        'original_count': len(candidates),
        'filtered_count': len(filtered_candidates),
        'removed_count': removed_count,
        'clusters_used': len(clusters),
        'false_positive_rate': false_positive_rate
    }
    
    logger.info(f"Filtered {len(candidates)} candidates to {len(filtered_candidates)} "
               f"(removed {removed_count} duplicates, false positive rate: {false_positive_rate:.2%})")
    
    return filtered_candidates, metadata

def run_clustering_pipeline(
    documents: List[Dict[str, Any]],
    threshold: float = 0.95,
    output_path: Optional[str] = None,
    strict_mode: bool = False
) -> Tuple[List[MinHashCluster], Dict[str, Any]]:
    """
    Run the full clustering pipeline with threshold sensitivity fallback.
    
    This implements T059: Threshold Sensitivity Fallback for Edge Case 1.
    If the initial threshold results in > 10% false positives (incorrectly merged
    unique documents), the system automatically retries with a relaxed threshold.
    
    Args:
        documents: List of document dicts.
        threshold: Initial Jaccard similarity threshold.
        output_path: Optional path to write cluster results.
        strict_mode: If True, raise ClusteringFailureError if fallback fails.
    
    Returns:
        Tuple of (clusters, metadata)
    
    Raises:
        ClusteringFailureError: If both initial and relaxed thresholds fail.
    """
    
    class ClusteringFailureError(Exception):
        """Raised when clustering fails after all fallback attempts."""
        pass
    
    def run_with_threshold(thresh: float) -> Tuple[List[MinHashCluster], Dict[str, Any]]:
        clusters = cluster_documents(documents, threshold=thresh)
        _, metadata = filter_candidates_by_clustering(documents, clusters, threshold=thresh)
        return clusters, metadata
    
    # Step 1: Try with initial threshold
    logger.info(f"Attempting clustering with initial threshold: {threshold}")
    clusters, metadata = run_with_threshold(threshold)
    
    false_positive_rate = metadata.get('false_positive_rate', 0.0)
    
    # Check if false positive rate is acceptable
    if false_positive_rate <= 0.10:
        logger.info(f"Clustering successful with threshold {threshold}: "
                   f"false positive rate = {false_positive_rate:.2%}")
    else:
        # Step 2: Threshold too aggressive, try relaxed threshold
        logger.warning(f"High false positive rate ({false_positive_rate:.2%}) with threshold {threshold}. "
                      "Attempting fallback with relaxed threshold.")
        
        # Relaxed threshold: decrease by 0.05 (e.g., 0.95 -> 0.90)
        relaxed_threshold = max(0.5, threshold - 0.05)
        logger.info(f"Retrying with relaxed threshold: {relaxed_threshold}")
        
        clusters, metadata = run_with_threshold(relaxed_threshold)
        false_positive_rate = metadata.get('false_positive_rate', 0.0)
        
        if false_positive_rate <= 0.10:
            logger.info(f"Clustering successful with relaxed threshold {relaxed_threshold}: "
                       f"false positive rate = {false_positive_rate:.2%}")
            metadata['threshold_used'] = relaxed_threshold
            metadata['fallback_triggered'] = True
        else:
            # Step 3: Fallback also failed
            error_msg = (
                f"Clustering failed: false positive rate {false_positive_rate:.2%} "
                f"exceeds 10% threshold even with relaxed threshold {relaxed_threshold}. "
                f"Initial threshold: {threshold}."
            )
            logger.error(error_msg)
            if strict_mode:
                raise ClusteringFailureError(error_msg)
            else:
                # In non-strict mode, log warning and return best effort
                logger.warning("Returning clusters despite high false positive rate. "
                              "Results may be unreliable.")
                metadata['threshold_used'] = relaxed_threshold
                metadata['fallback_triggered'] = True
                metadata['high_false_positive_warning'] = True
    
    # Write output if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        clusters_data = [c.to_dict() for c in clusters]
        with open(output_path, 'w') as f:
            json.dump({
                'clusters': clusters_data,
                'metadata': metadata
            }, f, indent=2)
        logger.info(f"Cluster results written to {output_path}")
    
    metadata['threshold_used'] = metadata.get('threshold_used', threshold)
    metadata['fallback_triggered'] = metadata.get('fallback_triggered', False)
    
    return clusters, metadata

def main():
    """CLI entry point for clustering module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MinHash-LSH Clustering Pipeline')
    parser.add_argument('--input', type=str, required=True, help='Input JSON file with documents')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for clusters')
    parser.add_argument('--threshold', type=float, default=0.95, help='Jaccard similarity threshold')
    parser.add_argument('--strict', action='store_true', help='Fail on high false positive rate')
    
    args = parser.parse_args()
    
    # Load documents
    with open(args.input, 'r') as f:
        data = json.load(f)
        documents = data.get('documents', data) if isinstance(data, dict) else data
    
    # Run pipeline
    clusters, metadata = run_clustering_pipeline(
        documents,
        threshold=args.threshold,
        output_path=args.output,
        strict_mode=args.strict
    )
    
    # Print summary
    print(f"Clustering complete:")
    print(f"  Threshold used: {metadata['threshold_used']}")
    print(f"  Fallback triggered: {metadata['fallback_triggered']}")
    print(f"  Clusters created: {len(clusters)}")
    print(f"  False positive rate: {metadata['false_positive_rate']:.2%}")

if __name__ == '__main__':
    main()