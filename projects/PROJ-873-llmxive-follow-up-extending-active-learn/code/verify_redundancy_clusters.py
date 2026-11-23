"""
Verification script for T012a: Verify injected dataset contains at least 20 clusters of 3–5 near-duplicate items.

This script loads the injected dataset, validates the cluster structure,
and asserts compliance with FR-002 before proceeding with further analysis.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Tuple

from data_loader import load_injected_dataset, RedundancyCluster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for FR-002 compliance
MIN_CLUSTERS_REQUIRED = 20
MIN_CLUSTER_SIZE = 3
MAX_CLUSTER_SIZE = 5

def validate_cluster_counts(clusters: List[RedundancyCluster]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the injected dataset meets FR-002 requirements:
    - At least 20 clusters
    - Each cluster has 3-5 items
    
    Args:
        clusters: List of RedundancyCluster objects from the injected dataset
        
    Returns:
        Tuple of (is_compliant, statistics_dict)
    """
    stats = {
        'total_clusters': len(clusters),
        'valid_clusters': 0,
        'invalid_clusters': 0,
        'cluster_sizes': [],
        'compliant': False,
        'errors': []
    }
    
    if len(clusters) < MIN_CLUSTERS_REQUIRED:
        stats['errors'].append(
            f"Insufficient clusters: {len(clusters)} < {MIN_CLUSTERS_REQUIRED}"
        )
        return False, stats
    
    for i, cluster in enumerate(clusters):
        size = len(cluster.documents)
        stats['cluster_sizes'].append(size)
        
        if MIN_CLUSTER_SIZE <= size <= MAX_CLUSTER_SIZE:
            stats['valid_clusters'] += 1
        else:
            stats['invalid_clusters'] += 1
            stats['errors'].append(
                f"Cluster {i} has invalid size: {size} (expected {MIN_CLUSTER_SIZE}-{MAX_CLUSTER_SIZE})"
            )
    
    # Check overall compliance
    if (stats['total_clusters'] >= MIN_CLUSTERS_REQUIRED and 
        stats['invalid_clusters'] == 0):
        stats['compliant'] = True
    else:
        stats['compliant'] = False
        
    return stats['compliant'], stats

def main():
    """Main entry point for verification."""
    logger.info("Starting redundancy cluster verification (T012a)...")
    
    # Load the injected dataset
    injected_data_path = "data/injected/nfcorpus_scifact_redundant.json"
    
    if not os.path.exists(injected_data_path):
        logger.error(f"Injected dataset not found at {injected_data_path}")
        logger.error("Please run the injection pipeline (T012) first.")
        sys.exit(1)
    
    try:
        clusters = load_injected_dataset(injected_data_path)
        logger.info(f"Loaded {len(clusters)} clusters from injected dataset")
    except Exception as e:
        logger.error(f"Failed to load injected dataset: {e}")
        sys.exit(1)
    
    # Validate cluster counts
    is_compliant, stats = validate_cluster_counts(clusters)
    
    # Log results
    logger.info(f"Total clusters: {stats['total_clusters']}")
    logger.info(f"Valid clusters (size 3-5): {stats['valid_clusters']}")
    logger.info(f"Invalid clusters: {stats['invalid_clusters']}")
    
    if stats['cluster_sizes']:
        min_size = min(stats['cluster_sizes'])
        max_size = max(stats['cluster_sizes'])
        avg_size = sum(stats['cluster_sizes']) / len(stats['cluster_sizes'])
        logger.info(f"Cluster size range: {min_size}-{max_size}")
        logger.info(f"Average cluster size: {avg_size:.2f}")
    
    # Save detailed statistics
    stats_path = "data/results/cluster_validation_stats.json"
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Validation statistics saved to {stats_path}")
    
    # Assert compliance
    if not is_compliant:
        logger.error("FR-002 COMPLIANCE FAILED!")
        for error in stats['errors']:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    logger.info("✅ FR-002 COMPLIANCE VERIFIED!")
    logger.info(f"   - {stats['total_clusters']} clusters found (≥ {MIN_CLUSTERS_REQUIRED} required)")
    logger.info(f"   - All clusters have 3-5 items")
    return 0

if __name__ == "__main__":
    sys.exit(main())
