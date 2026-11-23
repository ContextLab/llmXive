import os
import json
import hashlib
import time
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import logging

from datasketch import MinHash, MinHashLSH
from sentence_transformers import SentenceTransformer

from config import get_config
from models import RedundancyCluster
from metrics import calculate_cosine_similarity_proxy

logger = logging.getLogger(__name__)

@dataclass
class MinHashCluster:
    cluster_id: int
    member_ids: List[str]
    representative_id: str
    jaccard_similarities: Dict[str, float]

def create_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Create a MinHash signature for a given text."""
    m = MinHash(num_perm=num_perm)
    # Simple tokenization: lowercase and split
    tokens = text.lower().split()
    for token in tokens:
        m.update(token.encode('utf8'))
    return m

def estimate_jaccard(m1: MinHash, m2: MinHash) -> float:
    """Estimate Jaccard similarity between two MinHash signatures."""
    return m1.jaccard(m2)

def cluster_documents(documents: List[Dict[str, Any]], threshold: float = 0.95) -> List[MinHashCluster]:
    """
    Cluster documents using MinHash LSH.
    
    Args:
        documents: List of document dicts with 'id' and 'text' keys.
        threshold: Jaccard similarity threshold for clustering.
        
    Returns:
        List of MinHashCluster objects.
    """
    logger.info(f"Starting MinHash clustering with threshold {threshold}")
    
    # Create MinHash signatures for all documents
    signatures = {}
    for doc in documents:
        doc_id = doc['id']
        text = doc['text']
        signatures[doc_id] = create_minhash(text)
    
    # Create LSH index
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    
    # Add signatures to LSH
    for doc_id, sig in signatures.items():
        lsh.insert(doc_id, sig)
    
    # Query each document to find its cluster
    clusters_map = {}  # doc_id -> cluster_id
    clusters_data = {} # cluster_id -> set of doc_ids
    cluster_counter = 0
    
    for doc_id, sig in signatures.items():
        if doc_id in clusters_map:
            continue
        
        # Find similar documents
        similar_ids = lsh.query(sig)
        similar_ids = [sid for sid in similar_ids if sid != doc_id]
        
        # Create a new cluster
        cluster_id = cluster_counter
        clusters_data[cluster_id] = {doc_id}
        clusters_map[doc_id] = cluster_id
        
        for sid in similar_ids:
            if sid not in clusters_map:
                clusters_map[sid] = cluster_id
                clusters_data[cluster_id].add(sid)
            else:
                # Merge clusters if they are connected
                existing_cluster = clusters_map[sid]
                if existing_cluster != cluster_id:
                    # Merge existing_cluster into cluster_id
                    for other_id in clusters_data[existing_cluster]:
                        clusters_map[other_id] = cluster_id
                        clusters_data[cluster_id].add(other_id)
                    del clusters_data[existing_cluster]
        
        cluster_counter += 1
    
    # Convert to MinHashCluster objects
    result_clusters = []
    for cluster_id, member_ids in clusters_data.items():
        member_ids_list = list(member_ids)
        # Calculate pairwise Jaccard similarities within cluster
        jaccard_sims = {}
        for mid in member_ids_list:
            sims = []
            for other_id in member_ids_list:
                if mid != other_id:
                    sim = estimate_jaccard(signatures[mid], signatures[other_id])
                    sims.append(sim)
            if sims:
                jaccard_sims[mid] = sum(sims) / len(sims)
        
        # Select representative (highest average similarity to others)
        rep_id = max(member_ids_list, key=lambda x: jaccard_sims.get(x, 0))
        
        result_clusters.append(MinHashCluster(
            cluster_id=cluster_id,
            member_ids=member_ids_list,
            representative_id=rep_id,
            jaccard_similarities=jaccard_sims
        ))
    
    logger.info(f"Clustering complete: {len(result_clusters)} clusters found")
    return result_clusters

def filter_candidates_by_clustering(
    candidates: List[Dict[str, Any]], 
    clusters: List[MinHashCluster],
    threshold: float = 0.95
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Filter candidates by keeping only representatives from each cluster.
    
    Args:
        candidates: List of candidate dicts.
        clusters: List of MinHashCluster objects.
        threshold: Jaccard similarity threshold used for clustering.
        
    Returns:
        Tuple of (filtered candidates, number of removed candidates).
    """
    logger.info(f"Filtering candidates using {len(clusters)} clusters")
    
    # Build a map of document_id -> cluster_id
    doc_to_cluster = {}
    for cluster in clusters:
        for mid in cluster.member_ids:
            doc_to_cluster[mid] = cluster.cluster_id
    
    # Keep only representatives
    kept_ids = {cluster.representative_id for cluster in clusters}
    
    filtered_candidates = []
    removed_count = 0
    
    for candidate in candidates:
        doc_id = candidate['id']
        if doc_id in kept_ids:
            filtered_candidates.append(candidate)
        else:
            removed_count += 1
    
    logger.info(f"Filtered candidates: {len(candidates)} -> {len(filtered_candidates)} (removed {removed_count})")
    return filtered_candidates, removed_count

def run_clustering_pipeline(
    input_path: str,
    output_path: str,
    threshold: float = 0.95,
    fallback_thresholds: List[float] = None
) -> Dict[str, Any]:
    """
    Run the full clustering pipeline with threshold sensitivity fallback.
    
    Implements T059: If > 10% false-positive merges, automatically relax Jaccard 
    threshold and log adjustment; raise ClusteringFailureError if still > 10%.
    
    Args:
        input_path: Path to injected_datasets.json.
        output_path: Path to write clusters.json.
        threshold: Initial Jaccard similarity threshold.
        fallback_thresholds: List of thresholds to try if initial fails.
        
    Returns:
        Dictionary with clustering results and status.
    """
    logger.info(f"Running clustering pipeline with initial threshold {threshold}")
    
    # Load input data
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    documents = data.get('documents', [])
    if not documents:
        raise ValueError("No documents found in input file")
    
    # Prepare fallback thresholds if not provided
    if fallback_thresholds is None:
        # Default fallback: relax threshold if initial fails
        fallback_thresholds = [0.90, 0.85, 0.80]
    
    current_threshold = threshold
    max_false_positive_rate = 0.10  # 10%
    
    for attempt_idx, current_threshold in enumerate([threshold] + fallback_thresholds):
        logger.info(f"Clustering attempt {attempt_idx + 1} with threshold {current_threshold}")
        
        try:
            clusters = cluster_documents(documents, threshold=current_threshold)
            
            # Validate cluster quality
            false_positive_count = 0
            total_pairs = 0
            
            for cluster in clusters:
                if len(cluster.member_ids) < 2:
                    continue
                
                # Calculate actual cosine similarity for intra-cluster pairs
                # Using embedding model for ground truth validation
                embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                texts = []
                ids = []
                
                for doc in documents:
                    if doc['id'] in cluster.member_ids:
                        texts.append(doc['text'])
                        ids.append(doc['id'])
                
                if len(texts) < 2:
                    continue
                
                embeddings = embedding_model.encode(texts)
                
                # Check pairwise similarities
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        total_pairs += 1
                        # Calculate cosine similarity
                        from metrics import calculate_cosine_similarity_proxy
                        sim = calculate_cosine_similarity_proxy(embeddings[i], embeddings[j])
                        
                        # If similarity < 0.95 but they are in same cluster (Jaccard > threshold),
                        # it's a potential false positive
                        if sim < 0.95:
                            false_positive_count += 1
            
            false_positive_rate = false_positive_count / total_pairs if total_pairs > 0 else 0.0
            
            logger.info(f"Attempt {attempt_idx + 1}: False positive rate = {false_positive_rate:.4f}")
            
            if false_positive_rate <= max_false_positive_rate:
                # Success: write results
                clusters_dict = [asdict(c) for c in clusters]
                
                # Write to output file
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump({
                        'clusters': clusters_dict,
                        'threshold_used': current_threshold,
                        'false_positive_rate': false_positive_rate,
                        'total_clusters': len(clusters),
                        'total_documents': len(documents),
                        'attempt': attempt_idx + 1
                    }, f, indent=2)
                
                logger.info(f"Clustering successful with threshold {current_threshold}")
                return {
                    'status': 'success',
                    'threshold_used': current_threshold,
                    'false_positive_rate': false_positive_rate,
                    'num_clusters': len(clusters),
                    'num_documents': len(documents)
                }
            else:
                logger.warning(f"Attempt {attempt_idx + 1}: False positive rate {false_positive_rate:.4f} > {max_false_positive_rate}")
                if attempt_idx == len(fallback_thresholds):
                    # Last attempt failed
                    raise ClusteringFailureError(
                        f"Clustering failed: false positive rate {false_positive_rate:.4f} exceeds "
                        f"threshold {max_false_positive_rate} even after relaxing to {current_threshold}"
                    )
                else:
                    logger.info(f"Relaxing threshold to {fallback_thresholds[attempt_idx]} for next attempt")
                    
        except Exception as e:
            logger.error(f"Clustering attempt {attempt_idx + 1} failed: {str(e)}")
            if attempt_idx == len(fallback_thresholds):
                raise ClusteringFailureError(
                    f"Clustering failed after all attempts: {str(e)}"
                )
    
    raise ClusteringFailureError("Clustering failed: all threshold attempts exceeded false positive limit")

def main():
    """Main entry point for clustering pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MinHash clustering pipeline')
    parser.add_argument('--input', type=str, required=True, help='Input file path')
    parser.add_argument('--output', type=str, required=True, help='Output file path')
    parser.add_argument('--threshold', type=float, default=0.95, help='Jaccard similarity threshold')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    
    try:
        result = run_clustering_pipeline(
            input_path=args.input,
            output_path=args.output,
            threshold=args.threshold
        )
        print(json.dumps(result, indent=2))
    except ClusteringFailureError as e:
        logger.error(f"Clustering failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

class ClusteringFailureError(Exception):
    """Raised when clustering fails due to excessive false positives."""
    pass
